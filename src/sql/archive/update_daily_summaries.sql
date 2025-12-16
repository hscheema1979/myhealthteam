-- update_daily_summaries.sql
-- Ensure all summary tables exist for September 2025
CREATE TABLE IF NOT EXISTS coordinator_monthly_summary_2025_09 (
    patient_id TEXT,
    coordinator_id TEXT,
    total_minutes INT,
    month INT,
    year INT
);
CREATE TABLE IF NOT EXISTS coordinator_minutes_2025_09 (
    coordinator_id TEXT,
    total_minutes INT,
    month INT,
    year INT
);
CREATE TABLE IF NOT EXISTS provider_weekly_summary_2025_09 (
    provider_id INT,
    week INT,
    year INT,
    total_tasks INT
);
CREATE TABLE IF NOT EXISTS provider_monthly_billing_2025_09 (
    provider_id INT,
    patient_id INT,
    billing_code TEXT,
    total_tasks INT,
    month INT,
    year INT
);
DELETE FROM coordinator_monthly_summary_2025_09
WHERE month = 9
    AND year = 2025;
INSERT INTO coordinator_monthly_summary_2025_09 (
        patient_id,
        coordinator_id,
        total_minutes,
        month,
        year
    )
SELECT patient_id,
    coordinator_id,
    SUM(duration_minutes) AS total_minutes,
    9 AS month,
    2025 AS year
FROM coordinator_tasks_2025_09
WHERE strftime('%m', task_date) = '09'
    AND strftime('%Y', task_date) = '2025'
GROUP BY patient_id,
    coordinator_id;
DELETE FROM coordinator_minutes_2025_09
WHERE month = 9
    AND year = 2025;
INSERT INTO coordinator_minutes_2025_09 (coordinator_id, total_minutes, month, year)
SELECT coordinator_id,
    SUM(duration_minutes) AS total_minutes,
    9 AS month,
    2025 AS year
FROM coordinator_tasks_2025_09
WHERE strftime('%m', task_date) = '09'
    AND strftime('%Y', task_date) = '2025'
GROUP BY coordinator_id;
DELETE FROM provider_weekly_summary_2025_09
WHERE year = 2025;
INSERT INTO provider_weekly_summary_2025_09 (provider_id, week, year, total_tasks)
SELECT provider_id,
    strftime('%W', task_date) AS week,
    2025 AS year,
    COUNT(*) AS total_tasks
FROM provider_tasks_2025_09
WHERE strftime('%Y', task_date) = '2025'
GROUP BY provider_id,
    strftime('%W', task_date);
DELETE FROM provider_monthly_billing_2025_09
WHERE month = 9
    AND year = 2025;
INSERT INTO provider_monthly_billing_2025_09 (
        provider_id,
        patient_id,
        billing_code,
        total_tasks,
        month,
        year
    )
SELECT provider_id,
    patient_id,
    billing_code,
    COUNT(*) AS total_tasks,
    9 AS month,
    2025 AS year
FROM provider_tasks_2025_09
WHERE strftime('%m', task_date) = '09'
    AND strftime('%Y', task_date) = '2025'
GROUP BY provider_id,
    patient_id,
    billing_code;
UPDATE patient_panel
SET last_visit_date = (
        SELECT MAX(task_date)
        FROM provider_tasks_2025_09
        WHERE provider_tasks_2025_09.patient_id = patient_panel.patient_id
    ),
    last_visit_provider_id = (
        SELECT provider_id
        FROM provider_tasks_2025_09
        WHERE provider_tasks_2025_09.patient_id = patient_panel.patient_id
            AND task_date = (
                SELECT MAX(task_date)
                FROM provider_tasks_2025_09
                WHERE provider_tasks_2025_09.patient_id = patient_panel.patient_id
            )
    )
WHERE patient_id IN (
        SELECT DISTINCT patient_id
        FROM provider_tasks_2025_09
        WHERE strftime('%m', task_date) = '09'
            AND strftime('%Y', task_date) = '2025'
    );