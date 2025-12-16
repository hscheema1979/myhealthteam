r-- Test provider_id derivation in monthly summary
SELECT 'provider_id' as test_type,
    pms.provider_id,
    pt.provider_id as source_provider_id
FROM provider_monthly_summary pms
JOIN provider_tasks pt ON pms.provider_id = pt.provider_id
LIMIT 10;

-- Test provider_name derivation in monthly summary
SELECT 'provider_name' as test_type,
    pms.provider_name,
    (u.first_name || ' ' || u.last_name) as expected_name
FROM provider_monthly_summary pms
JOIN providers p ON pms.provider_id = p.provider_id
JOIN users u ON p.user_id = u.user_id
LIMIT 10;

-- Test month derivation in monthly summary
SELECT 'month' as test_type,
    pms.month,
    CAST(SUBSTR(pt.task_date, 1, INSTR(pt.task_date, '/') - 1) AS INTEGER) as source_month
FROM provider_monthly_summary pms
JOIN provider_tasks pt ON pms.provider_id = pt.provider_id 
    AND pms.month = CAST(SUBSTR(pt.task_date, 1, INSTR(pt.task_date, '/') - 1) AS INTEGER)
    AND pms.year = CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER)
LIMIT 10;

-- Test year derivation in monthly summary
SELECT 'year' as test_type,
    pms.year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as source_year
FROM provider_monthly_summary pms
JOIN provider_tasks pt ON pms.provider_id = pt.provider_id 
    AND pms.month = CAST(SUBSTR(pt.task_date, 1, INSTR(pt.task_date, '/') - 1) AS INTEGER)
    AND pms.year = CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER)
LIMIT 10;

-- Test total_tasks_completed derivation in monthly summary
SELECT 'total_tasks_completed' as test_type,
    pms.total_tasks_completed,
    COUNT(pt.provider_task_id) as calculated_count
FROM provider_monthly_summary pms
JOIN provider_tasks pt ON pms.provider_id = pt.provider_id 
    AND pms.month = CAST(SUBSTR(pt.task_date, 1, INSTR(pt.task_date, '/') - 1) AS INTEGER)
    AND pms.year = CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER)
GROUP BY pms.summary_id, pms.total_tasks_completed
LIMIT 10;

-- Test total_time_spent_minutes derivation in monthly summary
SELECT 'total_time_spent_minutes' as test_type,
    pms.total_time_spent_minutes,
    SUM(pt.minutes_of_service) as calculated_minutes
FROM provider_monthly_summary pms
JOIN provider_tasks pt ON pms.provider_id = pt.provider_id 
    AND pms.month = CAST(SUBSTR(pt.task_date, 1, INSTR(pt.task_date, '/') - 1) AS INTEGER)
    AND pms.year = CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER)
GROUP BY pms.summary_id, pms.total_time_spent_minutes
LIMIT 10;
