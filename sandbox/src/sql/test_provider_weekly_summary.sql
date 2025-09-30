-- Test provider_id derivation from provider_tasks
-- Create temporary table for weekly summary data
DROP TABLE IF EXISTS temp_weekly_summary;
CREATE TEMPORARY TABLE temp_weekly_summary AS
SELECT 
    pt.provider_id,
    pt.provider_name,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    COUNT(pt.provider_task_id) as total_tasks_completed,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) as average_daily_minutes,
    COUNT(DISTINCT pt.task_date) as days_active
FROM provider_tasks pt
WHERE pt.task_date LIKE '%25'
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1;

-- Debug: Check the data in the temporary table
SELECT 'temp_weekly_summary' as table_name, COUNT(*) as row_count FROM temp_weekly_summary;

-- Display sample data from the temporary table
SELECT * FROM temp_weekly_summary LIMIT 5;
SELECT 'provider_id' as test_type,
    pt.provider_id,
    pt.provider_id as source_provider_id
FROM provider_tasks pt
LIMIT 10;

-- Test provider_name derivation from users via providers
SELECT 'provider_name' as test_type,
    (u.first_name || ' ' || u.last_name) as derived_provider_name,
    pt.provider_name as stored_provider_name,
    pt.provider_id as provider_id
FROM provider_tasks pt
JOIN providers p ON pt.provider_id = p.provider_id
JOIN users u ON p.user_id = u.user_id
LIMIT 10;

-- Test year derivation from task_date
SELECT 'year' as test_type,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    pt.task_date as source_task_date
FROM provider_tasks pt
WHERE pt.task_date IS NOT NULL AND pt.task_date != ''
LIMIT 10;

-- Test week_number derivation from task_date
SELECT 'week_number' as test_type,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    pt.task_date as source_task_date
FROM provider_tasks pt
WHERE pt.task_date IS NOT NULL AND pt.task_date != ''
LIMIT 10;

-- Test total_tasks_completed derivation (count of tasks per provider per week, weekdays only)
SELECT 'total_tasks_completed' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    COUNT(pt.provider_task_id) as total_tasks_completed
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;

-- Test total_time_spent_minutes derivation (sum of minutes_of_service per provider per week, weekdays only)
SELECT 'total_time_spent_minutes' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    SUM(pt.minutes_of_service) as total_time_spent_minutes
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;

-- Test average_daily_minutes derivation (average minutes spent per day, weekdays only)
SELECT 'average_daily_minutes' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT CASE WHEN CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4 THEN pt.task_date END) as average_daily_minutes
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;

-- Test days_active derivation (number of weekdays with tasks completed)
SELECT 'days_active' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    COUNT(DISTINCT pt.task_date) as days_active
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
-- Display sample data from the temporary table
WHERE pt.task_date LIKE '%25'
FROM provider_tasks pt
    COUNT(DISTINCT pt.task_date) as days_active
    COUNT(DISTINCT pt.task_date) as days_active
    COUNT(DISTINCT pt.task_date) as days_active
    COUNT(DISTINCT pt.task_date) as days_active
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) as average_daily_minutes,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) as average_daily_minutes,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) as average_daily_minutes,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) as average_daily_minutes,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) as average_daily_minutes,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) as average_daily_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    COUNT(pt.provider_task_id) as total_tasks_completed,
    COUNT(pt.provider_task_id) as total_tasks_completed,
    COUNT(pt.provider_task_id) as total_tasks_completed,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0') as week_end_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    DATE(MIN(pt.task_date), 'weekday 0', '-6 days') as week_start_date,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_name,
    pt.provider_id,
SELECT 
SELECT 
SELECT 
SELECT 
    pt.provider_id,
    pt.provider_id as source_provider_id
FROM provider_tasks pt
LIMIT 10;

-- Test provider_name derivation from users via providers
SELECT 'provider_name' as test_type,
    (u.first_name || ' ' || u.last_name) as derived_provider_name,
    pt.provider_name as stored_provider_name,
    pt.provider_id as provider_id
FROM provider_tasks pt
JOIN providers p ON pt.provider_id = p.provider_id
JOIN users u ON p.user_id = u.user_id
LIMIT 10;

-- Test year derivation from task_date
SELECT 'year' as test_type,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    pt.task_date as source_task_date
FROM provider_tasks pt
WHERE pt.task_date IS NOT NULL AND pt.task_date != ''
LIMIT 10;

-- Test week_number derivation from task_date
SELECT 'week_number' as test_type,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    pt.task_date as source_task_date
FROM provider_tasks pt
WHERE pt.task_date IS NOT NULL AND pt.task_date != ''
LIMIT 10;

-- Test total_tasks_completed derivation (count of tasks per provider per week, weekdays only)
SELECT 'total_tasks_completed' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    COUNT(pt.provider_task_id) as total_tasks_completed
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;

-- Test total_time_spent_minutes derivation (sum of minutes_of_service per provider per week, weekdays only)
SELECT 'total_time_spent_minutes' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    SUM(pt.minutes_of_service) as total_time_spent_minutes
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;

-- Test average_daily_minutes derivation (average minutes spent per day, weekdays only)
SELECT 'average_daily_minutes' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT CASE WHEN CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4 THEN pt.task_date END) as average_daily_minutes
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;

-- Test days_active derivation (number of weekdays with tasks completed)
SELECT 'days_active' as test_type,
    pt.provider_id,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) as year,
    CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1 as week_number,
    COUNT(DISTINCT pt.task_date) as days_active
FROM provider_tasks pt
WHERE CAST((julianday(pt.task_date) + 3) % 7 AS INTEGER) BETWEEN 0 AND 4  -- Monday(0) to Friday(4)
GROUP BY pt.provider_id, 
         CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER),
         CAST((julianday(pt.task_date) - julianday('20' || SUBSTR(pt.task_date, -2) || '-01-01') + 1) / 7 AS INTEGER) + 1
LIMIT 10;
