-- Required session variables:
-- SET F1_DATABASE = 'F1_ANALYTICS';
-- SET F1_RAW_SCHEMA = 'RAW';
-- SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';

USE DATABASE IDENTIFIER($F1_DATABASE);

CREATE OR REPLACE VIEW IDENTIFIER($F1_ANALYTICS_SCHEMA || '.DRIVER_SEASON_STANDINGS') AS
WITH final_race_by_season AS (
    SELECT
        YEAR AS season,
        MAX(ROUND) AS final_round
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_RACES')
    GROUP BY YEAR
),

final_races AS (
    SELECT
        races.RACEID AS race_id,
        races.YEAR AS season
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_RACES') AS races
    INNER JOIN final_race_by_season
        ON races.YEAR = final_race_by_season.season
        AND races.ROUND = final_race_by_season.final_round
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

standings AS (
    SELECT
        DRIVERSTANDINGSID AS driver_standings_id,
        RACEID AS race_id,
        DRIVERID AS driver_id,
        POINTS AS season_points,
        POSITION AS championship_position,
        WINS AS season_wins
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_DRIVER_STANDINGS')
)

SELECT
    final_races.season,
    standings.driver_standings_id,
    drivers.driver_id,
    drivers.driver_reference,
    drivers.driver_code,
    drivers.driver_name,
    drivers.driver_nationality,
    standings.championship_position,
    standings.season_points,
    standings.season_wins,
    standings.championship_position = 1 AS is_world_champion
FROM standings
INNER JOIN final_races
    ON standings.race_id = final_races.race_id
INNER JOIN drivers
    ON standings.driver_id = drivers.driver_id;
