-- Required session variables:
-- SET F1_DATABASE = 'F1_ANALYTICS';
-- SET F1_RAW_SCHEMA = 'RAW';
-- SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';

USE DATABASE IDENTIFIER($F1_DATABASE);

CREATE OR REPLACE VIEW IDENTIFIER($F1_ANALYTICS_SCHEMA || '.QUALIFYING_RESULTS') AS
WITH races AS (
    SELECT
        RACEID AS race_id,
        YEAR AS season,
        ROUND AS round_number,
        NAME AS race_name,
        DATE AS race_date
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_RACES')
),

drivers AS (
    SELECT
        DRIVERID AS driver_id,
        DRIVERREF AS driver_reference,
        CODE AS driver_code,
        TRIM(FORENAME || ' ' || SURNAME) AS driver_name,
        NATIONALITY AS driver_nationality
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_DRIVERS')
),

constructors AS (
    SELECT
        CONSTRUCTORID AS constructor_id,
        CONSTRUCTORREF AS constructor_reference,
        NAME AS constructor_name,
        NATIONALITY AS constructor_nationality
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_CONSTRUCTORS')
),

qualifying AS (
    SELECT
        QUALIFYID AS qualifying_id,
        RACEID AS race_id,
        DRIVERID AS driver_id,
        CONSTRUCTORID AS constructor_id,
        POSITION AS qualifying_position,
        Q1 AS q1_time,
        Q2 AS q2_time,
        Q3 AS q3_time
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_QUALIFYING')
)

SELECT
    qualifying.qualifying_id,
    races.season,
    races.round_number,
    races.race_id,
    races.race_name,
    races.race_date,
    drivers.driver_id,
    drivers.driver_reference,
    drivers.driver_code,
    drivers.driver_name,
    drivers.driver_nationality,
    constructors.constructor_id,
    constructors.constructor_reference,
    constructors.constructor_name,
    constructors.constructor_nationality,
    qualifying.qualifying_position,
    qualifying.q1_time,
    qualifying.q2_time,
    qualifying.q3_time,
    qualifying.qualifying_position = 1 AS is_pole_position
FROM qualifying
INNER JOIN races
    ON qualifying.race_id = races.race_id
INNER JOIN drivers
    ON qualifying.driver_id = drivers.driver_id
INNER JOIN constructors
    ON qualifying.constructor_id = constructors.constructor_id;
