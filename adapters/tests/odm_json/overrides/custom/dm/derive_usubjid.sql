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
-- Unique Subject Identifier (USUBJID) --
-----------------------------------------
CASE
    WHEN prevstudy IS NULL OR TRIM(prevstudy) = '' THEN
        CASE
            WHEN prevsubj IS NOT NULL AND TRIM(prevsubj) <> '' THEN
                -- ERROR: prevstudy is null but prevsubj is not
                NULL
            WHEN rescreennum_raw IS NOT NULL AND TRIM(rescreennum_raw) <> '' THEN
                CONCAT(project, '-', rescreennum_raw)
            ELSE
                CONCAT(project, '-', subject)
        END
    ELSE
        CASE
            WHEN prevsubj IS NULL OR TRIM(prevsubj) = '' THEN
                -- ERROR: prevstudy not null but prevsubj is null
                NULL
            ELSE
                CONCAT(prevstudy, '-', prevsubj)
        END
END AS USUBJID,

-- Issue flag for unexpected USUBJID source combinations
CASE
    WHEN (prevstudy IS NULL OR TRIM(prevstudy) = '') AND (prevsubj IS NOT NULL AND TRIM(prevsubj) <> '')
        THEN 'ERR: prevstudy is null but prevsubj is not'
    WHEN (prevstudy IS NOT NULL AND TRIM(prevstudy) <> '') AND (prevsubj IS NULL OR TRIM(prevsubj) = '')
        THEN 'ERR: prevstudy not null but prevsubj is null'
    ELSE NULL
END AS USUBJID_ISSUE_FLAG