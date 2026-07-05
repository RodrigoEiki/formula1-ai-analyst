"""Streamlit in Snowflake app for Formula 1 Cortex Analyst questions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

try:
    import _snowflake
except ImportError:  # pragma: no cover - only available in Streamlit in Snowflake
    _snowflake = None

ANALYST_ENDPOINT = "/api/v2/cortex/analyst/message"
DEFAULT_SEMANTIC_MODEL_FILE = "@F1_ANALYTICS.ANALYTICS.F1_SEMANTIC_STAGE/f1_analyst.yaml"
LOCAL_SEMANTIC_MODEL_PATH = Path(__file__).resolve().parents[1] / "semantic_models" / "f1_analyst.yaml"

EXAMPLE_QUESTIONS = [
    "Which drivers won the most races in the 2021 season?",
    "Which constructor scored the most points in 2022?",
    "Show podium finishes by driver for the 2020 season.",
    "Which circuits hosted the most Formula 1 races?",
    "Compare Ferrari and Mercedes points by season.",
    "List the Formula 1 world drivers champions by season.",
    "Which drivers have the most pole positions?",
]


@dataclass(frozen=True)
class AnalystResponse:
    """Parsed response from Cortex Analyst."""

    text: str = ""
    sql: str | None = None
    suggestions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    request_id: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatTurn:
    """A single Streamlit chat turn."""

    question: str
    response: AnalystResponse
    results: pd.DataFrame | None
    summary: str = ""
    error: str | None = None


def configure_page() -> None:
    """Configure the Streamlit page."""
    st.set_page_config(page_title="Formula 1 AI Analyst", layout="wide")
    st.title("Formula 1 AI Analyst")
    st.caption("Ask natural language questions about historical Formula 1 data.")


def initialize_state() -> None:
    """Initialize Streamlit session state."""
    if "turns" not in st.session_state:
        st.session_state.turns = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


def build_analyst_request(question: str, semantic_model_file: str) -> dict[str, Any]:
    """Build the Cortex Analyst request payload."""
    payload: dict[str, Any] = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": question}],
            }
        ],
        "stream": False,
    }

    if semantic_model_file:
        payload["semantic_model_file"] = semantic_model_file
    elif LOCAL_SEMANTIC_MODEL_PATH.exists():
        payload["semantic_model"] = LOCAL_SEMANTIC_MODEL_PATH.read_text(encoding="utf-8")
    else:
        raise ValueError("Configure a semantic model file or deploy semantic_models/f1_analyst.yaml.")

    return payload


def parse_analyst_response(response_body: dict[str, Any]) -> AnalystResponse:
    """Parse a non-streaming Cortex Analyst response."""
    message = response_body.get("message", {})
    content_blocks = message.get("content", [])

    text_parts: list[str] = []
    sql: str | None = None
    suggestions: list[str] = []

    for block in content_blocks:
        block_type = block.get("type")
        if block_type == "text" and block.get("text"):
            text_parts.append(str(block["text"]))
        elif block_type == "sql" and block.get("statement"):
            sql = str(block["statement"])
        elif block_type in {"suggestion", "suggestions"}:
            block_suggestions = block.get("suggestions", [])
            if isinstance(block_suggestions, list):
                suggestions.extend(str(item) for item in block_suggestions)

    warning_messages = [
        str(warning.get("message"))
        for warning in response_body.get("warnings", [])
        if isinstance(warning, dict) and warning.get("message")
    ]

    return AnalystResponse(
        text="\n\n".join(text_parts),
        sql=sql,
        suggestions=suggestions,
        warnings=warning_messages,
        request_id=response_body.get("request_id"),
        raw_response=response_body,
    )


def ask_cortex_analyst(question: str, semantic_model_file: str) -> AnalystResponse:
    """Send a question to Cortex Analyst from Streamlit in Snowflake."""
    if _snowflake is None:
        raise RuntimeError("This app entrypoint must run inside Streamlit in Snowflake.")

    request_body = build_analyst_request(question, semantic_model_file)
    response = _snowflake.send_snow_api_request(
        "POST",
        ANALYST_ENDPOINT,
        {},
        {},
        request_body,
        {},
        60000,
    )

    status = response.get("status")
    if status is not None and status >= 400:
        content = response.get("content")
        raise RuntimeError(f"Cortex Analyst request failed with status {status}: {content}")

    content = response.get("content")
    if isinstance(content, str):
        response_body = json.loads(content)
    elif isinstance(content, dict):
        response_body = content
    else:
        raise RuntimeError("Cortex Analyst returned an unexpected response format.")

    return parse_analyst_response(response_body)


def execute_generated_sql(sql: str) -> pd.DataFrame:
    """Execute Cortex-generated SQL using the active Snowflake session."""
    session = get_active_session()
    return session.sql(sql).to_pandas()


def summarize_results(question: str, results: pd.DataFrame) -> str:
    """Generate a natural language summary of query results using Cortex."""
    session = get_active_session()
    preview = results.head(20).to_string(index=False)
    prompt = (
        f"User question: {question}\n\n"
        f"Query results:\n{preview}\n\n"
        "Provide a concise natural language answer to the user's question based on these results. "
        "Be direct and specific with the data."
    )
    escaped = prompt.replace("'", "''")
    row = session.sql(
        f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{escaped}') AS summary"
    ).collect()
    return row[0]["SUMMARY"] if row else ""


def render_sidebar() -> None:
    """Render sidebar context and example prompts."""
    with st.sidebar:
        st.header("Configuration")
        st.write("Runtime: `Streamlit in Snowflake`")
        st.write(f"Semantic model: `{DEFAULT_SEMANTIC_MODEL_FILE}`")

        st.divider()
        st.header("Example Prompts")
        for idx, question in enumerate(EXAMPLE_QUESTIONS):
            if st.button(question, key=f"sidebar-example-{idx}", use_container_width=True):
                st.session_state.pending_question = question


def render_onboarding() -> None:
    """Render clickable example prompts when no conversation exists."""
    st.markdown("#### Try asking:")
    cols = st.columns(2)
    for idx, question in enumerate(EXAMPLE_QUESTIONS):
        with cols[idx % 2]:
            if st.button(question, key=f"onboard-{idx}", use_container_width=True):
                st.session_state.pending_question = question


def render_turn(turn: ChatTurn) -> None:
    """Render a completed chat turn."""
    with st.chat_message("user"):
        st.write(turn.question)

    with st.chat_message("assistant"):
        if turn.error:
            st.error(turn.error)
            return

        if turn.summary:
            st.write(turn.summary)
        elif turn.response.text:
            st.write(turn.response.text)

        for warning in turn.response.warnings:
            st.warning(warning)

        if turn.response.suggestions:
            st.info("Cortex Analyst returned suggestions instead of SQL.")
            for suggestion in turn.response.suggestions:
                st.write(f"- {suggestion}")

        if turn.response.sql:
            with st.expander("Generated SQL", expanded=False):
                st.code(turn.response.sql, language="sql")

        if turn.results is not None:
            with st.expander("Results Table", expanded=True):
                st.dataframe(turn.results, use_container_width=True, hide_index=True)


def process_question(question: str) -> ChatTurn:
    """Ask Cortex Analyst and execute generated SQL."""
    try:
        response = ask_cortex_analyst(
            question,
            DEFAULT_SEMANTIC_MODEL_FILE,
        )
        results = execute_generated_sql(response.sql) if response.sql else None
        summary = ""
        if results is not None and not results.empty:
            summary = summarize_results(question, results)
        return ChatTurn(question=question, response=response, results=results, summary=summary)
    except Exception as exc:
        return ChatTurn(
            question=question,
            response=AnalystResponse(),
            results=None,
            error=str(exc),
        )


def main() -> None:
    """Run the Streamlit in Snowflake application."""
    configure_page()
    initialize_state()
    render_sidebar()

    if not st.session_state.turns:
        render_onboarding()

    for turn in st.session_state.turns:
        render_turn(turn)

    prompt = st.chat_input("Ask about Formula 1 history")
    if st.session_state.pending_question:
        prompt = st.session_state.pending_question
        st.session_state.pending_question = None

    if prompt:
        with st.spinner("Asking Cortex Analyst and running the generated SQL..."):
            st.session_state.turns.append(process_question(prompt))
        st.rerun()


if __name__ == "__main__":
    main()
