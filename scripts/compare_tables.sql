-- Compare names and DOBs across the three source tables
-- This script will extract and compare data directly in SQLite
-- First, create temporary tables for each source with normalized data
-- SOURCE_PATIENT_DATA: Use Last, First, DOB if available, otherwise use LAST FIRST DOB
CREATE TEMP TABLE patient_data AS
SELECT TRIM(COALESCE(Last, '')) || ' ' || TRIM(COALESCE(First, '')) || ' ' || TRIM(COALESCE(DOB, '')) AS name_dob,
    'SOURCE_PATIENT_DATA' AS source
FROM SOURCE_PATIENT_DATA
WHERE (
        Last IS NOT NULL
        OR First IS NOT NULL
        OR DOB IS NOT NULL
    )
    AND TRIM(COALESCE(Last, '')) || ' ' || TRIM(COALESCE(First, '')) || ' ' || TRIM(COALESCE(DOB, '')) != ' '
UNION ALL
SELECT TRIM([LAST FIRST DOB]) AS name_dob,
    'SOURCE_PATIENT_DATA' AS source
FROM SOURCE_PATIENT_DATA
WHERE [LAST FIRST DOB] IS NOT NULL
    AND TRIM([LAST FIRST DOB]) != ''
    AND (
        Last IS NULL
        AND First IS NULL
        AND DOB IS NULL
    );
-- SOURCE_COORDINATOR_TASKS_HISTORY: Use Pt Name
CREATE TEMP TABLE coordinator_data AS
SELECT TRIM([Pt Name]) AS name_dob,
    'SOURCE_COORDINATOR_TASKS_HISTORY' AS source
FROM SOURCE_COORDINATOR_TASKS_HISTORY
WHERE [Pt Name] IS NOT NULL
    AND TRIM([Pt Name]) != '';
-- SOURCE_PROVIDER_TASKS_HISTORY: Use Patient Last, First DOB
CREATE TEMP TABLE provider_data AS
SELECT TRIM([Patient Last, First DOB]) AS name_dob,
    'SOURCE_PROVIDER_TASKS_HISTORY' AS source
FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE [Patient Last, First DOB] IS NOT NULL
    AND TRIM([Patient Last, First DOB]) != ''
UNION ALL
SELECT TRIM([Patient Last, First DOB.1]) AS name_dob,
    'SOURCE_PROVIDER_TASKS_HISTORY' AS source
FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE [Patient Last, First DOB.1] IS NOT NULL
    AND TRIM([Patient Last, First DOB.1]) != '';
-- Create a combined view with all data
CREATE TEMP TABLE all_data AS
SELECT name_dob,
    source
FROM patient_data
UNION ALL
SELECT name_dob,
    source
FROM coordinator_data
UNION ALL
SELECT name_dob,
    source
FROM provider_data;
-- Create a view with only clean name+DOB entries (filtering out noise)
CREATE TEMP TABLE clean_data AS
SELECT name_dob,
    source
FROM all_data
WHERE name_dob NOT LIKE '%televisit%'
    AND name_dob NOT LIKE '%tele%'
    AND name_dob NOT LIKE '%appt%'
    AND name_dob NOT LIKE '%appointment%'
    AND name_dob NOT LIKE '%intake%'
    AND name_dob NOT LIKE '%no answer%'
    AND name_dob NOT LIKE '%no answe%'
    AND name_dob NOT LIKE '%scheduled%'
    AND name_dob NOT LIKE '%confirmed%'
    AND name_dob NOT LIKE '%cm%'
    AND name_dob NOT LIKE '%pcp/%'
    AND name_dob NOT LIKE '%admit date%'
    AND name_dob NOT LIKE '%dob:%'
    AND name_dob NOT LIKE '%hospitalized%'
    AND name_dob NOT LIKE '%facility%'
    AND name_dob NOT LIKE '%address%'
    AND name_dob NOT LIKE '%phone%'
    AND name_dob NOT LIKE '%medicare%'
    AND name_dob NOT LIKE '%rp:%'
    AND name_dob NOT LIKE '%rp%'
    AND name_dob NOT LIKE '%rescheduled%'
    AND name_dob NOT LIKE '%homevisit%'
    AND name_dob NOT LIKE '%home visit%'
    AND name_dob NOT LIKE '%lab%'
    AND name_dob NOT LIKE '%labs%'
    AND name_dob NOT LIKE '%called%'
    AND name_dob NOT LIKE '%call%'
    AND name_dob NOT LIKE '%message%'
    AND name_dob NOT LIKE '%text%'
    AND name_dob NOT LIKE '%notified%'
    AND name_dob NOT LIKE '%patient passed%'
    AND name_dob NOT LIKE '%superadmin%'
    AND name_dob NOT LIKE '%onboarding%'
    AND name_dob NOT LIKE '%mayra%'
    AND name_dob NOT LIKE '%no-show%'
    AND name_dob NOT LIKE '%no show%'
    AND name_dob NOT LIKE '%cancel%'
    AND name_dob NOT LIKE '%cancelled%'
    AND name_dob NOT LIKE '%lvm%'
    AND LENGTH(name_dob) >= 4
    AND name_dob REGEXP '[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}'
    AND name_dob REGEXP '[A-Za-z]';
-- Count total entries per source
SELECT source,
    COUNT(*) as count
FROM clean_data
GROUP BY source
ORDER BY source;
-- Find entries that appear in multiple sources
SELECT name_dob,
    COUNT(*) as source_count,
    GROUP_CONCAT(DISTINCT source) as sources
FROM clean_data
GROUP BY name_dob
HAVING COUNT(*) > 1
ORDER BY source_count DESC,
    name_dob;
-- Show top 20 most common entries across all sources
SELECT name_dob,
    COUNT(*) as frequency
FROM clean_data
GROUP BY name_dob
ORDER BY frequency DESC
LIMIT 20;
-- Show entries unique to each source
SELECT 'SOURCE_PATIENT_DATA' as source,
    name_dob
FROM clean_data
WHERE source = 'SOURCE_PATIENT_DATA'
    AND name_dob NOT IN (
        SELECT name_dob
        FROM clean_data
        WHERE source != 'SOURCE_PATIENT_DATA'
    )
LIMIT 10;
SELECT 'SOURCE_COORDINATOR_TASKS_HISTORY' as source,
    name_dob
FROM clean_data
WHERE source = 'SOURCE_COORDINATOR_TASKS_HISTORY'
    AND name_dob NOT IN (
        SELECT name_dob
        FROM clean_data
        WHERE source != 'SOURCE_COORDINATOR_TASKS_HISTORY'
    )
LIMIT 10;
SELECT 'SOURCE_PROVIDER_TASKS_HISTORY' as source,
    name_dob
FROM clean_data
WHERE source = 'SOURCE_PROVIDER_TASKS_HISTORY'
    AND name_dob NOT IN (
        SELECT name_dob
        FROM clean_data
        WHERE source != 'SOURCE_PROVIDER_TASKS_HISTORY'
    )
LIMIT 10;
-- Show total unique entries across all sources
SELECT COUNT(DISTINCT name_dob) as total_unique_entries
FROM clean_data;
-- Show total entries after filtering
SELECT COUNT(*) as total_filtered_entries
FROM clean_data;
-- Drop temporary tables
DROP TABLE patient_data;
DROP TABLE coordinator_data;
DROP TABLE provider_data;
DROP TABLE all_data;
DROP TABLE clean_data;