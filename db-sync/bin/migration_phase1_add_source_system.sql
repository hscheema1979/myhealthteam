-- =============================================================================
-- Migration Phase 1: Add source_system Column to VPS2 Operational Tables
-- =============================================================================
-- This script adds the source_system column to all operational tables on VPS2
-- to distinguish between CSV-imported data and manual/live user entries.
--
-- IMPORTANT: Run this BEFORE syncing csv_* tables
-- =============================================================================

BEGIN;

-- =============================================================================
-- PART 1: Add source_system to 2026 tables (Laura's live data)
-- =============================================================================
-- These tables contain Laura's entries starting 1/19/2026
-- Mark existing records as 'DASHBOARD' since they were entered via web UI

ALTER TABLE coordinator_tasks_2026_01 ADD COLUMN source_system TEXT DEFAULT 'DASHBOARD';
UPDATE coordinator_tasks_2026_01 SET source_system = 'DASHBOARD' WHERE source_system IS NULL;

ALTER TABLE provider_tasks_2026_01 ADD COLUMN source_system TEXT DEFAULT 'DASHBOARD';
UPDATE provider_tasks_2026_01 SET source_system = 'DASHBOARD' WHERE source_system IS NULL;

-- =============================================================================
-- PART 2: Add source_system to pre-2026 tables (CSV data - will be deleted)
-- =============================================================================
-- These tables contain CSV-imported data that will be migrated to csv_* tables
-- Mark as 'CSV_IMPORT' for clarity before deletion in Phase 3

-- 2025 Coordinator tables
ALTER TABLE coordinator_tasks_2025_01 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_02 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_03 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_04 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_05 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_06 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_07 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_08 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_09 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_10 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_11 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_2025_12 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';

-- 2022 and older Coordinator tables
ALTER TABLE coordinator_tasks_2022_01 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE coordinator_tasks_1999_12 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';

-- 2025 Provider tables
ALTER TABLE provider_tasks_2025_01 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_02 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_03 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_04 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_05 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_06 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_07 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_08 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_09 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_10 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_11 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2025_12 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';

-- 2024 Provider tables
ALTER TABLE provider_tasks_2024_01 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_02 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_03 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_04 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_05 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_06 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_07 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_08 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_09 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_10 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_11 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2024_12 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';

-- 2023 Provider tables
ALTER TABLE provider_tasks_2023_05 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2023_06 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2023_07 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2023_10 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2023_11 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
ALTER TABLE provider_tasks_2023_12 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';

-- 2001 Provider table (old data)
ALTER TABLE provider_tasks_2001_01 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';

-- =============================================================================
-- PART 3: Verification
-- =============================================================================

-- Verify 2026 tables have correct source_system (should be DASHBOARD)
SELECT 'Verification: 2026 tables should have DASHBOARD source_system' as check;
SELECT 'coordinator_tasks_2026_01' as table_name,
       source_system,
       COUNT(*) as count
FROM coordinator_tasks_2026_01
GROUP BY source_system;

SELECT 'provider_tasks_2026_01' as table_name,
       source_system,
       COUNT(*) as count
FROM provider_tasks_2026_01
GROUP BY source_system;

COMMIT;

-- =============================================================================
-- Summary of Changes:
-- =============================================================================
-- - Added source_system column to all operational tables
-- - 2026_01 tables: Existing records marked as DASHBOARD (Laura's data)
-- - Pre-2026 tables: Existing records marked as CSV_IMPORT (will be deleted)
-- - Future entries will have source_system set automatically
-- =============================================================================
