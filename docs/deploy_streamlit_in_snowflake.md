# Deploy Streamlit in Snowflake

This project includes a Snowflake-native Streamlit entrypoint:

```text
app/sis_streamlit_app.py
```

Use this file for Streamlit in Snowflake. It uses the active Snowpark session to run generated SQL and Snowflake's internal API bridge to call Cortex Analyst, so it does not need local `.env` credentials or a Snowflake connector login.

## Prerequisites

Your Snowflake role needs:

- `USAGE` on the database used by the app
- `USAGE` and `CREATE STREAMLIT` on the schema used by the app
- `USAGE` on the warehouse used by the app
- privileges to query the analytics views
- privileges to use Cortex Analyst

## 1. Create Snowflake Objects

Run the existing SQL scripts first:

```text
sql/ddl/001_create_database_and_schemas.sql
sql/ddl/002_create_raw_tables.sql
sql/ddl/003_create_semantic_model_stage.sql
sql/views/001_driver_race_results.sql
sql/views/002_constructor_race_results.sql
sql/views/003_race_summary.sql
sql/views/004_driver_season_standings.sql
sql/views/005_constructor_season_standings.sql
sql/views/006_qualifying_results.sql
```

Set these variables before running the scripts:

```sql
SET F1_DATABASE = 'F1_ANALYTICS';
SET F1_RAW_SCHEMA = 'RAW';
SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';
```

## 2. Upload the Semantic Model

Upload the semantic YAML to the stage created by `003_create_semantic_model_stage.sql`:

```sql
PUT file://semantic_models/f1_analyst.yaml
    @F1_ANALYTICS.ANALYTICS.F1_SEMANTIC_STAGE
    AUTO_COMPRESS = FALSE
    OVERWRITE = TRUE;
```

The app defaults to this staged semantic model path:

```text
@F1_ANALYTICS.ANALYTICS.F1_SEMANTIC_STAGE/f1_analyst.yaml
```

## 3. Deploy with Snowflake CLI

Edit `snowflake.yml` if your warehouse or app name differs from the defaults:

```yaml
query_warehouse: F1_WH
identifier: F1_AI_ANALYST
```

Deploy:

```bash
snow streamlit deploy --open
```

## 4. Deploy with SQL Instead

Upload the app files to a stage:

```sql
CREATE STAGE IF NOT EXISTS F1_ANALYTICS.ANALYTICS.F1_APP_STAGE
    DIRECTORY = (ENABLE = TRUE);

PUT file://app/sis_streamlit_app.py
    @F1_ANALYTICS.ANALYTICS.F1_APP_STAGE/app
    AUTO_COMPRESS = FALSE
    OVERWRITE = TRUE;

PUT file://environment.yml
    @F1_ANALYTICS.ANALYTICS.F1_APP_STAGE/app
    AUTO_COMPRESS = FALSE
    OVERWRITE = TRUE;
```

Then run:

```text
sql/deploy_streamlit_in_snowflake.sql
```

The script uses the default object names `F1_ANALYTICS`, `ANALYTICS`, `F1_WH`, and `F1_AI_ANALYST`. Edit the script if your account uses different names.

## Runtime Notes

The local app remains available at `app/streamlit_app.py`. Use it for local development.

Use `app/sis_streamlit_app.py` for Streamlit in Snowflake deployment.
