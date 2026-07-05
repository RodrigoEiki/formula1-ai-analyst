"""Tests for Cortex Analyst request and response helpers."""

from __future__ import annotations

from pathlib import Path

from app.config import CortexAnalystConfig
from app.cortex_client import build_analyst_request, parse_analyst_response


def test_build_analyst_request_uses_local_semantic_model(tmp_path):
    """Local semantic YAML should be embedded in the Analyst request."""
    semantic_model = tmp_path / "model.yaml"
    semantic_model.write_text("name: test_model\n", encoding="utf-8")
    config = CortexAnalystConfig(
        account_url="https://example.snowflakecomputing.com",
        semantic_model_path=semantic_model,
        semantic_model_file=None,
        semantic_view=None,
        auth_token="token",
        auth_token_type="OAUTH",
    )

    payload = build_analyst_request("Who won in 2021?", config)

    assert payload["semantic_model"] == "name: test_model\n"
    assert payload["messages"][0]["content"][0]["text"] == "Who won in 2021?"


def test_parse_analyst_response_extracts_text_sql_and_warnings():
    """Analyst response parsing should expose text, SQL, and warnings."""
    response = parse_analyst_response(
        {
            "request_id": "request-1",
            "message": {
                "content": [
                    {"type": "text", "text": "Here is the SQL."},
                    {"type": "sql", "statement": "SELECT 1;"},
                ]
            },
            "warnings": [{"message": "Check generated SQL before use."}],
        }
    )

    assert response.request_id == "request-1"
    assert response.text == "Here is the SQL."
    assert response.sql == "SELECT 1;"
    assert response.warnings == ["Check generated SQL before use."]
