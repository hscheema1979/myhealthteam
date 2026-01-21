-- =============================================================================
-- Migration Phase 2b: Fix Views - Handle Column Mismatch
-- =============================================================================
-- This updates views to work with tables that may have different columns
-- =============================================================================

BEGIN;

-- Drop existing views
DROP VIEW IF EXISTS coordinator_tasks;
DROP VIEW IF EXISTS provider_tasks;

-- Create coordinator_tasks view with NULL for missing columns in older tables
CREATE VIEW coordinator_tasks AS
SELECT *, NULL as source_system FROM coordinator_tasks_2022_01
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_01
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_02
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_03
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_04
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_05
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_06
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_07
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_08
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_09
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_10
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_11
UNION ALL
SELECT *, NULL as source_system FROM coordinator_tasks_2025_12
UNION ALL
SELECT * FROM coordinator_tasks_2026_01;  -- Has source_system column

-- Create provider_tasks view with NULL for missing columns in older tables
CREATE VIEW provider_tasks AS
SELECT *, NULL as source_system FROM provider_tasks_2001_01
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2023_05
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2023_06
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2023_07
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2023_10
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2023_11
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2023_12
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_01
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_02
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_03
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_04
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_05
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_06
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_07
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_08
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_09
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_10
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_11
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2024_12
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_01
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_02
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_03
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_04
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_05
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_06
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_07
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_08
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_09
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_10
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_11
UNION ALL
SELECT *, NULL as source_system FROM provider_tasks_2025_12
UNION ALL
SELECT * FROM provider_tasks_2026_01;  -- Has source_system column

COMMIT;

-- =============================================================================
-- Summary: Views fixed to handle column differences
-- Older tables have NULL source_system, 2026_01 tables have actual values
-- =============================================================================
