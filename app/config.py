"""Configuration helpers for environment-driven application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class SnowflakeConfig:
    """Snowflake connection settings loaded from environment variables."""

    account: str
    user: str
    password: str
    role: str
    warehouse: str
    database: str
    schema: str


@dataclass(frozen=True)
class CortexAnalystConfig:
    """Cortex Analyst API settings loaded from environment variables."""

    account_url: str
    semantic_model_path: Path | None
    semantic_model_file: str | None
    semantic_view: str | None
    auth_token: str | None
    auth_token_type: str


def _get_required_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_optional_env(name: str) -> str | None:
    """Return an optional environment variable, normalized for blanks."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def load_snowflake_config(
    env_file: Path | None = None,
    preferred_schema_env: str | None = None,
) -> SnowflakeConfig:
    """Load Snowflake connection settings from `.env` and the environment."""
    load_dotenv(dotenv_path=env_file)
    preferred_schema = (
        _get_optional_env(preferred_schema_env)
        if preferred_schema_env is not None
        else None
    )

    return SnowflakeConfig(
        account=_get_required_env("SNOWFLAKE_ACCOUNT"),
        user=_get_required_env("SNOWFLAKE_USER"),
        password=_get_required_env("SNOWFLAKE_PASSWORD"),
        role=_get_required_env("SNOWFLAKE_ROLE"),
        warehouse=_get_required_env("SNOWFLAKE_WAREHOUSE"),
        database=_get_required_env("SNOWFLAKE_DATABASE"),
        schema=preferred_schema or _get_required_env("SNOWFLAKE_SCHEMA"),
    )


def load_cortex_analyst_config(
    env_file: Path | None = None,
) -> CortexAnalystConfig:
    """Load Cortex Analyst settings from `.env` and the environment."""
    load_dotenv(dotenv_path=env_file)

    account = _get_required_env("SNOWFLAKE_ACCOUNT")
    account_url = _get_optional_env("SNOWFLAKE_ACCOUNT_URL")
    if account_url is None:
        account_url = f"https://{account}.snowflakecomputing.com"

    semantic_model_path_value = _get_optional_env("CORTEX_ANALYST_SEMANTIC_MODEL_PATH")
    semantic_model_path = (
        Path(semantic_model_path_value)
        if semantic_model_path_value is not None
        else get_project_root() / "semantic_models" / "f1_analyst.yaml"
    )

    return CortexAnalystConfig(
        account_url=account_url.rstrip("/"),
        semantic_model_path=semantic_model_path,
        semantic_model_file=_get_optional_env("CORTEX_ANALYST_SEMANTIC_MODEL_FILE"),
        semantic_view=_get_optional_env("CORTEX_ANALYST_SEMANTIC_VIEW"),
        auth_token=_get_optional_env("CORTEX_ANALYST_AUTH_TOKEN"),
        auth_token_type=_get_optional_env("CORTEX_ANALYST_AUTH_TOKEN_TYPE") or "OAUTH",
    )


def get_project_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).resolve().parents[1]
