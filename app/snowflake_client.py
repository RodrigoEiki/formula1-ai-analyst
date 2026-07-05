"""Snowflake connector helpers used by the application."""

from __future__ import annotations

import logging

import pandas as pd
import snowflake.connector
from snowflake.connector import SnowflakeConnection

from app.config import SnowflakeConfig

logger = logging.getLogger(__name__)


def connect_to_snowflake(config: SnowflakeConfig) -> SnowflakeConnection:
    """Create a Snowflake connection from validated configuration."""
    logger.info(
        "Connecting to Snowflake account=%s database=%s schema=%s",
        config.account,
        config.database,
        config.schema,
    )
    return snowflake.connector.connect(
        account=config.account,
        user=config.user,
        password=config.password,
        role=config.role,
        warehouse=config.warehouse,
        database=config.database,
        schema=config.schema,
    )


def execute_query(connection: SnowflakeConnection, sql: str) -> pd.DataFrame:
    """Execute SQL in Snowflake and return the result as a pandas DataFrame."""
    logger.info("Executing generated SQL")
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        return cursor.fetch_pandas_all()
    finally:
        cursor.close()
