-- Populate coordinator minutes summary for September 2025
-- This creates the total minutes pivot table per coordinator
DELETE FROM coordinator_minutes_2025_09;
INSERT INTO coordinator_minutes_2025_09 (
        coordinator_id,
        coordinator_name,
        year,
        month,
        total_minutes,
        billing_code,
        billing_code_description
    )
SELECT ct.coordinator_id,
    COALESCE(u.first_name || ' ' || u.last_name, 'Unknown') as coordinator_name,
    2025 as year,
    9 as month,
    SUM(ct.duration_minutes) as total_minutes,
    CASE
        WHEN SUM(ct.duration_minutes) <= 120 THEN 'T1016'
        WHEN SUM(ct.duration_minutes) <= 240 THEN 'T1016-HM'
        ELSE 'T1016-HC'
    END as billing_code,
    CASE
        WHEN SUM(ct.duration_minutes) <= 120 THEN 'Case management, each 15 min'
        WHEN SUM(ct.duration_minutes) <= 240 THEN 'Case management, moderate complexity'
        ELSE 'Case management, high complexity'
    END as billing_code_description
FROM coordinator_tasks_2025_09 ct
    LEFT JOIN coordinators c ON ct.coordinator_id = c.coordinator_id
    LEFT JOIN users u ON c.user_id = u.user_id
WHERE ct.duration_minutes IS NOT NULL
GROUP BY ct.coordinator_id
ORDER BY ct.coordinator_id;