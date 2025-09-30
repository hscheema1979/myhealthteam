-- This script performs the following tasks:
-- 1. Clears any existing data from the final summary table.
-- 2. Creates and populates a temporary table with weekly provider summary data,
--    handling all potential NULL values to prevent errors.
-- 3. Creates the permanent 'provider_weekly_summary' table with the correct schema
--    to ensure it matches the database structure.
-- 4. Inserts the data from the temporary table into the permanent table.
-- 5. Cleans up by dropping the temporary table.
-- Step 1: Clear all existing data from the final summary table
DELETE FROM provider_weekly_summary;
-- Step 2: Create a temporary table for the weekly summary data
DROP TABLE IF EXISTS temp_weekly_summary;
CREATE TEMPORARY TABLE temp_weekly_summary AS
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
    CAST(SUM(pt.minutes_of_service) AS REAL) / COUNT(DISTINCT pt.task_date) AS average_daily_minutes,
    COUNT(DISTINCT pt.task_date) AS days_active
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
-- Step 3: Create the permanent table with the correct schema
-- This will ensure the table exists before data is inserted.
-- The schema below is based on the one you provided.
CREATE TABLE IF NOT EXISTS provider_weekly_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    average_daily_minutes REAL DEFAULT 0.0,
    days_active INTEGER DEFAULT 0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);
-- Step 4: Insert data from the temporary table into the permanent table
INSERT INTO provider_weekly_summary (
        provider_id,
        provider_name,
        week_start_date,
        week_end_date,
        year,
        week_number,
        total_tasks_completed,
        total_time_spent_minutes,
        average_daily_minutes,
        days_active
    )
SELECT CAST(provider_id AS INTEGER),
    provider_name,
    week_start_date,
    week_end_date,
    year,
    week_number,
    total_tasks_completed,
    total_time_spent_minutes,
    average_daily_minutes,
    days_active
FROM temp_weekly_summary;
-- Step 5: Clean up the temporary table
DROP TABLE temp_weekly_summary;
-- Optional: Display a sample of the newly populated permanent table
-- SELECT *
-- FROM provider_weekly_summary
-- LIMIT 5;