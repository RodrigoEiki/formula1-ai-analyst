# Snowflake SQL

These scripts create the Snowflake database objects for the Formula 1 AI Analyst project.

## Execution Order

Set the Snowflake session variables first:

```sql
SET F1_DATABASE = 'F1_ANALYTICS';
SET F1_RAW_SCHEMA = 'RAW';
SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';
```

Run the scripts in this order in the same session:

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

## Assumed Source Tables

The raw table definitions target the common Ergast/Kaggle Formula 1 dataset. The SQL expects uppercase raw column identifiers such as `DRIVERID`, `RACEID`, and `CONSTRUCTORID`.

## Schemas

The scripts use two logical schemas:

- `RAW`: source-aligned Formula 1 tables
- `ANALYTICS`: business-friendly views for Cortex Analyst
