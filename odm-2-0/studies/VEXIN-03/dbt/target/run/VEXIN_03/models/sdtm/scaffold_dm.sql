
  
  create view "dev"."main"."scaffold_dm__dbt_tmp" as (
    


-- ============================================
-- Step 2: Build SDTM Domain Variables
-- ============================================
SELECT
    raw_dm.studyid AS STUDYID
    ,raw_dm.domain AS DOMAIN
    -- Injected custom: derive_usubjid.sql
    ,CASE
    WHEN prevstudy IS NULL OR TRIM(CAST(prevstudy AS VARCHAR)) = '' THEN
        CASE
            WHEN prevsubj IS NOT NULL AND TRIM(CAST(prevsubj AS VARCHAR)) <> '' THEN
                -- ERROR: prevstudy is null but prevsubj is not
                NULL
            WHEN rescreennum_raw IS NOT NULL AND TRIM(CAST(rescreennum_raw AS VARCHAR)) <> '' THEN
                CONCAT(project, '-', rescreennum_raw)
            ELSE
                CONCAT(project, '-', subject)
        END
    ELSE
        CASE
            WHEN prevsubj IS NULL OR TRIM(CAST(prevsubj AS VARCHAR)) = '' THEN
                -- ERROR: prevstudy not null but prevsubj is null
                NULL
            ELSE
                CONCAT(prevstudy, '-', prevsubj)
        END
    END AS USUBJID
    ,raw_dm.subject AS SUBJID
    ,NULL AS RFSTDTC
    ,NULL AS RFENDTC
    ,NULL AS RFXSTDTC
    ,NULL AS RFXENDTC
    ,NULL AS RFCSTDTC
    ,NULL AS RFCENDTC
    -- Injected custom: derive_rficdtc.sql
    ,
    CASE 
        WHEN RFICDTC_RAW IS NULL OR TRIM(RFICDTC_RAW) = '' THEN NULL
        ELSE STRFTIME(STRPTIME(RFICDTC_RAW, '%m/%d/%Y'), '%Y-%m-%d')
    END
 AS RFICDTC
    ,NULL AS RFPENDTC
    ,NULL AS DTHDTC
    ,NULL AS DTHFL
    ,raw_dm.siteid AS SITEID
    ,NULL AS INVID
    ,NULL AS INVNAM
    -- Injected custom: derive_brthdtc.sql
    ,
    CASE 
        WHEN BRTHDTC_RAW IS NULL OR TRIM(BRTHDTC_RAW) = '' THEN NULL
        ELSE STRFTIME(STRPTIME(BRTHDTC_RAW, '%m/%d/%Y'), '%Y-%m-%d')
    END
 AS BRTHDTC
    ,NULL AS AGE  -- TODO: Derived variable AGE needs a derivation
    ,NULL AS AGEU
    ,raw_dm.sex AS SEX
    -- Injected custom: derive_race.sql
    ,CASE
    WHEN COALESCE(raceoth, '') = ''
         THEN CASE
             WHEN COALESCE(race_aian, 0) + COALESCE(race_asian, 0) + COALESCE(race_black, 0) + COALESCE(race_nhpi, 0) + COALESCE(race_white, 0) > 1
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
    ,raw_dm.ethnic AS ETHNIC
    ,NULL AS ARMCD  -- TODO: Derived variable ARMCD needs a derivation
    ,NULL AS ARM  -- TODO: Derived variable ARM needs a derivation
    ,NULL AS ACTARMCD  -- TODO: Derived variable ACTARMCD needs a derivation
    ,NULL AS ACTARM  -- TODO: Derived variable ACTARM needs a derivation
    ,NULL AS ARMNRS  -- TODO: Derived variable ARMNRS needs a derivation
    ,NULL AS ACTARMUD  -- TODO: Derived variable ACTARMUD needs a derivation
    ,raw_dm.country AS COUNTRY
    -- Injected custom: derive_dmdtc.sql
    ,
    CASE 
        WHEN DMDTC_RAW IS NULL OR TRIM(DMDTC_RAW) = '' THEN NULL
        ELSE STRFTIME(STRPTIME(DMDTC_RAW, '%m/%d/%Y'), '%Y-%m-%d')
    END
 AS DMDTC
    ,NULL AS DMDY
    ,NULL AS QVAL
    ,NULL AS DY  -- TODO: Standard derivation file missing for DY
    ,NULL AS EPOCH  -- TODO: Standard derivation file missing for EPOCH
    ,NULL AS ISSUE_FLAG_USUBJID  -- TODO: Custom derivation file missing for ISSUE_FLAG_USUBJID

FROM "dev"."main"."raw_dm"
  );
