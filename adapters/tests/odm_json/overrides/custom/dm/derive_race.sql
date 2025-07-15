/********************************************************************************
* File        : custom_fields.sql
* Purpose     : Injects custom field-level derivations into SDTM scaffold model
* Project     : Template-Driven SDTM Blueprint Generator
* Author      : Melanie Logan
* Created     : 2025-07-15
*
* Description :
*   This override file provides domain-specific custom SQL logic for derived
*   variables not covered by standard mappings. These expressions are injected
*   during the scaffold phase of SDTM model generation using Jinja templates.
*
* Usage       :
*   - Place this file in overrides/<domain>/custom_fields.sql
*   - Referenced automatically when Mapping_Type is 'Derived' but not standard
*
* Notes       :
*   - Must be valid SQL expressions, typically used in SELECT fields
*   - Comments should clearly mark each derived variable block
*   - Supports integration with dbt-based pipelines
********************************************************************************/

-----------------------------------------
-- Race (RACE)                         --
-----------------------------------------
CASE
    WHEN COALESCE(raceoth, '') = ''
         THEN CASE
             WHEN COALESCE(raceaian, 0) + COALESCE(raceasian, 0) + COALESCE(racebaa, 0) + COALESCE(racenhopi, 0) + COALESCE(racewhite, 0) > 1
                 THEN 'MULTIPLE'
             WHEN race_aian = 1 THEN 'AMERICAN INDIAN OR ALASKA NATIVE'
             WHEN race_asian = 1 THEN 'ASIAN'
             WHEN race_black = 1 THEN 'BLACK OR AFRICAN AMERICAN'
             WHEN race_nhpi = 1 THEN 'NATIVE HAWAIIAN OR OTHER PACIFIC ISLANDER'
             WHEN race_white = 1 THEN 'WHITE'
             ELSE NULL
         END
    WHEN COALESCE(raceoth, '') <> ''
         THEN CASE
             WHEN COALESCE(race_aian, 0) + COALESCE(race_asian, 0) + COALESCE(race_black, 0) + COALESCE(race_nhpi, 0) + COALESCE(race_white, 0) >= 1
                 THEN 'MULTIPLE'
             ELSE 'OTHER'
         END
END AS RACE