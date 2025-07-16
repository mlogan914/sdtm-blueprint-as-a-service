WITH raw_dm AS (
    SELECT * FROM {{ ref('raw_dm') }}
),
raw_ds AS (
    SELECT * FROM {{ ref('raw_ds') }}
),
dm_input AS (
    SELECT
        dm.*,
        ds.DSDECOD,
        ds.DSDTC
    FROM raw_dm dm
    LEFT JOIN raw_ds ds
        ON dm.SUBJID = ds.SUBJID AND ds.DSCAT = 'DISPOSITION'
)
SELECT * FROM dm_input;
