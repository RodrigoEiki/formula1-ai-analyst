-- Required session variables:
-- SET F1_DATABASE = 'F1_ANALYTICS';
-- SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';

USE DATABASE IDENTIFIER($F1_DATABASE);

CREATE OR REPLACE VIEW IDENTIFIER($F1_ANALYTICS_SCHEMA || '.RACE_SUMMARY') AS
WITH driver_results AS (
    SELECT
        season,
        round_number,
        race_id,
        race_name,
        race_date,
        circuit_id,
        circuit_name,
        circuit_location,
        circuit_country,
        driver_id,
        driver_name,
        constructor_name,
        classified_position,
        championship_points,
        is_winner,
        is_podium
    FROM IDENTIFIER($F1_ANALYTICS_SCHEMA || '.DRIVER_RACE_RESULTS')
),

race_rollup AS (
    SELECT
        season,
        round_number,
        race_id,
        race_name,
        race_date,
        circuit_id,
        circuit_name,
        circuit_location,
        circuit_country,
        COUNT(DISTINCT driver_id) AS classified_drivers,
        SUM(championship_points) AS total_points_awarded
    FROM driver_results
    GROUP BY
        season,
        round_number,
        race_id,
        race_name,
        race_date,
        circuit_id,
        circuit_name,
        circuit_location,
        circuit_country
),

winners AS (
    SELECT
        race_id,
        driver_name AS winning_driver,
        constructor_name AS winning_constructor
    FROM driver_results
    WHERE is_winner
),

podiums AS (
    SELECT
        race_id,
        LISTAGG(driver_name, ', ') WITHIN GROUP (ORDER BY classified_position) AS podium_drivers
    FROM driver_results
    WHERE is_podium
    GROUP BY race_id
)

SELECT
    race_rollup.season,
    race_rollup.round_number,
    race_rollup.race_id,
    race_rollup.race_name,
    race_rollup.race_date,
    race_rollup.circuit_id,
    race_rollup.circuit_name,
    race_rollup.circuit_location,
    race_rollup.circuit_country,
    winners.winning_driver,
    winners.winning_constructor,
    podiums.podium_drivers,
    race_rollup.classified_drivers,
    race_rollup.total_points_awarded
FROM race_rollup
LEFT JOIN winners
    ON race_rollup.race_id = winners.race_id
LEFT JOIN podiums
    ON race_rollup.race_id = podiums.race_id;
