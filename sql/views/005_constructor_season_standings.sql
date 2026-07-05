-- Required session variables:
-- SET F1_DATABASE = 'F1_ANALYTICS';
-- SET F1_RAW_SCHEMA = 'RAW';
-- SET F1_ANALYTICS_SCHEMA = 'ANALYTICS';

USE DATABASE IDENTIFIER($F1_DATABASE);

CREATE OR REPLACE VIEW IDENTIFIER($F1_ANALYTICS_SCHEMA || '.CONSTRUCTOR_SEASON_STANDINGS') AS
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

constructors AS (
    SELECT
        CONSTRUCTORID AS constructor_id,
        CONSTRUCTORREF AS constructor_reference,
        NAME AS constructor_name,
        NATIONALITY AS constructor_nationality
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_CONSTRUCTORS')
),

standings AS (
    SELECT
        CONSTRUCTORSTANDINGSID AS constructor_standings_id,
        RACEID AS race_id,
        CONSTRUCTORID AS constructor_id,
        POINTS AS season_points,
        POSITION AS championship_position,
        WINS AS season_wins
    FROM IDENTIFIER($F1_RAW_SCHEMA || '.RAW_CONSTRUCTOR_STANDINGS')
)

SELECT
    final_races.season,
    standings.constructor_standings_id,
    constructors.constructor_id,
    constructors.constructor_reference,
    constructors.constructor_name,
    constructors.constructor_nationality,
    standings.championship_position,
    standings.season_points,
    standings.season_wins,
    standings.championship_position = 1 AS is_constructor_champion
FROM standings
INNER JOIN final_races
    ON standings.race_id = final_races.race_id
INNER JOIN constructors
    ON standings.constructor_id = constructors.constructor_id;
