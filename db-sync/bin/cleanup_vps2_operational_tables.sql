-- =============================================================================
-- Cleanup VPS2 Operational Tables - Safe for Laura's Data
-- =============================================================================
-- This script is for VPS2 where tables DON'T have source_system column
--
-- Strategy:
-- 1. KEEP all 2026 data (Laura's live entries starting 1/19)
-- 2. DELETE all data from 2025 and earlier (this is CSV data now in csv_* tables)
--
-- The csv_* tables become the source of truth for billing
-- Operational tables are used only for live user data going forward
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- PART 1: Delete all data from 2025 and earlier tables
--
-- NOTE: These tables contain only CSV-imported data (thousands of records
-- per month with full date ranges). Laura started using the system on 1/19/2026,
-- so her data is only in 2026 tables.
-- -----------------------------------------------------------------------------

-- Coordinator tasks 2025 (all months)
DELETE FROM coordinator_tasks_2025_12 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_11 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_10 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_09 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_08 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_07 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_06 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_05 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_04 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_03 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_02 WHERE 1=1;
DELETE FROM coordinator_tasks_2025_01 WHERE 1=1;

-- Coordinator tasks older (2022 and earlier)
DELETE FROM coordinator_tasks_2022_01 WHERE 1=1;
DELETE FROM coordinator_tasks_1999_12 WHERE 1=1;

-- Provider tasks 2025 (all months)
DELETE FROM provider_tasks_2025_12 WHERE 1=1;
DELETE FROM provider_tasks_2025_11 WHERE 1=1;
DELETE FROM provider_tasks_2025_10 WHERE 1=1;
DELETE FROM provider_tasks_2025_09 WHERE 1=1;
DELETE FROM provider_tasks_2025_08 WHERE 1=1;
DELETE FROM provider_tasks_2025_07 WHERE 1=1;
DELETE FROM provider_tasks_2025_06 WHERE 1=1;
DELETE FROM provider_tasks_2025_05 WHERE 1=1;
DELETE FROM provider_tasks_2025_04 WHERE 1=1;
DELETE FROM provider_tasks_2025_03 WHERE 1=1;
DELETE FROM provider_tasks_2025_02 WHERE 1=1;
DELETE FROM provider_tasks_2025_01 WHERE 1=1;

-- Provider tasks 2024 (all months)
DELETE FROM provider_tasks_2024_12 WHERE 1=1;
DELETE FROM provider_tasks_2024_11 WHERE 1=1;
DELETE FROM provider_tasks_2024_10 WHERE 1=1;
DELETE FROM provider_tasks_2024_09 WHERE 1=1;
DELETE FROM provider_tasks_2024_08 WHERE 1=1;
DELETE FROM provider_tasks_2024_07 WHERE 1=1;
DELETE FROM provider_tasks_2024_06 WHERE 1=1;
DELETE FROM provider_tasks_2024_05 WHERE 1=1;
DELETE FROM provider_tasks_2024_04 WHERE 1=1;
DELETE FROM provider_tasks_2024_03 WHERE 1=1;
DELETE FROM provider_tasks_2024_02 WHERE 1=1;
DELETE FROM provider_tasks_2024_01 WHERE 1=1;

-- Provider tasks 2023 (all months)
DELETE FROM provider_tasks_2023_12 WHERE 1=1;
DELETE FROM provider_tasks_2023_11 WHERE 1=1;
DELETE FROM provider_tasks_2023_10 WHERE 1=1;
DELETE FROM provider_tasks_2023_07 WHERE 1=1;
DELETE FROM provider_tasks_2023_06 WHERE 1=1;
DELETE FROM provider_tasks_2023_05 WHERE 1=1;

-- Provider tasks older (2001)
DELETE FROM provider_tasks_2001_01 WHERE 1=1;

-- -----------------------------------------------------------------------------
-- PART 2: VERIFY - 2026 tables should be untouched (Laura's data)
-- -----------------------------------------------------------------------------

SELECT 'coordinator_tasks_2026_01 - Laura data' as table_name, COUNT(*) as record_count
FROM coordinator_tasks_2026_01
UNION ALL
SELECT 'provider_tasks_2026_01 - Laura data', COUNT(*) FROM provider_tasks_2026_01;

SELECT 'coordinator_tasks_2026_01 date range' as info,
       MIN(task_date) as first_date,
       MAX(task_date) as last_date
FROM coordinator_tasks_2026_01
UNION ALL
SELECT 'provider_tasks_2026_01 date range', MIN(task_date), MAX(task_date)
FROM provider_tasks_2026_01;

COMMIT;

-- =============================================================================
-- Summary After Cleanup:
-- =============================================================================
-- - 2025 and earlier: Deleted (CSV data now lives in csv_* tables)
-- - 2026_01: Preserved (Laura's live data)
-- - csv_* tables: New billing source of truth (added separately via sync)
-- =============================================================================
