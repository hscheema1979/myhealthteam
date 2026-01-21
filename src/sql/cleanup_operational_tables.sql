-- =============================================================================
-- Cleanup Operational Tables - Remove CSV-Imported Data
-- =============================================================================
-- This script cleans up the existing operational tables after the csv_* tables
-- are created. The csv_* tables become the source of truth for billing data.
--
-- Strategy:
-- 1. Delete all data before January 1, 2026 (pre-2026 is historical, use csv_* tables)
-- 2. For 2026 data, delete rows where source_system = 'CSV_IMPORT' (keep only manual entries)
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Part 1: Delete all historical data (before Jan 1, 2026)
-- -----------------------------------------------------------------------------

-- Delete coordinator_tasks tables from 2025 and earlier (only existing tables)
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
-- Also cleanup older tables
DELETE FROM coordinator_tasks_2022_01 WHERE 1=1;
DELETE FROM coordinator_tasks_1999_12 WHERE 1=1;

-- Delete provider_tasks tables from 2025 and earlier (only existing tables)
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
DELETE FROM provider_tasks_2023_12 WHERE 1=1;
DELETE FROM provider_tasks_2023_11 WHERE 1=1;
DELETE FROM provider_tasks_2023_10 WHERE 1=1;
DELETE FROM provider_tasks_2023_07 WHERE 1=1;
DELETE FROM provider_tasks_2023_06 WHERE 1=1;
DELETE FROM provider_tasks_2023_05 WHERE 1=1;
DELETE FROM provider_tasks_2001_01 WHERE 1=1;

-- -----------------------------------------------------------------------------
-- Part 2: For 2026 data, remove CSV_IMPORT entries (keep only manual entries)
-- -----------------------------------------------------------------------------

-- Delete CSV-imported coordinator tasks from 2026_01 (only table that exists)
DELETE FROM coordinator_tasks_2026_01
WHERE source_system = 'CSV_IMPORT';

-- Delete CSV-imported provider tasks from 2026_01 (only table that exists)
DELETE FROM provider_tasks_2026_01
WHERE source_system = 'CSV_IMPORT';

-- -----------------------------------------------------------------------------
-- Part 3: Verify what's left (should only be manual/live entries)
-- -----------------------------------------------------------------------------

-- Count remaining coordinator tasks in 2026_01 (should be low - only manual entries)
SELECT 'coordinator_tasks_2026_01' as table_name, COUNT(*) as remaining_count
FROM coordinator_tasks_2026_01;

-- Count remaining provider tasks in 2026_01 (should be low - only manual entries)
SELECT 'provider_tasks_2026_01' as table_name, COUNT(*) as remaining_count
FROM provider_tasks_2026_01;

-- Count source systems in 2026_01 tables (should only have MANUAL, DASHBOARD, WORKFLOW)
SELECT 'coordinator_tasks_2026_01 source_systems' as table_name, source_system, COUNT(*) as count
FROM coordinator_tasks_2026_01
GROUP BY source_system;

SELECT 'provider_tasks_2026_01 source_systems' as table_name, source_system, COUNT(*) as count
FROM provider_tasks_2026_01
GROUP BY source_system;

COMMIT;

-- =============================================================================
-- Summary After Cleanup:
-- =============================================================================
-- - operational tables (coordinator_tasks_*, provider_tasks_*) contain ONLY manual entries
-- - csv_* tables contain ALL CSV-imported data (billing source of truth)
-- - No duplication between operational and csv_* tables
-- =============================================================================
