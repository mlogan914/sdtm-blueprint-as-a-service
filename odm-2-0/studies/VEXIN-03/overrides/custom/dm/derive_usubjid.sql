CASE
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
