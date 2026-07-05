-- Required session variables:
-- SET F1_DATABASE = 'F1_ANALYTICS';
-- SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';

USE DATABASE IDENTIFIER($F1_DATABASE);

CREATE OR REPLACE VIEW IDENTIFIER($F1_ANALYTICS_SCHEMA || '.CONSTRUCTOR_RACE_RESULTS') AS
WITH driver_results AS (
    SELECT
        season,
        round_number,
        race_id,
        race_name,
        race_date,
        circuit_id,
        circuit_name,
        circuit_country,
        constructor_id,
        constructor_reference,
        constructor_name,
        constructor_nationality,
        driver_id,
        driver_name,
        championship_points,
        is_winner,
        is_podium
    FROM IDENTIFIER($F1_ANALYTICS_SCHEMA || '.DRIVER_RACE_RESULTS')
)

SELECT
    season,
    round_number,
    race_id,
    race_name,
    race_date,
    circuit_id,
    circuit_name,
    circuit_country,
    constructor_id,
    constructor_reference,
    constructor_name,
    constructor_nationality,
    COUNT(DISTINCT driver_id) AS classified_drivers,
    SUM(championship_points) AS constructor_points,
    SUM(IFF(is_winner, 1, 0)) AS wins,
    SUM(IFF(is_podium, 1, 0)) AS podiums,
    LISTAGG(driver_name, ', ') WITHIN GROUP (ORDER BY driver_name) AS drivers
FROM driver_results
GROUP BY
    season,
    round_number,
    race_id,
    race_name,
    race_date,
    circuit_id,
    circuit_name,
    circuit_country,
    constructor_id,
    constructor_reference,
    constructor_name,
    constructor_nationality;
