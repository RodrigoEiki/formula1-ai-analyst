"""Client utilities for communicating with Snowflake Cortex Analyst."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
from snowflake.connector import SnowflakeConnection

from app.config import CortexAnalystConfig

logger = logging.getLogger(__name__)

ANALYST_MESSAGE_PATH = "/api/v2/cortex/analyst/message"


@dataclass(frozen=True)
class AnalystResponse:
    """Parsed response from Cortex Analyst."""

    text: str = ""
    sql: str | None = None
    suggestions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    request_id: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class CortexAnalystError(RuntimeError):
    """Raised when Cortex Analyst communication or parsing fails."""


def read_semantic_model_yaml(path: Path) -> str:
    """Read a local semantic model YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Semantic model YAML not found: {path}")
    return path.read_text(encoding="utf-8")


def get_connection_auth_token(connection: SnowflakeConnection) -> str | None:
    """Return the Snowflake session token from a connector connection when available."""
    rest = getattr(connection, "_rest", None)
    token = getattr(rest, "_token", None)
    if isinstance(token, str) and token:
        return token
    return None


def build_analyst_request(question: str, config: CortexAnalystConfig) -> dict[str, Any]:
    """Build the Cortex Analyst message request payload."""
    payload: dict[str, Any] = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": question}],
            }
        ],
        "stream": False,
    }

    if config.semantic_view is not None:
        payload["semantic_view"] = config.semantic_view
    elif config.semantic_model_file is not None:
        payload["semantic_model_file"] = config.semantic_model_file
    elif config.semantic_model_path is not None:
        payload["semantic_model"] = read_semantic_model_yaml(config.semantic_model_path)
    else:
        raise CortexAnalystError(
            "Configure CORTEX_ANALYST_SEMANTIC_VIEW, "
            "CORTEX_ANALYST_SEMANTIC_MODEL_FILE, or "
            "CORTEX_ANALYST_SEMANTIC_MODEL_PATH."
        )

    return payload


def parse_analyst_response(response_body: dict[str, Any]) -> AnalystResponse:
    """Parse the non-streaming Cortex Analyst response body."""
    message = response_body.get("message", {})
    content_blocks = message.get("content", [])

    text_parts: list[str] = []
    sql: str | None = None
    suggestions: list[str] = []

    for block in content_blocks:
        block_type = block.get("type")
        if block_type == "text":
            text = block.get("text")
            if isinstance(text, str) and text:
                text_parts.append(text)
        elif block_type == "sql":
            statement = block.get("statement")
            if isinstance(statement, str) and statement:
                sql = statement
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


def ask_cortex_analyst(
    question: str,
    config: CortexAnalystConfig,
    *,
    auth_token: str | None = None,
    timeout_seconds: int = 60,
) -> AnalystResponse:
    """Send a natural language question to Cortex Analyst."""
    token = auth_token or config.auth_token
    if token is None:
        raise CortexAnalystError(
            "Cortex Analyst requires an auth token. Set CORTEX_ANALYST_AUTH_TOKEN "
            "or use a Snowflake connector session that exposes a session token."
        )

    payload = build_analyst_request(question, config)
    url = f"{config.account_url}{ANALYST_MESSAGE_PATH}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Snowflake-Authorization-Token-Type": config.auth_token_type,
    }

    logger.info("Sending question to Cortex Analyst")
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        detail = getattr(exc.response, "text", "") if exc.response is not None else ""
        message = f"Cortex Analyst request failed: {exc}"
        if detail:
            message = f"{message}. Response: {detail}"
        raise CortexAnalystError(message) from exc

    try:
        response_body = response.json()
    except ValueError as exc:
        raise CortexAnalystError("Cortex Analyst returned invalid JSON") from exc

    return parse_analyst_response(response_body)
