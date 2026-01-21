-- =============================================================================
-- Migration Phase 2d: Fix Views - Handle Major Schema Differences
-- =============================================================================
-- Schema changes:
-- - coordinator_tasks_2025_* has coordinator_name (no task_id)
-- - coordinator_tasks_2026_01 has task_id (no coordinator_name)
--
-- - provider_tasks_2023-2025 have 15 columns (minutes_of_service, billing_code, etc.)
-- - provider_tasks_2026_01 has 22 columns (completely different schema)
--
-- Strategy:
-- - coordinator_tasks view: Include all tables with NULL for missing columns
-- - provider_tasks view: Only include 2023-2025 tables (2026_01 excluded - incompatible)
--   2026_01 data will need to be accessed directly or via a separate view
-- =============================================================================

BEGIN;

-- Drop existing views
DROP VIEW IF EXISTS coordinator_tasks;
DROP VIEW IF EXISTS provider_tasks;

-- =============================================================================
-- Create coordinator_tasks view
-- Maps 2025 schema (with coordinator_name) and 2026 schema (with task_id)
-- to a common schema with both columns (NULL where not applicable)
-- =============================================================================
CREATE VIEW coordinator_tasks AS
-- 1999/2022 tables: have coordinator_name, no task_id, no submission_status, no created_at_pst
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    NULL as submission_status,
    NULL as created_at_pst,
    NULL as task_id
FROM coordinator_tasks_1999_12
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    NULL as submission_status,
    NULL as created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2022_01
UNION ALL
-- 2025 tables: have coordinator_name, no task_id
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_01
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_02
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_03
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_04
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_05
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_06
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_07
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_08
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_09
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_10
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_11
UNION ALL
SELECT
    coordinator_task_id,
    coordinator_id,
    coordinator_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    NULL as task_id
FROM coordinator_tasks_2025_12
UNION ALL
-- 2026 table: has task_id, no coordinator_name
-- Need to look up coordinator_name from users table
SELECT
    c.coordinator_task_id,
    c.coordinator_id,
    u.full_name as coordinator_name,
    c.patient_id,
    c.task_date,
    c.duration_minutes,
    c.task_type,
    c.notes,
    c.source_system,
    c.imported_at,
    c.submission_status,
    c.created_at_pst,
    c.task_id
FROM coordinator_tasks_2026_01 c
LEFT JOIN users u ON c.coordinator_id = CAST(u.user_id AS TEXT);

-- =============================================================================
-- Create provider_tasks view
-- NOTE: Only includes 2023-2025 tables with compatible schema
-- provider_tasks_2026_01 has a completely different 22-column schema and is excluded
-- Use provider_tasks_2026_01 directly or create a separate view for it
-- =============================================================================
CREATE VIEW provider_tasks AS
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2023_05
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2023_06
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2023_07
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2023_10
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2023_11
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2023_12
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_01
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_02
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_03
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_04
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_05
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_06
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_07
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_08
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_09
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_10
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_11
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2024_12
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_01
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_02
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_03
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_04
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_05
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_06
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_07
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_08
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_09
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_10
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_11
UNION ALL
SELECT
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    notes,
    minutes_of_service,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted
FROM provider_tasks_2025_12;

COMMIT;

-- =============================================================================
-- Summary:
-- - coordinator_tasks view: Includes 2025 tables + 2026_01 (with coordinator_name join)
-- - provider_tasks view: Includes 2023-2025 tables only (2026_01 excluded - incompatible schema)
-- - 2026_01 provider data should be queried from provider_tasks_2026_01 directly
-- =============================================================================
