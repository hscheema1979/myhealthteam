-- =============================================================================
-- Migration Phase 2: Update Views to Include 2026 Tables
-- =============================================================================
-- This script updates the coordinator_tasks and provider_tasks views
-- to include the 2026_01 tables (Laura's live data)
--
-- IMPORTANT: Run this AFTER Phase 1 (adding source_system column)
-- =============================================================================

BEGIN;

-- =============================================================================
-- PART 1: Update coordinator_tasks View
-- =============================================================================

DROP VIEW IF EXISTS coordinator_tasks;

CREATE VIEW coordinator_tasks AS
SELECT * FROM coordinator_tasks_2022_01
UNION ALL
SELECT * FROM coordinator_tasks_2025_01
UNION ALL
SELECT * FROM coordinator_tasks_2025_02
UNION ALL
SELECT * FROM coordinator_tasks_2025_03
UNION ALL
SELECT * FROM coordinator_tasks_2025_04
UNION ALL
SELECT * FROM coordinator_tasks_2025_05
UNION ALL
SELECT * FROM coordinator_tasks_2025_06
UNION ALL
SELECT * FROM coordinator_tasks_2025_07
UNION ALL
SELECT * FROM coordinator_tasks_2025_08
UNION ALL
SELECT * FROM coordinator_tasks_2025_09
UNION ALL
SELECT * FROM coordinator_tasks_2025_10
UNION ALL
SELECT * FROM coordinator_tasks_2025_11
UNION ALL
SELECT * FROM coordinator_tasks_2025_12
UNION ALL
SELECT * FROM coordinator_tasks_2026_01;  -- NEW: Laura's live data

-- =============================================================================
-- PART 2: Update provider_tasks View
-- =============================================================================

DROP VIEW IF EXISTS provider_tasks;

CREATE VIEW provider_tasks AS
SELECT * FROM provider_tasks_2001_01
UNION ALL
SELECT * FROM provider_tasks_2023_05
UNION ALL
SELECT * FROM provider_tasks_2023_06
UNION ALL
SELECT * FROM provider_tasks_2023_07
UNION ALL
SELECT * FROM provider_tasks_2023_10
UNION ALL
SELECT * FROM provider_tasks_2023_11
UNION ALL
SELECT * FROM provider_tasks_2023_12
UNION ALL
SELECT * FROM provider_tasks_2024_01
UNION ALL
SELECT * FROM provider_tasks_2024_02
UNION ALL
SELECT * FROM provider_tasks_2024_03
UNION ALL
SELECT * FROM provider_tasks_2024_04
UNION ALL
SELECT * FROM provider_tasks_2024_05
UNION ALL
SELECT * FROM provider_tasks_2024_06
UNION ALL
SELECT * FROM provider_tasks_2024_07
UNION ALL
SELECT * FROM provider_tasks_2024_08
UNION ALL
SELECT * FROM provider_tasks_2024_09
UNION ALL
SELECT * FROM provider_tasks_2024_10
UNION ALL
SELECT * FROM provider_tasks_2024_11
UNION ALL
SELECT * FROM provider_tasks_2024_12
UNION ALL
SELECT * FROM provider_tasks_2025_01
UNION ALL
SELECT * FROM provider_tasks_2025_02
UNION ALL
SELECT * FROM provider_tasks_2025_03
UNION ALL
SELECT * FROM provider_tasks_2025_04
UNION ALL
SELECT * FROM provider_tasks_2025_05
UNION ALL
SELECT * FROM provider_tasks_2025_06
UNION ALL
SELECT * FROM provider_tasks_2025_07
UNION ALL
SELECT * FROM provider_tasks_2025_08
UNION ALL
SELECT * FROM provider_tasks_2025_09
UNION ALL
SELECT * FROM provider_tasks_2025_10
UNION ALL
SELECT * FROM provider_tasks_2025_11
UNION ALL
SELECT * FROM provider_tasks_2025_12
UNION ALL
SELECT * FROM provider_tasks_2026_01;  -- NEW: Laura's live data

-- =============================================================================
-- PART 3: Verify Views Include 2026 Data
-- =============================================================================

-- Verify coordinator_tasks view includes 2026
SELECT 'coordinator_tasks view total (should include 2026):' as check, COUNT(*) as total
FROM coordinator_tasks;

SELECT 'coordinator_tasks view from 2026-01:' as check, COUNT(*) as total
FROM coordinator_tasks
WHERE task_date >= '2026-01-01';

-- Verify provider_tasks view includes 2026
SELECT 'provider_tasks view total (should include 2026):' as check, COUNT(*) as total
FROM provider_tasks;

SELECT 'provider_tasks view from 2026-01:' as check, COUNT(*) as total
FROM provider_tasks
WHERE task_date >= '2026-01-01';

COMMIT;

-- =============================================================================
-- Summary of Changes:
-- =============================================================================
-- - Updated coordinator_tasks view to include coordinator_tasks_2026_01
-- - Updated provider_tasks view to include provider_tasks_2026_01
-- - Dashboards will now see Laura's live entries from 2026
-- =============================================================================
