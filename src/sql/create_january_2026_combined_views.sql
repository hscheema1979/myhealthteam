-- =============================================================================
-- January 2026 Combined Billing Views
-- Handles the transition period with both CSV import and live data
-- =============================================================================

BEGIN;

-- =============================================================================
-- Monthly Coordinator Billing - January 2026 Options
-- =============================================================================

-- 1. CSV Import Only (old system data)
DROP VIEW IF EXISTS coordinator_monthly_2026_01_import;
CREATE VIEW coordinator_monthly_2026_01_import AS
SELECT
    staff_id as coordinator_id,
    staff_name as coordinator_name,
    1 as month,
    2026 as year,
    task_type,
    SUM(total_tasks) as total_tasks,
    SUM(total_minutes) as total_minutes,
    ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
    SUM(unique_patients) as unique_patients,
    'CSV_IMPORT' as data_source
FROM csv_monthly_billing_summary_2026_01
WHERE staff_type = 'coordinator'
GROUP BY staff_id, staff_name, task_type;

-- 2. Live Data Only (new system live)
DROP VIEW IF EXISTS coordinator_monthly_2026_01;
CREATE VIEW coordinator_monthly_2026_01 AS
SELECT
    coordinator_id,
    u.full_name as coordinator_name,
    1 as month,
    2026 as year,
    task_type,
    COUNT(*) as total_tasks,
    SUM(duration_minutes) as total_minutes,
    ROUND(SUM(duration_minutes) / 60.0, 2) as total_hours,
    COUNT(DISTINCT patient_id) as unique_patients,
    'LIVE' as data_source
FROM coordinator_tasks_2026_01 c
LEFT JOIN users u ON CAST(c.coordinator_id AS TEXT) = CAST(u.user_id AS TEXT)
WHERE c.coordinator_id IS NOT NULL
GROUP BY c.coordinator_id, u.full_name, task_type;

-- 3. Combined (both sources)
DROP VIEW IF EXISTS coordinator_monthly_2026_01_combined;
CREATE VIEW coordinator_monthly_2026_01_combined AS
-- CSV Import data
SELECT
    staff_id as coordinator_id,
    staff_name as coordinator_name,
    1 as month,
    2026 as year,
    task_type,
    SUM(total_tasks) as total_tasks,
    SUM(total_minutes) as total_minutes,
    ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
    SUM(unique_patients) as unique_patients,
    'CSV_IMPORT' as data_source
FROM csv_monthly_billing_summary_2026_01
WHERE staff_type = 'coordinator'
GROUP BY staff_id, staff_name, task_type

UNION ALL

-- Live data
SELECT
    coordinator_id,
    u.full_name as coordinator_name,
    1 as month,
    2026 as year,
    task_type,
    COUNT(*) as total_tasks,
    SUM(duration_minutes) as total_minutes,
    ROUND(SUM(duration_minutes) / 60.0, 2) as total_hours,
    COUNT(DISTINCT patient_id) as unique_patients,
    'LIVE' as data_source
FROM coordinator_tasks_2026_01 c
LEFT JOIN users u ON CAST(c.coordinator_id AS TEXT) = CAST(u.user_id AS TEXT)
WHERE c.coordinator_id IS NOT NULL
GROUP BY c.coordinator_id, u.full_name, task_type;

-- =============================================================================
-- Weekly Provider Billing - January 2026 Options
-- =============================================================================

-- 1. CSV Import Only
DROP VIEW IF EXISTS provider_weekly_2026_01_import;
CREATE VIEW provider_weekly_2026_01_import AS
SELECT
    provider_id,
    provider_name,
    week_start_date,
    week_end_date,
    year,
    week_number,
    billing_code,
    billing_code_description,
    task_type,
    SUM(total_tasks) as total_tasks,
    SUM(total_minutes) as total_minutes,
    ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
    SUM(unique_patients) as unique_patients,
    'CSV_IMPORT' as data_source
FROM csv_weekly_billing_summary_2026_01
GROUP BY provider_id, provider_name, week_start_date, week_end_date,
         year, week_number, billing_code, task_type;

-- 2. Live Data Only (using existing summary table structure)
DROP VIEW IF EXISTS provider_weekly_2026_01;
CREATE VIEW provider_weekly_2026_01 AS
SELECT
    p.provider_id,
    p.provider_name,
    p.week_start_date,
    p.week_end_date,
    p.year,
    p.week_number,
    p.billing_code,
    p.billing_code_description,
    p.task_type,
    COUNT(*) as total_tasks,
    SUM(p.total_time_spent_minutes) as total_minutes,
    ROUND(SUM(p.total_time_spent_minutes) / 60.0, 2) as total_hours,
    COUNT(DISTINCT t.patient_id) as unique_patients,
    'LIVE' as data_source
FROM provider_weekly_summary_with_billing p
LEFT JOIN provider_tasks_2026_01 t ON p.provider_id = t.provider_id
    AND t.task_date BETWEEN p.week_start_date AND p.week_end_date
WHERE p.week_start_date >= '2026-01-01' AND p.week_end_date <= '2026-01-31'
GROUP BY p.provider_id, p.provider_name, p.week_start_date, p.week_end_date,
         p.year, p.week_number, p.billing_code, p.billing_code_description;

-- 3. Combined (both sources)
DROP VIEW IF EXISTS provider_weekly_2026_01_combined;
CREATE VIEW provider_weekly_2026_01_combined AS
-- CSV Import data
SELECT
    provider_id,
    provider_name,
    week_start_date,
    week_end_date,
    year,
    week_number,
    billing_code,
    billing_code_description,
    task_type,
    SUM(total_tasks) as total_tasks,
    SUM(total_minutes) as total_minutes,
    ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
    SUM(unique_patients) as unique_patients,
    'CSV_IMPORT' as data_source
FROM csv_weekly_billing_summary_2026_01
GROUP BY provider_id, provider_name, week_start_date, week_end_date,
         year, week_number, billing_code, task_type

UNION ALL

-- Live data
SELECT
    p.provider_id,
    p.provider_name,
    p.week_start_date,
    p.week_end_date,
    p.year,
    p.week_number,
    p.billing_code,
    p.billing_code_description,
    p.task_type,
    COUNT(*) as total_tasks,
    SUM(p.total_time_spent_minutes) as total_minutes,
    ROUND(SUM(p.total_time_spent_minutes) / 60.0, 2) as total_hours,
    COUNT(DISTINCT t.patient_id) as unique_patients,
    'LIVE' as data_source
FROM provider_weekly_summary_with_billing p
LEFT JOIN provider_tasks_2026_01 t ON p.provider_id = t.provider_id
    AND t.task_date BETWEEN p.week_start_date AND p.week_end_date
WHERE p.week_start_date >= '2026-01-01' AND p.week_end_date <= '2026-01-31'
GROUP BY p.provider_id, p.provider_name, p.week_start_date, p.week_end_date,
         p.year, p.week_number, p.billing_code, p.billing_code_description;

COMMIT;

-- =============================================================================
-- Summary of Views Created:
-- - coordinator_monthly_2026_01_import: CSV only
-- - coordinator_monthly_2026_01: Live only
-- - coordinator_monthly_2026_01_combined: Both
-- - provider_weekly_2026_01_import: CSV only
-- - provider_weekly_2026_01: Live only
-- - provider_weekly_2026_01_combined: Both
-- =============================================================================
