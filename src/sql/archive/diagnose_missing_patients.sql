-- Diagnostic query to find which patients are not transforming
-- This will show us exactly which records from SOURCE_PATIENT_DATA are not making it to the patients table
SELECT 'SOURCE_PATIENT_DATA Total Records:' as description,
    COUNT(*) as count
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
UNION ALL
SELECT 'Patients Table Records:' as description,
    COUNT(*) as count
FROM patients
UNION ALL
SELECT 'Missing Records (should be 0):' as description,
    (
        SELECT COUNT(*)
        FROM SOURCE_PATIENT_DATA spd
        WHERE spd."LAST FIRST DOB" IS NOT NULL
            AND spd."LAST FIRST DOB" != ''
            AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    ) - (
        SELECT COUNT(*)
        FROM patients
    ) as count
UNION ALL
SELECT 'Records with missing First Name:' as description,
    COUNT(*) as count
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND (
        TRIM(spd."First") IS NULL
        OR TRIM(spd."First") = ''
    )
UNION ALL
SELECT 'Records with missing Last Name:' as description,
    COUNT(*) as count
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND (
        TRIM(spd."Last") IS NULL
        OR TRIM(spd."Last") = ''
    )
UNION ALL
SELECT 'Records with missing DOB:' as description,
    COUNT(*) as count
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND spd."DOB" IS NULL;
-- Show the actual records that are being filtered out
SELECT '=== PROBLEMATIC RECORDS ===' as issue,
    '' as first_name,
    '' as last_name,
    '' as dob,
    '' as last_first_dob
UNION ALL
SELECT CASE
        WHEN TRIM(spd."First") IS NULL
        OR TRIM(spd."First") = '' THEN 'Missing First Name'
        WHEN TRIM(spd."Last") IS NULL
        OR TRIM(spd."Last") = '' THEN 'Missing Last Name'
        WHEN spd."DOB" IS NULL THEN 'Missing DOB'
        ELSE 'Other Issue'
    END as issue,
    COALESCE(TRIM(spd."First"), 'NULL') as first_name,
    COALESCE(TRIM(spd."Last"), 'NULL') as last_name,
    COALESCE(spd."DOB", 'NULL') as dob,
    spd."LAST FIRST DOB" as last_first_dob
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND (
        TRIM(spd."First") IS NULL
        OR TRIM(spd."First") = ''
        OR TRIM(spd."Last") IS NULL
        OR TRIM(spd."Last") = ''
        OR spd."DOB" IS NULL
    );