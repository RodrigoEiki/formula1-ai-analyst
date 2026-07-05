"""Streamlit application for asking Formula 1 questions with Cortex Analyst."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from app.config import (
    CortexAnalystConfig,
    SnowflakeConfig,
    load_cortex_analyst_config,
    load_snowflake_config,
)
from app.cortex_client import (
    AnalystResponse,
    CortexAnalystError,
    ask_cortex_analyst,
    get_connection_auth_token,
)
from app.snowflake_client import connect_to_snowflake, execute_query

logger = logging.getLogger(__name__)

EXAMPLE_QUESTIONS = [
    "Which drivers won the most races in the 2021 season?",
    "Which constructor scored the most points in 2022?",
    "Show podium finishes by driver for the 2020 season.",
    "Which circuits hosted the most Formula 1 races?",
    "Compare Ferrari and Mercedes points by season.",
    "List the Formula 1 world drivers champions by season.",
    "Which drivers have the most pole positions?",
]


@dataclass
class ChatTurn:
    """A single user question and Analyst response shown in chat history."""

    question: str
    response: AnalystResponse
    results: pd.DataFrame | None
    error: str | None = None


def configure_page() -> None:
    """Configure Streamlit page settings and styling."""
    st.set_page_config(page_title="Formula 1 AI Analyst", layout="wide")
    st.title("Formula 1 AI Analyst")
    st.caption("Ask natural language questions about historical Formula 1 data.")


@st.cache_resource(show_spinner=False)
def get_app_config() -> tuple[SnowflakeConfig, CortexAnalystConfig]:
    """Load application configuration once per Streamlit session."""
    snowflake_config = load_snowflake_config(
        preferred_schema_env="SNOWFLAKE_ANALYTICS_SCHEMA"
    )
    return snowflake_config, load_cortex_analyst_config()


def render_sidebar(
    snowflake_config: SnowflakeConfig,
    cortex_config: CortexAnalystConfig,
) -> None:
    """Render sidebar context and example questions."""
    with st.sidebar:
        st.header("Configuration")
        st.write(f"Database: `{snowflake_config.database}`")
        st.write(f"Schema: `{snowflake_config.schema}`")
        st.write(f"Warehouse: `{snowflake_config.warehouse}`")

        if cortex_config.semantic_view:
            st.write(f"Semantic view: `{cortex_config.semantic_view}`")
        elif cortex_config.semantic_model_file:
            st.write(f"Semantic model file: `{cortex_config.semantic_model_file}`")
        elif cortex_config.semantic_model_path:
            st.write(f"Local semantic YAML: `{cortex_config.semantic_model_path.name}`")

        st.divider()
        st.header("Example Prompts")
        selected = None
        for question in EXAMPLE_QUESTIONS:
            if st.button(question, key=f"example-{question}", use_container_width=True):
                selected = question

        if selected:
            st.session_state.pending_question = selected


def initialize_state() -> None:
    """Initialize Streamlit session state."""
    if "turns" not in st.session_state:
        st.session_state.turns = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


def render_turn(turn: ChatTurn) -> None:
    """Render a chat turn with SQL and result table."""
    with st.chat_message("user"):
        st.write(turn.question)

    with st.chat_message("assistant"):
        if turn.error:
            st.error(turn.error)
            return

        if turn.response.text:
            st.write(turn.response.text)

        if turn.response.warnings:
            for warning in turn.response.warnings:
                st.warning(warning)

        if turn.response.suggestions:
            st.info("Cortex Analyst returned suggestions instead of SQL.")
            for suggestion in turn.response.suggestions:
                st.write(f"- {suggestion}")

        if turn.response.sql:
            with st.expander("Generated SQL", expanded=True):
                st.code(turn.response.sql, language="sql")

        if turn.results is not None:
            st.dataframe(turn.results, use_container_width=True, hide_index=True)


def process_question(
    question: str,
    snowflake_config: SnowflakeConfig,
    cortex_config: CortexAnalystConfig,
) -> ChatTurn:
    """Send a question to Cortex Analyst and execute generated SQL."""
    connection = None
    try:
        connection = connect_to_snowflake(snowflake_config)
        auth_token = cortex_config.auth_token or get_connection_auth_token(connection)
        response = ask_cortex_analyst(
            question,
            cortex_config,
            auth_token=auth_token,
        )

        results = None
        if response.sql:
            results = execute_query(connection, response.sql)

        return ChatTurn(question=question, response=response, results=results)
    except (CortexAnalystError, ValueError, RuntimeError) as exc:
        logger.exception("Question processing failed")
        return ChatTurn(
            question=question,
            response=AnalystResponse(),
            results=None,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected question processing failure")
        return ChatTurn(
            question=question,
            response=AnalystResponse(),
            results=None,
            error=f"Unexpected error: {exc}",
        )
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Run the Streamlit application."""
    logging.basicConfig(level=logging.INFO)
    configure_page()
    initialize_state()

    try:
        snowflake_config, cortex_config = get_app_config()
    except Exception as exc:
        st.error(f"Configuration error: {exc}")
        st.stop()

    render_sidebar(snowflake_config, cortex_config)

    for turn in st.session_state.turns:
        render_turn(turn)

    prompt = st.chat_input("Ask about Formula 1 history")
    pending_question = st.session_state.pending_question
    if pending_question:
        prompt = pending_question
        st.session_state.pending_question = None

    if prompt:
        with st.spinner("Asking Cortex Analyst and running the generated SQL..."):
            turn = process_question(prompt, snowflake_config, cortex_config)
            st.session_state.turns.append(turn)
        st.rerun()


if __name__ == "__main__":
    main()
