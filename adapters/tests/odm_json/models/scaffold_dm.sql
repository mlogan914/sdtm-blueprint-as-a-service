SELECT
    ,studyid AS STUDYID  -- Study Identifier
    ,domain AS DOMAIN  -- Domain Abbreviation
    ,subjid AS SUBJID  -- Subject Identifier for the Study
    ,rficdtc AS RFICDTC  -- Date/Time of Informed Consent
    ,siteid AS SITEID  -- Study Site Identifier
    ,brthdtc AS BRTHDTC  -- Date/Time of Birth
    -- Derived variable: AGE
    -- Candidate inputs: age
    ,{% raw %}{{ derive_age(...) }}{% endraw %} AS AGE  -- Age
    ,sex AS SEX  -- Sex
    -- Derived variable: RACE
    -- Candidate inputs: race
    ,{% raw %}{{ derive_race(...) }}{% endraw %} AS RACE  -- Race
    ,ethnic AS ETHNIC  -- Ethnicity
    -- Derived variable: ARMCD
    -- Candidate inputs: armcd
    ,{% raw %}{{ derive_armcd(...) }}{% endraw %} AS ARMCD  -- Planned Arm Code
    -- Derived variable: ARM
    -- Candidate inputs: arm
    ,{% raw %}{{ derive_arm(...) }}{% endraw %} AS ARM  -- Description of Planned Arm
    -- Derived variable: ACTARMCD
    -- Candidate inputs: actarmcd
    ,{% raw %}{{ derive_actarmcd(...) }}{% endraw %} AS ACTARMCD  -- Actual Arm Code
    -- Derived variable: ACTARM
    -- Candidate inputs: actarm
    ,{% raw %}{{ derive_actarm(...) }}{% endraw %} AS ACTARM  -- Description of Actual Arm
    -- Derived variable: ARMNRS
    -- Candidate inputs: armnrs
    ,{% raw %}{{ derive_armnrs(...) }}{% endraw %} AS ARMNRS  -- Reason Arm and/or Actual Arm is Null
    -- Derived variable: ACTARMUD
    -- Candidate inputs: actarmud
    ,{% raw %}{{ derive_actarmud(...) }}{% endraw %} AS ACTARMUD  -- Description of Unplanned Actual Arm
    ,country AS COUNTRY  -- Country
    ,dmdtc AS DMDTC  -- Date/Time of Collection
FROM {% raw %}{{ ref('raw_dm') }}{% endraw %};