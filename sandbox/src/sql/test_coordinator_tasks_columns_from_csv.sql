-- Test patient_id derivation from CSV import
SELECT 'patient_id' as column_test,
    COALESCE(
        p.patient_id,
        t."Pt Name"
    ) as result,
    t."Pt Name" as source_value
FROM TEST_HEADER_SCHEMA_MAP t
    LEFT JOIN patients p ON TRIM(UPPER(t."Pt Name")) = TRIM(UPPER(p.last_first_dob))
WHERE t."Pt Name" IS NOT NULL
    AND t."Pt Name" != ''
LIMIT 10;
-- Test patient_name derivation
SELECT 'patient_name' as column_test,
    t."Pt Name" as result,
    t."Pt Name" as source_value
FROM TEST_HEADER_SCHEMA_MAP t
WHERE t."Pt Name" IS NOT NULL
    AND t."Pt Name" != ''
LIMIT 10;
-- Test coordinator_id and user_id derivation
SELECT 'coordinator_id_user_id' as column_test,
    COALESCE(scm.user_id, t."Staff") as user_id_result,
    t."Staff" as staff_source
FROM TEST_HEADER_SCHEMA_MAP t
    LEFT JOIN staff_code_mapping scm ON t."Staff" = scm.staff_code
WHERE t."Staff" IS NOT NULL
    AND t."Staff" != ''
LIMIT 10;
-- Test task_date derivation
SELECT 'task_date' as column_test,
    t."Date Only" as task_date_result,
    t."Date Only" as source_value
FROM TEST_HEADER_SCHEMA_MAP t
WHERE t."Date Only" IS NOT NULL
    AND t."Date Only" != ''
LIMIT 10;
-- Test duration_minutes derivation
SELECT 'duration_minutes' as column_test,
    t."Total Mins" as duration_minutes_result,
    t."Total Mins" as source_value
FROM TEST_HEADER_SCHEMA_MAP t
WHERE t."Total Mins" IS NOT NULL
LIMIT 10;
-- Test task_type derivation
SELECT 'task_type' as column_test,
    t."Type" as task_type_result,
    t."Type" as source_value
FROM TEST_HEADER_SCHEMA_MAP t
WHERE t."Type" IS NOT NULL
    AND t."Type" != ''
LIMIT 10;
-- Test notes derivation
SELECT 'notes' as column_test,
    t."Notes" as notes_result,
    t."Notes" as source_value
FROM TEST_HEADER_SCHEMA_MAP t
WHERE t."Notes" IS NOT NULL
LIMIT 10;