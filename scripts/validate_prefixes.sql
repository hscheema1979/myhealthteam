-- Validate prefixes: detect 3-char-prefix ("???-") and BlessedCare variants
PRAGMA foreign_keys = OFF;
-- Build raw combined table (same sources as normalized compare)
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
-- Apply the same normalization rules used in compare_tables_normalized.sql
CREATE TEMP TABLE all_norm AS
SELECT raw,
    LTRIM(
        CASE
            WHEN raw LIKE 'BlessedCare-%' THEN substr(raw, length('BlessedCare-') + 1)
            WHEN raw LIKE 'BlessedCare %' THEN substr(raw, length('BlessedCare ') + 1)
            WHEN raw LIKE 'BleessedCare-%' THEN substr(raw, length('BleessedCare-') + 1)
            WHEN raw LIKE 'BleessedCare %' THEN substr(raw, length('BleessedCare ') + 1)
            WHEN LOWER(raw) LIKE 'zen,%' THEN substr(raw, instr(raw, ',') + 1)
            WHEN LOWER(raw) LIKE 'zen %' THEN substr(raw, instr(raw, ' ') + 1)
            WHEN LOWER(raw) LIKE '3pr %' THEN substr(raw, instr(raw, ' ') + 1)
            WHEN LOWER(raw) LIKE '3pr-%' THEN substr(raw, instr(raw, '-') + 1)
            WHEN instr(raw, '-') > 0
            AND instr(raw, '-') <= 12 THEN substr(raw, instr(raw, '-') + 1)
            WHEN instr(raw, ' ') > 0
            AND length(substr(raw, 1, instr(raw, ' ') -1)) <= 4
            AND (
                substr(raw, 1, 1) GLOB '[0-9]'
                OR lower(substr(raw, 1, instr(raw, ' ') -1)) IN ('zen', '3pr', 'zen,', '3pr,')
            ) THEN substr(raw, instr(raw, ' ') + 1)
            ELSE raw
        END
    ) AS norm
FROM all_raw;
-- Trim results
CREATE TEMP TABLE all_norm_trim AS
SELECT raw,
    TRIM(norm) AS norm
FROM all_norm;
-- 1) How many raw rows start with exactly three characters followed by a hyphen? (after trimming)
SELECT COUNT(*) AS three_char_prefix_raw
FROM all_raw
WHERE TRIM(raw) GLOB '???-*';
-- 2) How many normalized rows still start with three-char- prefix? (should be 0 ideally)
SELECT COUNT(*) AS three_char_prefix_after_norm
FROM all_norm_trim
WHERE norm GLOB '???-*';
-- 1a) More strict: how many raw rows start with three alphanumeric characters followed by a hyphen
SELECT COUNT(*) AS three_alnum_hyphen_raw
FROM all_raw
WHERE TRIM(raw) GLOB '[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]-*';
-- 1b) After normalization: three alnum + hyphen remaining
SELECT COUNT(*) AS three_alnum_hyphen_after_norm
FROM all_norm_trim
WHERE norm GLOB '[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]-*';
-- 1c) Check for patterns where a short alphanumeric token (1-4 chars) appears before a hyphen
SELECT COUNT(*) AS short_alnum_token_before_hyphen_raw
FROM all_raw
WHERE instr(TRIM(raw), '-') > 0
    AND length(substr(TRIM(raw), 1, instr(TRIM(raw), '-') -1)) BETWEEN 1 AND 4
    AND substr(TRIM(raw), 1, instr(TRIM(raw), '-') -1) GLOB '[A-Za-z0-9]*';
-- 1d) Show samples where the prefix is three alnum + hyphen
SELECT DISTINCT TRIM(raw) AS sample_three_alnum
FROM all_raw
WHERE TRIM(raw) GLOB '[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]-*'
LIMIT 200;
-- 1e) Show samples where a short alnum token appears before a hyphen (1-4 chars)
SELECT DISTINCT TRIM(raw) AS sample_short_token
FROM all_raw
WHERE instr(TRIM(raw), '-') > 0
    AND length(substr(TRIM(raw), 1, instr(TRIM(raw), '-') -1)) BETWEEN 1 AND 4
    AND substr(TRIM(raw), 1, instr(TRIM(raw), '-') -1) GLOB '[A-Za-z0-9]*'
LIMIT 200;
-- 1f) Colon-suffixed prefix checks: e.g. "ABC: rest"
SELECT COUNT(*) AS colon_prefix_raw
FROM all_raw
WHERE TRIM(raw) GLOB '[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]:*';
SELECT COUNT(*) AS colon_prefix_after_norm
FROM all_norm_trim
WHERE norm GLOB '[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]:*';
SELECT DISTINCT TRIM(raw) AS sample_colon_prefix
FROM all_raw
WHERE TRIM(raw) GLOB '[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]:*'
LIMIT 200;
-- 3) Show samples where a three-char prefix remains after normalization
SELECT raw,
    norm
FROM all_norm_trim
WHERE norm GLOB '???-*'
LIMIT 100;
-- 4) BlessedCare / BleessedCare counts before and after
SELECT COUNT(*) AS blessedcare_raw
FROM all_raw
WHERE raw LIKE 'BlessedCare-%'
    OR raw LIKE 'BlessedCare %';
SELECT COUNT(*) AS blessedcare_after_norm
FROM all_norm_trim
WHERE norm LIKE 'BlessedCare%';
SELECT COUNT(*) AS bleessedcare_raw
FROM all_raw
WHERE raw LIKE 'BleessedCare-%'
    OR raw LIKE 'BleessedCare %';
SELECT COUNT(*) AS bleessedcare_after_norm
FROM all_norm_trim
WHERE norm LIKE 'BleessedCare%';
-- 5) zen and 3pr checks (before/after)
SELECT COUNT(*) AS zen_raw
FROM all_raw
WHERE LOWER(raw) LIKE 'zen,%'
    OR LOWER(raw) LIKE 'zen %';
SELECT COUNT(*) AS zen_after_norm
FROM all_norm_trim
WHERE LOWER(norm) LIKE 'zen,%'
    OR LOWER(norm) LIKE 'zen %';
SELECT COUNT(*) AS threepr_raw
FROM all_raw
WHERE LOWER(raw) LIKE '3pr,%'
    OR LOWER(raw) LIKE '3pr %'
    OR LOWER(raw) LIKE '3pr-%';
SELECT COUNT(*) AS threepr_after_norm
FROM all_norm_trim
WHERE LOWER(norm) LIKE '3pr,%'
    OR LOWER(norm) LIKE '3pr %'
    OR LOWER(norm) LIKE '3pr-%';
-- 6) Show some examples of raw values that matched the three-character prefix pattern (for manual review)
SELECT DISTINCT TRIM(raw) AS sample_raw
FROM all_raw
WHERE TRIM(raw) GLOB '???-*'
LIMIT 200;
-- Cleanup
DROP TABLE all_raw;
DROP TABLE all_norm;
DROP TABLE all_norm_trim;
-- End