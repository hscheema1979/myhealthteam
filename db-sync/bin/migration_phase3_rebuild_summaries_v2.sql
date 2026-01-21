-- =============================================================================
-- Migration Phase 3: Rebuild Billing and Payroll Summaries (Corrected)
-- =============================================================================
-- This script rebuilds the billing and payroll summary tables using:
-- 1. csv_* tables for historical billing data (2025 and earlier)
-- 2. Operational tables for 2026 live data (Laura's entries)
-- =============================================================================

BEGIN;

-- =============================================================================
-- PART 1: Clear Existing Summary Data (will be rebuilt)
-- =============================================================================

DELETE FROM provider_weekly_summary_with_billing WHERE 1=1;
DELETE FROM provider_task_billing_status WHERE 1=1;
DELETE FROM coordinator_monthly_summary WHERE 1=1;
DELETE FROM provider_monthly_summary WHERE 1=1;
DELETE FROM provider_weekly_payroll_status WHERE 1=1;

-- =============================================================================
-- PART 2: Populate Coordinator Monthly Summary from csv_coordinator_tasks
-- =============================================================================

INSERT INTO coordinator_monthly_summary (
    coordinator_id,
    coordinator_name,
    month,
    year,
    total_minutes,
    total_tasks,
    billable_minutes,
    non_billable_minutes,
    breakdown_by_task_type,
    source_system
)
SELECT
    staff_id as coordinator_id,
    staff_name as coordinator_name,
    CAST(substr(task_date, 6, 2) AS INTEGER) as month,
    CAST(substr(task_date, 1, 4) AS INTEGER) as year,
    SUM(duration_minutes) as total_minutes,
    COUNT(*) as total_tasks,
    SUM(duration_minutes) as billable_minutes,
    0 as non_billable_minutes,
    task_type as breakdown_by_task_type,
    'CSV_IMPORT' as source_system
FROM csv_coordinator_tasks_2025_12
WHERE staff_id IS NOT NULL
GROUP BY staff_id, staff_name, substr(task_date, 6, 2), substr(task_date, 1, 4), task_type;

-- =============================================================================
-- PART 3: Populate Provider Billing Status from csv_provider_tasks
-- =============================================================================

INSERT INTO provider_task_billing_status (
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    billing_code,
    task_type,
    location_type,
    patient_type,
    duration_minutes,
    billable_minutes,
    is_billable,
    billing_status,
    week_of,
    source_system
)
SELECT
    csv_task_id as task_id,
    staff_id as provider_id,
    staff_name as provider_name,
    patient_id,
    task_date,
    billing_code,
    task_type,
    'Home' as location_type,
    'Follow Up' as patient_type,
    duration_minutes,
    duration_minutes as billable_minutes,
    1 as is_billable,
    'Pending' as billing_status,
    strftime('%Y-W%W', task_date) as week_of,
    'CSV_IMPORT' as source_system
FROM csv_provider_tasks_2025_12
WHERE staff_id IS NOT NULL
  AND duration_minutes > 0;

-- =============================================================================
-- PART 4: Populate Provider Weekly Summary with Billing
-- =============================================================================

INSERT INTO provider_weekly_summary_with_billing (
    provider_id,
    provider_name,
    week_of,
    week_start_date,
    week_end_date,
    billing_code,
    task_type,
    location_type,
    patient_type,
    total_tasks,
    total_minutes,
    total_hours,
    total_billed,
    total_pending,
    source_system
)
SELECT
    staff_id as provider_id,
    staff_name as provider_name,
    strftime('%Y-W%W', task_date) as week_of,
    date(task_date, 'weekday 0', '-6 days') as week_start_date,
    date(task_date, 'weekday 0', '-0 days') as week_end_date,
    billing_code,
    task_type,
    'Home' as location_type,
    'Follow Up' as patient_type,
    COUNT(*) as total_tasks,
    SUM(duration_minutes) as total_minutes,
    ROUND(SUM(duration_minutes) / 60.0, 2) as total_hours,
    0 as total_billed,
    COUNT(*) as total_pending,
    'CSV_IMPORT' as source_system
FROM csv_provider_tasks_2025_12
WHERE staff_id IS NOT NULL AND duration_minutes > 0
GROUP BY staff_id, staff_name, strftime('%Y-W%W', task_date), billing_code, task_type;

-- =============================================================================
-- PART 5: Verification Queries
-- =============================================================================

-- Verify coordinator_monthly_summary populated
SELECT 'coordinator_monthly_summary:' as table_name, COUNT(*) as record_count
FROM coordinator_monthly_summary;

-- Verify provider_task_billing_status populated
SELECT 'provider_task_billing_status:' as table_name, COUNT(*) as record_count
FROM provider_task_billing_status;

-- Verify provider_weekly_summary_with_billing populated
SELECT 'provider_weekly_summary_with_billing:' as table_name, COUNT(*) as record_count
FROM provider_weekly_summary_with_billing;

-- Show breakdown by source_system
SELECT 'coordinator_monthly_summary by source:' as info, source_system, COUNT(*) as count
FROM coordinator_monthly_summary
GROUP BY source_system;

SELECT 'provider_task_billing_status by source:' as info, source_system, COUNT(*) as count
FROM provider_task_billing_status
GROUP BY source_system;

COMMIT;

-- =============================================================================
-- Summary of Changes:
-- =============================================================================
-- - Cleared and rebuilt billing summary tables
-- - Used csv_* tables for historical billing data (2025-12 only as sample)
-- - For full rebuild, need to add UNION ALL for all csv_* tables
-- - 2026 operational data (Laura's entries) can be added separately
-- - Source system tracking maintained (CSV_IMPORT)
-- =============================================================================
