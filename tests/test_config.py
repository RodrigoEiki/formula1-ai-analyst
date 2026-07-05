"""Tests for environment-based configuration helpers."""

from __future__ import annotations

from app.config import load_snowflake_config


def test_load_snowflake_config_uses_default_schema(monkeypatch):
    """The configured schema should be used by default."""
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "account")
    monkeypatch.setenv("SNOWFLAKE_USER", "user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "password")
    monkeypatch.setenv("SNOWFLAKE_ROLE", "role")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "warehouse")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "database")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "public")

    config = load_snowflake_config()

    assert config.schema == "public"


def test_load_snowflake_config_can_prefer_named_schema(monkeypatch):
    """A caller can prefer a specific schema environment variable."""
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "account")
    monkeypatch.setenv("SNOWFLAKE_USER", "user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "password")
    monkeypatch.setenv("SNOWFLAKE_ROLE", "role")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "warehouse")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "database")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "public")
    monkeypatch.setenv("SNOWFLAKE_ANALYTICS_SCHEMA", "analytics")

    config = load_snowflake_config(preferred_schema_env="SNOWFLAKE_ANALYTICS_SCHEMA")

    assert config.schema == "analytics"
