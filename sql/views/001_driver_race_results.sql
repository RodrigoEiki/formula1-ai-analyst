-- Required session variables:
-- SET F1_DATABASE = 'F1_ANALYTICS';
-- SET F1_RAW_SCHEMA = 'RAW';
-- SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';

USE DATABASE IDENTIFIER($F1_DATABASE);

CREATE OR REPLACE VIEW IDENTIFIER($F1_ANALYTICS_SCHEMA || '.DRIVER_RACE_RESULTS') AS
WITH races AS (
    SELECT
        RACEID AS race_id,
        YEAR AS season,
        ROUND AS round_number,
        CIRCUITID AS circuit_id,
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
        FORENAME AS driver_forename,
        SURNAME AS driver_surname,
        DOB AS driver_date_of_birth,
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

circuits AS (
    SELECT
        CIRCUITID AS circuit_id,
        NAME AS circuit_name,
        LOCATION AS circuit_location,
        COUNTRY AS circuit_country
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_CIRCUITS')
),

race_results AS (
    SELECT
        RESULTID AS result_id,
        RACEID AS race_id,
        DRIVERID AS driver_id,
        CONSTRUCTORID AS constructor_id,
        GRID AS grid_position,
        POSITION AS finishing_position,
        POSITIONORDER AS classified_position,
        POINTS AS championship_points,
        LAPS AS completed_laps,
        MILLISECONDS AS race_time_milliseconds,
        FASTESTLAP AS fastest_lap_number,
        RANK AS fastest_lap_rank,
        FASTESTLAPTIME AS fastest_lap_time,
        FASTESTLAPSPEED AS fastest_lap_speed,
        STATUSID AS status_id
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_RESULTS')
),

statuses AS (
    SELECT
        STATUSID AS status_id,
        STATUS AS result_status
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_STATUS')
)

SELECT
    race_results.result_id,
    races.season,
    races.round_number,
    races.race_id,
    races.race_name,
    races.race_date,
    circuits.circuit_id,
    circuits.circuit_name,
    circuits.circuit_location,
    circuits.circuit_country,
    drivers.driver_id,
    drivers.driver_reference,
    drivers.driver_code,
    drivers.driver_name,
    drivers.driver_forename,
    drivers.driver_surname,
    drivers.driver_date_of_birth,
    drivers.driver_nationality,
    constructors.constructor_id,
    constructors.constructor_reference,
    constructors.constructor_name,
    constructors.constructor_nationality,
    race_results.grid_position,
    race_results.finishing_position,
    race_results.classified_position,
    race_results.championship_points,
    race_results.completed_laps,
    race_results.race_time_milliseconds,
    race_results.fastest_lap_number,
    race_results.fastest_lap_rank,
    race_results.fastest_lap_time,
    race_results.fastest_lap_speed,
    statuses.result_status,
    race_results.classified_position = 1 AS is_winner,
    race_results.classified_position <= 3 AS is_podium,
    race_results.grid_position = 1 AS is_pole_position
FROM race_results
INNER JOIN races
    ON race_results.race_id = races.race_id
INNER JOIN drivers
    ON race_results.driver_id = drivers.driver_id
INNER JOIN constructors
    ON race_results.constructor_id = constructors.constructor_id
LEFT JOIN circuits
    ON races.circuit_id = circuits.circuit_id
LEFT JOIN statuses
    ON race_results.status_id = statuses.status_id;
