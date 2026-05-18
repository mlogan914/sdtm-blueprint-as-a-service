WITH

dm_input AS (
    SELECT
         dm.*
        ,ds.armcd
        ,ds.raw_arm
    FROM {{ ref('raw_dm') }} dm LEFT JOIN 
         {{ ref('raw_ds') }} ds
    ON dm.subject = ds.subject
)