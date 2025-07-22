-- ============================================
-- Step 1: Pre-Merge Input Data
-- ============================================
-- This CTE (if present) prepares raw inputs from one or more source datasets
-- into a unified input structure for downstream derivations.
-- The logic is defined in: overrides/custom/<domain>/prep_input_cte.sql
{% include 'overrides/custom/dm/prep_input_cte.sql' %}

-- ============================================
-- Step 2: Build SDTM Domain Variables
-- ============================================
-- This SELECT block builds the SDTM-compliant domain using:
--  - Direct mappings from source columns
--  - Standard derivation snippets (injected)
--  - Custom derivation snippets (injected per domain)
--  - Null placeholders for unmapped variables (with TODO comments)
-- Column order is based on SDTMIG metadata
SELECT
    ,studyid AS STUDYID
    ,domain AS DOMAIN
    ,NULL AS USUBJID  -- TODO: Custom derivation file missing for USUBJID
    ,subjid AS SUBJID
    ,NULL AS RFSTDTC
    ,NULL AS RFENDTC
    ,NULL AS RFXSTDTC
    ,NULL AS RFXENDTC
    ,NULL AS RFCSTDTC
    ,NULL AS RFCENDTC
    ,rficdtc AS RFICDTC
    ,NULL AS RFPENDTC
    ,NULL AS DTHDTC
    ,NULL AS DTHFL
    ,siteid AS SITEID
    ,NULL AS INVID
    ,NULL AS INVNAM
    ,brthdtc AS BRTHDTC
    ,{% include 'overrides/standard/derive_age.sql' %} AS AGE
    ,NULL AS AGEU
    ,sex AS SEX
    ,NULL AS RACE  -- TODO: Custom derivation file missing for RACE
    ,ethnic AS ETHNIC
    ,NULL AS ARMCD  -- TODO: Custom derivation file missing for ARMCD
    ,NULL AS ARM  -- TODO: Custom derivation file missing for ARM
    ,NULL AS ACTARMCD  -- TODO: Custom derivation file missing for ACTARMCD
    ,NULL AS ACTARM  -- TODO: Custom derivation file missing for ACTARM
    ,NULL AS ARMNRS  -- TODO: Custom derivation file missing for ARMNRS
    ,NULL AS ACTARMUD  -- TODO: Custom derivation file missing for ACTARMUD
    ,country AS COUNTRY
    ,dmdtc AS DMDTC
    ,NULL AS DMDY
    ,NULL AS QVAL
    ,NULL AS DY  -- TODO: Standard derivation file missing for DY
    ,NULL AS EPOCH  -- TODO: Standard derivation file missing for EPOCH
    ,NULL AS VISIT  -- TODO: Standard derivation file missing for VISIT
    ,NULL AS VISITDY  -- TODO: Standard derivation file missing for VISITDY

FROM { { domain.lower() } }_input;