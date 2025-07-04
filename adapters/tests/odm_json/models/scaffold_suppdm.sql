SELECT
    studyid
    ,'SUPPDM' AS RDOMAIN
    ,usubjid
    ,'DM' AS IDVAR
    ,raceoth AS IDVARVAL
    ,'RACEOTH' AS QNAM
    ,'Race, Other Specify' AS QLABEL
    ,raceoth AS QVAL
FROM {% raw %}{{ ref('raw_dm') }}{% endraw %}
WHERE raceoth IS NOT NULL;