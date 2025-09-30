-- Test patient_id derivation from provider CSV import
SELECT 'patient_id' as column_test,
    COALESCE(
        p.patient_id,
        t."Patient Last, First DOB"
    ) as result,
    t."Patient Last, First DOB" as source_value
FROM TEST_PROVIDER_HEADER_SCHEMA_MAP t
    LEFT JOIN patients p ON TRIM(UPPER(t."Patient Last, First DOB")) = TRIM(UPPER(p.last_first_dob))
WHERE t."Patient Last, First DOB" IS NOT NULL
    AND t."Patient Last, First DOB" != ''
LIMIT 10;
-- Test provider_id derivation
SELECT 'provider_id' as column_test,
    COALESCE(scm.user_id, t."Prov") as user_id_result,
    t."Prov" as staff_source
FROM TEST_PROVIDER_HEADER_SCHEMA_MAP t
    LEFT JOIN staff_code_mapping scm ON t."Prov" = scm.staff_code
WHERE t."Prov" IS NOT NULL
    AND t."Prov" != ''
LIMIT 10;
-- Test task_date derivation
SELECT 'task_date' as column_test,
    t."DOS" as task_date_result,
    t."DOS" as source_value
FROM TEST_PROVIDER_HEADER_SCHEMA_MAP t
WHERE t."DOS" IS NOT NULL
    AND t."DOS" != ''
LIMIT 10;
-- Test minutes_of_service derivation
SELECT 'minutes_of_service' as column_test,
    t."Minutes" as minutes_of_service_result,
    t."Minutes" as source_value
FROM TEST_PROVIDER_HEADER_SCHEMA_MAP t
WHERE t."Minutes" IS NOT NULL
LIMIT 10;
-- Test task_description derivation
SELECT 'task_description' as column_test,
    t."Service" as task_description_result,
    t."Service" as source_value
FROM TEST_PROVIDER_HEADER_SCHEMA_MAP t
WHERE t."Service" IS NOT NULL
    AND t."Service" != ''
LIMIT 10;
-- Test notes derivation
SELECT 'notes' as column_test,
    t."Notes" as notes_result,
    t."Notes" as source_value
FROM TEST_PROVIDER_HEADER_SCHEMA_MAP t
WHERE t."Notes" IS NOT NULL
LIMIT 10;
-- Test billing_code derivation
SELECT 'billing_code' as column_test,
    t."Coding" as billing_code_result,
    t."Coding" as source_value
FROM TEST_PROVIDER_HEADER_SCHEMA_MAP t
WHERE t."Coding" IS NOT NULL
LIMIT 10;
-- Test billing_code_description derivation
-- No Billing Code Description column in this CSV, so skip this test.