-- Test patient_id derivation
SELECT 'patient_id' as column_test, 
    COALESCE(p.patient_id, sch."Pt Name") as result,
    sch."Pt Name" as source_value
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
LEFT JOIN patients p ON TRIM(UPPER(sch."Pt Name")) = TRIM(UPPER(p.last_first_dob))
WHERE sch."Pt Name" IS NOT NULL AND sch."Pt Name" != ''
LIMIT 10;

-- Test patient_name derivation
SELECT 'patient_name' as column_test, 
    sch."Pt Name" as result,
    sch."Pt Name" as source_value
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
WHERE sch."Pt Name" IS NOT NULL AND sch."Pt Name" != ''
LIMIT 10;

-- Test coordinator_id and user_id derivation
SELECT 'coordinator_id_user_id' as column_test,
    COALESCE(scm.user_id, sch."Staff") as user_id_result,
    COALESCE(c.coordinator_id, sch."Staff") as coordinator_id_result,
    sch."Staff" as staff_source
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
LEFT JOIN staff_code_mapping scm ON sch."Staff" = scm.staff_code
LEFT JOIN coordinators c ON scm.user_id = c.user_id
WHERE sch."Staff" IS NOT NULL AND sch."Staff" != ''
LIMIT 10;

-- Test coordinator_name derivation
SELECT 'coordinator_name' as column_test,
    COALESCE(u.first_name || ' ' || u.last_name, sch."Staff") as coordinator_name_result,
    sch."Staff" as staff_source
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
LEFT JOIN staff_code_mapping scm ON sch."Staff" = scm.staff_code
LEFT JOIN users u ON scm.user_id = u.user_id
WHERE sch."Staff" IS NOT NULL AND sch."Staff" != ''
LIMIT 10;

-- Test task_date derivation
SELECT 'task_date' as column_test,
    sch."Date Only" as task_date_result,
    sch."Date Only" as source_value
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
WHERE sch."Date Only" IS NOT NULL AND sch."Date Only" != ''
LIMIT 10;

-- Test duration_minutes derivation
SELECT 'duration_minutes' as column_test,
    sch."Mins B" as duration_minutes_result,
    sch."Mins B" as source_value
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
WHERE sch."Mins B" IS NOT NULL
LIMIT 10;

-- Test task_type derivation
SELECT 'task_type' as column_test,
    sch."Type" as task_type_result,
    sch."Type" as source_value
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
WHERE sch."Type" IS NOT NULL AND sch."Type" != ''
LIMIT 10;

-- Test notes derivation
SELECT 'notes' as column_test,
    sch."Notes" as notes_result,
    sch."Notes" as source_value
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
WHERE sch."Notes" IS NOT NULL
LIMIT 10;
