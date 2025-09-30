-- This script creates a provider weekly summary table WITH billing codes and status for pay and billing
-- 1. Clears any existing data from the final summary table
-- 2. Creates and populates a temporary table with weekly provider summary data, including billing codes and status
-- 3. Creates the permanent 'provider_weekly_summary_with_billing' table with the correct schema
-- 4. Inserts the data from the temporary table into the permanent table
-- 5. Cleans up by dropping the temporary table
DELETE FROM provider_weekly_summary_with_billing;
DROP TABLE IF EXISTS temp_weekly_summary_with_billing;
CREATE TEMPORARY TABLE temp_weekly_summary_with_billing AS
SELECT pt.provider_id,
    pt.provider_name,
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
        WHEN COUNT(pt.provider_task_id) <= 5 THEN '99201'
        WHEN COUNT(pt.provider_task_id) <= 10 THEN '99202'
        WHEN COUNT(pt.provider_task_id) <= 15 THEN '99203'
        ELSE '99204'
    END as billing_code,
    CASE
        WHEN COUNT(pt.provider_task_id) <= 5 THEN 'Office visit, minimal'
        WHEN COUNT(pt.provider_task_id) <= 10 THEN 'Office visit, straightforward'
        WHEN COUNT(pt.provider_task_id) <= 15 THEN 'Office visit, low complexity'
        ELSE 'Office visit, moderate complexity'
    END as billing_code_description,
    'PENDING' as status -- Placeholder for status, can be updated as needed
FROM provider_tasks pt
WHERE pt.task_date IS NOT NULL
    AND pt.task_date != ''
    AND LENGTH(pt.task_date) = 10
    AND SUBSTR(pt.task_date, 5, 1) = '-'
    AND SUBSTR(pt.task_date, 8, 1) = '-'
    AND CAST(strftime('%Y', pt.task_date) AS INTEGER) >= 2023
    AND pt.provider_id IS NOT NULL
    AND pt.provider_id != ''
GROUP BY pt.provider_id,
    year,
    week_number;
CREATE TABLE IF NOT EXISTS provider_weekly_summary_with_billing (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    status TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);
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
SELECT CAST(provider_id AS INTEGER),
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
FROM temp_weekly_summary_with_billing;
DROP TABLE temp_weekly_summary_with_billing;
-- Optional: SELECT * FROM provider_weekly_summary_with_billing LIMIT 5;