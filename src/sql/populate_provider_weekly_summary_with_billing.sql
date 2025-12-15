-- Populate provider_weekly_summary_with_billing from monthly partitioned tables
-- This script aggregates data from provider_tasks_YYYY_MM tables
DELETE FROM provider_weekly_summary_with_billing;
CREATE TABLE IF NOT EXISTS provider_weekly_summary_with_billing (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    status TEXT DEFAULT 'PENDING',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    paid BOOLEAN DEFAULT FALSE
);
-- Insert aggregated data from all provider_tasks_YYYY_MM tables
INSERT INTO provider_weekly_summary_with_billing (
        provider_id,
        provider_name,
        week_start_date,
        week_end_date,
        year,
        week_number,
        total_tasks_completed,
        total_time_spent_minutes,
        billing_code,
        billing_code_description,
        status
    )
SELECT pt.provider_id,
    u.full_name AS provider_name,
    DATE(
        pt.task_date,
        '-' || ((strftime('%w', pt.task_date) + 6) % 7) || ' days'
    ) AS week_start_date,
    DATE(
        pt.task_date,
        '+' || (6 - ((strftime('%w', pt.task_date) + 6) % 7)) || ' days'
    ) AS week_end_date,
    CAST(strftime('%Y', pt.task_date) AS INTEGER) AS year,
    CAST(strftime('%W', pt.task_date) AS INTEGER) + 1 AS week_number,
    COUNT(pt.provider_task_id) AS total_tasks_completed,
    SUM(pt.minutes_of_service) AS total_time_spent_minutes,
    CASE
        WHEN SUM(pt.minutes_of_service) <= 30 THEN '99201'
        WHEN SUM(pt.minutes_of_service) <= 45 THEN '99202'
        WHEN SUM(pt.minutes_of_service) <= 60 THEN '99203'
        ELSE '99204'
    END as billing_code,
    CASE
        WHEN SUM(pt.minutes_of_service) <= 30 THEN 'Office visit, 15-30 min'
        WHEN SUM(pt.minutes_of_service) <= 45 THEN 'Office visit, 31-45 min'
        WHEN SUM(pt.minutes_of_service) <= 60 THEN 'Office visit, 46-60 min'
        ELSE 'Office visit, 61+ min'
    END as billing_code_description,
    'PENDING' as status
FROM (
        SELECT *
        FROM provider_tasks_2023_05
        UNION ALL
        SELECT *
        FROM provider_tasks_2023_06
        UNION ALL
        SELECT *
        FROM provider_tasks_2023_07
        UNION ALL
        SELECT *
        FROM provider_tasks_2023_10
        UNION ALL
        SELECT *
        FROM provider_tasks_2023_11
        UNION ALL
        SELECT *
        FROM provider_tasks_2023_12
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_01
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_02
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_03
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_04
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_05
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_06
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_07
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_08
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_09
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_10
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_11
        UNION ALL
        SELECT *
        FROM provider_tasks_2024_12
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_01
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_02
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_03
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_04
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_05
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_06
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_07
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_08
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_09
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_10
        UNION ALL
        SELECT *
        FROM provider_tasks_2025_11
    ) pt
    LEFT JOIN users u ON pt.provider_id = u.user_id
WHERE pt.task_date IS NOT NULL
    AND pt.provider_id IS NOT NULL
GROUP BY pt.provider_id,
    year,
    week_number
ORDER BY year,
    week_number,
    pt.provider_id;