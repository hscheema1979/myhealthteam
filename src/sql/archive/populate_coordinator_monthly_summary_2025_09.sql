-- Populate coordinator monthly summary for September 2025
-- This creates the patient minutes pivot table per coordinator
DELETE FROM coordinator_monthly_summary_2025_09;
INSERT INTO coordinator_monthly_summary_2025_09 (
        coordinator_id,
        coordinator_name,
        patient_id,
        patient_name,
        year,
        month,
        total_minutes,
        billing_code,
        billing_code_description
    )
SELECT ct.coordinator_id,
    COALESCE(u.first_name || ' ' || u.last_name, 'Unknown') as coordinator_name,
    ct.patient_id,
    COALESCE(
        p.first_name || ' ' || p.last_name,
        ct.patient_id
    ) as patient_name,
    2025 as year,
    9 as month,
    SUM(ct.duration_minutes) as total_minutes,
    CASE
        WHEN SUM(ct.duration_minutes) <= 15 THEN '99211'
        WHEN SUM(ct.duration_minutes) <= 30 THEN '99212'
        WHEN SUM(ct.duration_minutes) <= 45 THEN '99213'
        WHEN SUM(ct.duration_minutes) <= 60 THEN '99214'
        ELSE '99215'
    END as billing_code,
    CASE
        WHEN SUM(ct.duration_minutes) <= 15 THEN 'Office/outpatient visit, minimal'
        WHEN SUM(ct.duration_minutes) <= 30 THEN 'Office/outpatient visit, straightforward'
        WHEN SUM(ct.duration_minutes) <= 45 THEN 'Office/outpatient visit, low complexity'
        WHEN SUM(ct.duration_minutes) <= 60 THEN 'Office/outpatient visit, moderate complexity'
        ELSE 'Office/outpatient visit, comprehensive'
    END as billing_code_description
FROM coordinator_tasks_2025_09 ct
    LEFT JOIN coordinators c ON ct.coordinator_id = c.coordinator_id
    LEFT JOIN users u ON c.user_id = u.user_id
    LEFT JOIN patients p ON ct.patient_id = p.patient_id
WHERE ct.duration_minutes IS NOT NULL
GROUP BY ct.coordinator_id,
    ct.patient_id
ORDER BY ct.coordinator_id,
    ct.patient_id;