CASE
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