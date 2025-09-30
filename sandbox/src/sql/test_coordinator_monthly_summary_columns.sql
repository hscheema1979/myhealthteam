-- Test coordinator_id derivation
SELECT 'coordinator_id' as column_test,
    ct.coordinator_id as result,
    ct.coordinator_id as source_value
FROM coordinator_tasks ct
WHERE ct.coordinator_id IS NOT NULL
LIMIT 10;

-- Test coordinator_name derivation
SELECT 'coordinator_name' as column_test,
    COALESCE(u.first_name || ' ' || u.last_name, ct.coordinator_id) as coordinator_name_result,
    ct.coordinator_id as source_value
FROM coordinator_tasks ct
LEFT JOIN coordinators c ON ct.coordinator_id = c.coordinator_id
LEFT JOIN users u ON c.user_id = u.user_id
WHERE ct.coordinator_id IS NOT NULL
LIMIT 10;

-- Test patient_id derivation
SELECT 'patient_id' as column_test,
    ct.patient_id as result,
    ct.patient_id as source_value
FROM coordinator_tasks ct
WHERE ct.patient_id IS NOT NULL
LIMIT 10;

-- Test patient_name derivation
SELECT 'patient_name' as column_test,
    COALESCE(p.first_name || ' ' || p.last_name, ct.patient_id) as patient_name_result,
    ct.patient_id as source_value
FROM coordinator_tasks ct
LEFT JOIN patients p ON ct.patient_id = p.patient_id
WHERE ct.patient_id IS NOT NULL
LIMIT 10;

-- Test year and month derivation
SELECT 'year_month' as column_test,
    CAST(SUBSTR(ct.task_date, -2) AS INTEGER) + 2000 as year_result,
    CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER) as month_result,
    ct.task_date as source_value
FROM coordinator_tasks ct
WHERE ct.task_date IS NOT NULL AND ct.task_date != ''
LIMIT 10;

-- Test total_minutes derivation
SELECT 'total_minutes' as column_test,
    SUM(ct.duration_minutes) as total_minutes_result,
    ct.coordinator_id as coordinator_id,
    ct.patient_id as patient_id,
    CAST(SUBSTR(ct.task_date, -2) AS INTEGER) + 2000 as year,
    CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER) as month
FROM coordinator_tasks ct
WHERE ct.task_date IS NOT NULL AND ct.task_date != ''
    AND ct.coordinator_id IS NOT NULL
    AND ct.patient_id IS NOT NULL
    AND ct.duration_minutes IS NOT NULL
GROUP BY ct.coordinator_id, ct.patient_id, 
         CAST(SUBSTR(ct.task_date, -2) AS INTEGER) + 2000,
         CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER)
LIMIT 10;

-- Test billing_code_id, billing_code, and billing_code_description derivation
SELECT 'billing_codes' as column_test,
    bc.code_id as billing_code_id,
    bc.billing_code,
    bc.description as billing_code_description,
    time_summary.total_minutes
FROM (
    SELECT 
        ct.coordinator_id,
        ct.patient_id,
        CAST(SUBSTR(ct.task_date, -2) AS INTEGER) + 2000 as year,
        CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER) as month,
        SUM(ct.duration_minutes) as total_minutes
    FROM coordinator_tasks ct
    WHERE ct.task_date IS NOT NULL AND ct.task_date != ''
        AND ct.coordinator_id IS NOT NULL
        AND ct.patient_id IS NOT NULL
        AND ct.duration_minutes IS NOT NULL
    GROUP BY ct.coordinator_id, ct.patient_id, 
             CAST(SUBSTR(ct.task_date, -2) AS INTEGER) + 2000,
             CAST(SUBSTR(ct.task_date, 1, INSTR(ct.task_date, '/') - 1) AS INTEGER)
) time_summary
LEFT JOIN coordinator_billing_codes bc ON time_summary.total_minutes >= bc.min_minutes 
    AND time_summary.total_minutes <= bc.max_minutes
LIMIT 10;
