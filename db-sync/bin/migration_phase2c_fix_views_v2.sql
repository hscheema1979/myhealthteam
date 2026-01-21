-- =============================================================================
-- Migration Phase 2c: Fix Views - Handle Schema Differences
-- =============================================================================
-- 2025 and earlier tables have: coordinator_task_id, coordinator_id, coordinator_name, ...
-- 2026 tables have: coordinator_task_id, task_id, patient_id, coordinator_id, ...
-- =============================================================================

BEGIN;

-- Drop existing views
DROP VIEW IF EXISTS coordinator_tasks;
DROP VIEW IF EXISTS provider_tasks;

-- Create coordinator_tasks view - map columns to common schema
CREATE VIEW coordinator_tasks AS
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
    NULL as task_id  -- Add for compatibility with 2026 schema
FROM coordinator_tasks_2022_01
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
SELECT
    coordinator_task_id,
    task_id,
    patient_id,
    coordinator_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    source_system,
    imported_at,
    submission_status,
    created_at_pst,
    coordinator_name  -- Add for compatibility with pre-2026 schema
FROM coordinator_tasks_2026_01;

-- Create provider_tasks view - similar approach
CREATE VIEW provider_tasks AS
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2001_01
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2023_05
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2023_06
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2023_07
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2023_10
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2023_11
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2023_12
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_01
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_02
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_03
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_04
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_05
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_06
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_07
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_08
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_09
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_10
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_11
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2024_12
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_01
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_02
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_03
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_04
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_05
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_06
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_07
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_08
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_09
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_10
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_11
UNION ALL
SELECT
    task_id,
    provider_id,
    provider_name,
    patient_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    billing_code,
    location_type,
    patient_type,
    source_system,
    imported_at,
    submission_status,
    created_at_pst
FROM provider_tasks_2025_12
UNION ALL
SELECT * FROM provider_tasks_2026_01;

COMMIT;

-- =============================================================================
-- Summary: Views created with proper column mapping
-- =============================================================================
