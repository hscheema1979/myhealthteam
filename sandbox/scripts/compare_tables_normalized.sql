-- Normalized comparison: strip common prefixes before comparing name+DOB across source tables
-- Build raw combined table
CREATE TEMP TABLE all_raw AS
SELECT TRIM(
        COALESCE(Last, '') || ' ' || COALESCE(First, '') || ' ' || COALESCE(DOB, '')
    ) AS raw,
    'SOURCE_PATIENT_DATA' AS src
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
SELECT TRIM([LAST FIRST DOB]) AS raw,
    'SOURCE_PATIENT_DATA' AS src
FROM SOURCE_PATIENT_DATA
WHERE [LAST FIRST DOB] IS NOT NULL
    AND TRIM([LAST FIRST DOB]) <> ''
UNION ALL
SELECT TRIM([Pt Name]) AS raw,
    'SOURCE_COORDINATOR_TASKS_HISTORY' AS src
FROM SOURCE_COORDINATOR_TASKS_HISTORY
WHERE [Pt Name] IS NOT NULL
    AND TRIM([Pt Name]) <> ''
UNION ALL
SELECT TRIM([Patient Last, First DOB]) AS raw,
    'SOURCE_PROVIDER_TASKS_HISTORY' AS src
FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE [Patient Last, First DOB] IS NOT NULL
    AND TRIM([Patient Last, First DOB]) <> ''
UNION ALL
SELECT TRIM([Patient Last, First DOB.1]) AS raw,
    'SOURCE_PROVIDER_TASKS_HISTORY' AS src
FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE [Patient Last, First DOB.1] IS NOT NULL
    AND TRIM([Patient Last, First DOB.1]) <> '';
-- Normalize: strip known prefixes and short token prefixes followed by '-' or space
CREATE TEMP TABLE all_norm AS
SELECT raw,
    src,
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
-- Clean: filter rows that look like name + DOB (contain a slash and digits)
CREATE TEMP TABLE clean AS
SELECT norm,
    TRIM(
        REPLACE(
            REPLACE(
                REPLACE(REPLACE(norm, '\t', ' '), '\n', ' '),
                '\r',
                ' '
            ),
            '  ',
            ' '
        )
    ) AS name_dob,
    src
FROM all_norm
WHERE norm LIKE '%/%'
    AND norm GLOB '*[0-9]*'
    AND length(norm) > 6;
-- Count per source
SELECT src,
    COUNT(*) AS cnt
FROM clean
GROUP BY src
ORDER BY src;
-- Entries appearing in multiple sources (after normalization)
SELECT name_dob,
    COUNT(DISTINCT src) AS source_count,
    GROUP_CONCAT(DISTINCT src) AS sources
FROM clean
GROUP BY name_dob
HAVING COUNT(DISTINCT src) > 1
ORDER BY source_count DESC,
    name_dob
LIMIT 200;
-- Totals
SELECT COUNT(DISTINCT name_dob) AS unique_name_dob
FROM clean;
SELECT COUNT(*) AS total_rows
FROM clean;
-- Show some examples of normalized rows that had prefixes removed
SELECT all_norm.raw,
    clean.name_dob,
    all_norm.src AS raw_src
FROM all_norm
    JOIN clean USING (norm)
LIMIT 20;
-- Cleanup
DROP TABLE all_raw;
DROP TABLE all_norm;
DROP TABLE clean;
-- Helper function: simple regexp_replace implementation if not available
-- Note: Some SQLite builds may not have regexp_replace; above uses it for whitespace collapse. If not available, the query will still run without collapsing whitespace.