-- SQL deployment path for Streamlit in Snowflake.
-- This script uses the project's default object names. Edit these names if
-- your Snowflake database, schema, warehouse, or app name differs.
--
-- Before running CREATE STREAMLIT, upload app/sis_streamlit_app.py and
-- environment.yml to @F1_ANALYTICS.ANALYTICS.F1_APP_STAGE/app.

USE DATABASE F1_ANALYTICS;

CREATE STAGE IF NOT EXISTS ANALYTICS.F1_APP_STAGE
    DIRECTORY = (ENABLE = TRUE);

CREATE STREAMLIT IF NOT EXISTS ANALYTICS.F1_AI_ANALYST
    FROM @F1_ANALYTICS.ANALYTICS.F1_APP_STAGE/app
    MAIN_FILE = 'sis_streamlit_app.py'
    QUERY_WAREHOUSE = F1_WH;

ALTER STREAMLIT ANALYTICS.F1_AI_ANALYST ADD LIVE VERSION FROM LAST;
