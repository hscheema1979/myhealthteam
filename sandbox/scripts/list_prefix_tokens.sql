-- List candidate prefix tokens seen before '-' and short tokens before space
PRAGMA foreign_keys = OFF;
CREATE TEMP TABLE all_raw AS
SELECT TRIM(
        COALESCE(Last, '') || ' ' || COALESCE(First, '') || ' ' || COALESCE(DOB, '')
    ) AS raw
FROM SOURCE_PATIENT_DATA
WHERE (
        Last IS NOT NULL
        OR First IS NOT NULL
        OR DOB IS NOT NULL
    )
    AND TRIM(
        COALESCE(Last, '') || ' ' || COALESCE(First, '') || ' ' || COALESCE(DOB, '')
    ) != ''
UNION ALL
SELECT TRIM([LAST FIRST DOB]) AS raw
FROM SOURCE_PATIENT_DATA
WHERE [LAST FIRST DOB] IS NOT NULL
    AND TRIM([LAST FIRST DOB]) <> ''
UNION ALL
SELECT TRIM([Pt Name]) AS raw
FROM SOURCE_COORDINATOR_TASKS_HISTORY
WHERE [Pt Name] IS NOT NULL
    AND TRIM([Pt Name]) <> ''
UNION ALL
SELECT TRIM([Patient Last, First DOB]) AS raw
FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE [Patient Last, First DOB] IS NOT NULL
    AND TRIM([Patient Last, First DOB]) <> ''
UNION ALL
SELECT TRIM([Patient Last, First DOB.1]) AS raw
FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE [Patient Last, First DOB.1] IS NOT NULL
    AND TRIM([Patient Last, First DOB.1]) <> '';
-- Extract prefix token before hyphen (up to 20 chars) and count occurrences
CREATE TEMP TABLE prefix_hyphen AS
SELECT UPPER(TRIM(substr(raw, 1, instr(raw, '-') -1))) AS prefix,
    COUNT(*) AS cnt
FROM all_raw
WHERE instr(raw, '-') > 0
    AND length(substr(raw, 1, instr(raw, '-') -1)) <= 20
GROUP BY prefix
ORDER BY cnt DESC;
SELECT prefix,
    cnt
FROM prefix_hyphen
LIMIT 200;
-- Show examples for top prefixes (top 20)
SELECT p.prefix,
    ar.raw
FROM (
        SELECT prefix
        FROM prefix_hyphen
        LIMIT 20
    ) p
    JOIN all_raw ar ON UPPER(TRIM(substr(ar.raw, 1, instr(ar.raw, '-') -1))) = p.prefix
LIMIT 200;
-- Extract short token before first space (1-4 chars), candidate prefix tokens
CREATE TEMP TABLE short_space_prefix AS
SELECT UPPER(TRIM(substr(raw, 1, instr(raw, ' ') -1))) AS token,
    COUNT(*) AS cnt
FROM all_raw
WHERE instr(raw, ' ') > 0
    AND length(substr(raw, 1, instr(raw, ' ') -1)) BETWEEN 1 AND 4
GROUP BY token
ORDER BY cnt DESC;
SELECT token,
    cnt
FROM short_space_prefix
LIMIT 200;
-- Examples of short-space tokens
SELECT token,
    raw
FROM (
        SELECT UPPER(TRIM(substr(raw, 1, instr(raw, ' ') -1))) AS token,
            raw
        FROM all_raw
        WHERE instr(raw, ' ') > 0
            AND length(substr(raw, 1, instr(raw, ' ') -1)) BETWEEN 1 AND 4
    )
WHERE token IN (
        SELECT token
        FROM short_space_prefix
        LIMIT 20
    )
LIMIT 200;
-- Cleanup
DROP TABLE all_raw;
DROP TABLE prefix_hyphen;
DROP TABLE short_space_prefix;
-- End