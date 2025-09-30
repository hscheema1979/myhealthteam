-- Clear existing data
DELETE FROM coordinator_monthly_summary;

-- Insert data with proper derivations using subquery to handle aggregation
INSERT INTO coordinator_monthly_summary (
    coordinator_id,
    coordinator_name,
    patient_id,
    patient_name,
    year,
    month,
    total_minutes,
    billing_code_id,
    billing_code,
    billing_code_description
)
SELECT 
    time_summary.coordinator_id,
    COALESCE(u.first_name || ' ' || u.last_name, time_summary.coordinator_id) as coordinator_name,
    time_summary.patient_id,
    COALESCE(p.first_name || ' ' || p.last_name, time_summary.patient_id) as patient_name,
    time_summary.year,
    time_summary.month,
    time_summary.total_minutes,
    bc.code_id as billing_code_id,
    bc.billing_code,
    bc.description as billing_code_description
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
LEFT JOIN coordinators c ON time_summary.coordinator_id = c.coordinator_id
LEFT JOIN users u ON c.user_id = u.user_id
LEFT JOIN patients p ON time_summary.patient_id = p.patient_id
LEFT JOIN coordinator_billing_codes bc ON time_summary.total_minutes >= bc.min_minutes 
    AND time_summary.total_minutes <= bc.max_minutes;
