-- Comprehensive Patient Transformation Test Script
-- Test all aspects of patient data transformation with LIMIT 10
-- Test 1: Basic patient data transformation (first 10 records)
SELECT 'Test 1: Basic Patient Data' as test_name,
    '' as separator
UNION ALL
SELECT 'Patient #' || ROW_NUMBER() OVER (
        ORDER BY spd."LAST FIRST DOB"
    ) as test_name,
    TRIM(spd."First") || ' ' || TRIM(spd."Last") || ' | DOB: ' || spd."DOB" || ' | Phone: ' || COALESCE(NULLIF(spd."Phone", 'zPhone'), 'N/A') || ' | Status: ' || COALESCE(NULLIF(spd."Pt Status", ''), 'Active') as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND TRIM(spd."First") IS NOT NULL
    AND TRIM(spd."Last") IS NOT NULL
    AND spd."DOB" IS NOT NULL
LIMIT 10
UNION ALL
-- Test 2: Address data quality (first 10 records)
SELECT '' as test_name,
    '' as separator
UNION ALL
SELECT 'Test 2: Address Data Quality' as test_name,
    '' as separator
UNION ALL
SELECT 'Address #' || ROW_NUMBER() OVER (
        ORDER BY spd."LAST FIRST DOB"
    ) as test_name,
    TRIM(spd."First") || ' ' || TRIM(spd."Last") || ' | Street: ' || COALESCE(
        NULLIF(NULLIF(spd."Street", ''), 'zStreet'),
        'N/A'
    ) || ' | City: ' || COALESCE(NULLIF(NULLIF(spd."City", ''), 'zCity'), 'N/A') || ' | State: ' || COALESCE(NULLIF(NULLIF(spd."State", ''), 'zState'), 'N/A') || ' | Zip: ' || COALESCE(NULLIF(NULLIF(spd."Zip", ''), 'zZip'), 'N/A') as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
LIMIT 10
UNION ALL
-- Test 3: Region and Facility mapping (first 10 records)
SELECT '' as test_name,
    '' as separator
UNION ALL
SELECT 'Test 3: Region & Facility Mapping' as test_name,
    '' as separator
UNION ALL
SELECT 'Region #' || ROW_NUMBER() OVER (
        ORDER BY spd."LAST FIRST DOB"
    ) as test_name,
    TRIM(spd."First") || ' ' || TRIM(spd."Last") || ' | Region: ' || COALESCE(
        NULLIF(NULLIF(spd."Region", ''), 'zRegion'),
        'N/A'
    ) || ' | Facility: ' || COALESCE(NULLIF(NULLIF(spd."Fac", ''), 'zFac'), 'N/A') || ' | Coordinator: ' || COALESCE(NULLIF(spd."Assigned CM", ''), 'N/A') as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
LIMIT 10
UNION ALL
-- Test 4: Insurance and Emergency Contact data (first 10 records)
SELECT '' as test_name,
    '' as separator
UNION ALL
SELECT 'Test 4: Insurance & Emergency Contact' as test_name,
    '' as separator
UNION ALL
SELECT 'Insurance #' || ROW_NUMBER() OVER (
        ORDER BY spd."LAST FIRST DOB"
    ) as test_name,
    TRIM(spd."First") || ' ' || TRIM(spd."Last") || ' | Insurance: ' || COALESCE(NULLIF(NULLIF(spd."Ins1", ''), 'zIns'), 'N/A') || ' | Policy: ' || COALESCE(
        NULLIF(NULLIF(spd."Policy", ''), 'zPolicy'),
        'N/A'
    ) || ' | Emergency Contact: ' || COALESCE(
        NULLIF(NULLIF(spd."Contact Name", ''), 'zContact'),
        'N/A'
    ) as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
LIMIT 10
UNION ALL
-- Test 5: Notes consolidation (first 10 records with notes)
SELECT '' as test_name,
    '' as separator
UNION ALL
SELECT 'Test 5: Notes Data Consolidation' as test_name,
    '' as separator
UNION ALL
SELECT 'Notes #' || ROW_NUMBER() OVER (
        ORDER BY spd."LAST FIRST DOB"
    ) as test_name,
    TRIM(spd."First") || ' ' || TRIM(spd."Last") || ' | Notes: ' || SUBSTR(
        TRIM(
            COALESCE(
                NULLIF(spd."List6 Notes", ''),
                NULLIF(spd."Prescreen Call Notes", ''),
                NULLIF(spd."Initial TV Notes", ''),
                NULLIF(spd."TV Note", ''),
                NULLIF(spd."eMed Records Routing Notes", ''),
                NULLIF(spd."Schedule HV 2w Notes", ''),
                'No notes available'
            )
        ),
        1,
        100
    ) || '...' as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND (
        (
            spd."List6 Notes" IS NOT NULL
            AND spd."List6 Notes" != ''
        )
        OR (
            spd."Prescreen Call Notes" IS NOT NULL
            AND spd."Prescreen Call Notes" != ''
        )
        OR (
            spd."Initial TV Notes" IS NOT NULL
            AND spd."Initial TV Notes" != ''
        )
        OR (
            spd."TV Note" IS NOT NULL
            AND spd."TV Note" != ''
        )
        OR (
            spd."eMed Records Routing Notes" IS NOT NULL
            AND spd."eMed Records Routing Notes" != ''
        )
        OR (
            spd."Schedule HV 2w Notes" IS NOT NULL
            AND spd."Schedule HV 2w Notes" != ''
        )
    )
LIMIT 10
UNION ALL
-- Test 6: Data quality summary
SELECT '' as test_name,
    '' as separator
UNION ALL
SELECT 'Test 6: Data Quality Summary' as test_name,
    '' as separator
UNION ALL
SELECT 'Total Records' as test_name,
    COUNT(*) || ' records found in SOURCE_PATIENT_DATA' as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
UNION ALL
SELECT 'Records with Phone' as test_name,
    COUNT(*) || ' records have valid phone numbers' as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."Phone" IS NOT NULL
    AND spd."Phone" != ''
    AND spd."Phone" != 'zPhone'
UNION ALL
SELECT 'Records with Address' as test_name,
    COUNT(*) || ' records have valid addresses' as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."Street" IS NOT NULL
    AND spd."Street" != ''
    AND spd."Street" != 'zStreet'
UNION ALL
SELECT 'Records with Region' as test_name,
    COUNT(*) || ' records have region assignments' as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."Region" IS NOT NULL
    AND spd."Region" != ''
    AND spd."Region" != 'zRegion'
UNION ALL
SELECT 'Records with Facility' as test_name,
    COUNT(*) || ' records have facility assignments' as separator
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."Fac" IS NOT NULL
    AND spd."Fac" != ''
    AND spd."Fac" != 'zFac';