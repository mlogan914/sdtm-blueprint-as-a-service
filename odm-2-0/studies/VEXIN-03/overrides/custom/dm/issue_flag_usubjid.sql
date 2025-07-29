CASE
    WHEN (prevstudy IS NULL OR TRIM(prevstudy) = '') AND (prevsubj IS NOT NULL AND TRIM(prevsubj) <> '')
        THEN 'ERR: prevstudy is null but prevsubj is not'
    WHEN (prevstudy IS NOT NULL AND TRIM(prevstudy) <> '') AND (prevsubj IS NULL OR TRIM(prevsubj) = '')
        THEN 'ERR: prevstudy not null but prevsubj is null'
    ELSE NULL
END AS USUBJID_ISSUE_FLAG