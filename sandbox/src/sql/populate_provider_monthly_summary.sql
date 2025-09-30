-- Clear existing data from provider_monthly_summary table
DELETE FROM provider_monthly_summary;
-- Insert data into provider_monthly_summary table from provider_tasks
INSERT INTO provider_monthly_summary (
        provider_id,
        provider_name,
        month,
        year,
        total_tasks_completed,
        total_time_spent_minutes
    )
SELECT pt.provider_id,
    pt.provider_name,
    CAST(
        SUBSTR(pt.task_date, 1, INSTR(pt.task_date, '/') - 1) AS INTEGER
    ) AS month,
    CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) AS year,
    COUNT(pt.provider_task_id) AS total_tasks_completed,
    SUM(pt.minutes_of_service) AS total_time_spent_minutes
FROM provider_tasks pt
WHERE pt.task_date IS NOT NULL
    AND pt.task_date != ''
    AND LENGTH(pt.task_date) = 8
    AND SUBSTR(pt.task_date, 3, 1) = '/'
    AND SUBSTR(pt.task_date, 6, 1) = '/'
    AND CAST('20' || SUBSTR(pt.task_date, -2) AS INTEGER) >= 2023
GROUP BY pt.provider_id,
    month,
    year;
-- Sample info
SELECT *
FROM provider_monthly_summary
LIMIT 5;