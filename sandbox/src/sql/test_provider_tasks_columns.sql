-- Test provider_id derivation
SELECT 'provider_id' as column_test,
    COALESCE(p.provider_id, sp."Prov") as result,
    sp."Prov" as source_value
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
LEFT JOIN staff_code_mapping scm ON sp."Prov" = scm.staff_code
LEFT JOIN providers p ON scm.user_id = p.user_id
WHERE sp."Prov" IS NOT NULL AND sp."Prov" != ''
LIMIT 10;

-- Test patient_id derivation
SELECT 'patient_id' as column_test,
    COALESCE(p.patient_id, sp."Patient Last, First DOB") as result,
    sp."Patient Last, First DOB" as source_value
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
LEFT JOIN patients p ON TRIM(UPPER(sp."Patient Last, First DOB")) = TRIM(UPPER(p.last_first_dob))
WHERE sp."Patient Last, First DOB" IS NOT NULL AND sp."Patient Last, First DOB" != ''
LIMIT 10;

-- Test patient_name derivation
SELECT 'patient_name' as column_test,
    sp."Patient Last, First DOB" as result,
    sp."Patient Last, First DOB" as source_value
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
WHERE sp."Patient Last, First DOB" IS NOT NULL AND sp."Patient Last, First DOB" != ''
LIMIT 10;

-- Test provider_name derivation
SELECT 'provider_name' as column_test,
    COALESCE(u2.first_name || ' ' || u2.last_name, sp."Prov") as provider_name_result,
    sp."Prov" as staff_source
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
LEFT JOIN staff_code_mapping scm ON sp."Prov" = scm.staff_code
LEFT JOIN providers p ON scm.user_id = p.user_id
LEFT JOIN users u ON scm.user_id = u.user_id
LEFT JOIN users u2 ON p.user_id = u2.user_id
WHERE sp."Prov" IS NOT NULL AND sp."Prov" != ''
LIMIT 10;

-- Test user_id derivation
SELECT 'user_id' as column_test,
    COALESCE(scm.user_id, sp."Prov") as user_id_result,
    sp."Prov" as staff_source
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
LEFT JOIN staff_code_mapping scm ON sp."Prov" = scm.staff_code
WHERE sp."Prov" IS NOT NULL AND sp."Prov" != ''
LIMIT 10;

-- Test task_date derivation
SELECT 'task_date' as column_test,
    sp.DOS as task_date_result,
    sp.DOS as source_value
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
WHERE sp.DOS IS NOT NULL AND sp.DOS != ''
LIMIT 10;

-- Test minutes_of_service derivation
SELECT 'minutes_of_service' as column_test,
    CAST(sp.Minutes AS INTEGER) as minutes_result,
    sp.Minutes as source_value
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
WHERE sp.Minutes IS NOT NULL
LIMIT 10;

-- Test status derivation
SELECT 'status' as column_test,
    'completed' as status_result,
    'completed' as source_value
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
LIMIT 10;

-- Test notes derivation
SELECT 'notes' as column_test,
    COALESCE(sp."EHR Chief Complaint" || ' ' || sp."EHR Assessment Dx", sp."EHR Chief Complaint", sp."EHR Assessment Dx") as notes_result,
    sp."EHR Chief Complaint" as chief_complaint_source,
    sp."EHR Assessment Dx" as assessment_dx_source
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
WHERE sp."EHR Chief Complaint" IS NOT NULL OR sp."EHR Assessment Dx" IS NOT NULL
LIMIT 10;

-- Test billing_code_id derivation
SELECT 'billing_code_id' as column_test,
    bc.code_id as billing_code_id_result,
    sp.Coding as coding_source,
    bc.billing_code as matched_billing_code
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
LEFT JOIN task_billing_codes bc ON sp.Coding = bc.billing_code
WHERE sp.Coding IS NOT NULL AND sp.Coding != ''
LIMIT 10;

-- Test month and year derivation from task_date
SELECT 'month_year' as column_test,
    CAST(SUBSTR(sp.DOS, 1, INSTR(sp.DOS, '/') - 1) AS INTEGER) as month_result,
    CAST('20' || SUBSTR(sp.DOS, -2) AS INTEGER) as year_result,
    sp.DOS as source_value
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
WHERE sp.DOS IS NOT NULL AND sp.DOS != ''
LIMIT 10;

-- Test billing_code and billing_code_description derivation
SELECT 'billing_codes' as column_test,
    COALESCE(sp.Coding, 'Unknown') as billing_code,
    COALESCE(bc.description, 'Unknown') as billing_code_description,
    sp.Coding as coding_source
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sp
LEFT JOIN task_billing_codes bc ON sp.Coding = bc.billing_code
WHERE sp.Coding IS NOT NULL AND sp.Coding != ''
LIMIT 10;
