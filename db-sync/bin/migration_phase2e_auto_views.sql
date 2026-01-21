BEGIN;
-- Coordinator Tasks View
-- Auto-generated to handle schema differences
DROP VIEW IF EXISTS coordinator_tasks;
CREATE VIEW coordinator_tasks AS
SELECT coordinator_task_id, coordinator_id, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, submission_status, created_at_pst, task_id, NULL as coordinator_name
FROM coordinator_tasks_2026_01
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, NULL as submission_status, NULL as created_at_pst, NULL as task_id
FROM coordinator_tasks_1999_12
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, NULL as submission_status, NULL as created_at_pst, NULL as task_id
FROM coordinator_tasks_2022_01
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_01
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_02
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_03
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_04
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_05
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_06
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_07
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_08
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_09
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_10
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst, NULL as submission_status, NULL as task_id
FROM coordinator_tasks_2025_11
UNION ALL
SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, submission_status, created_at_pst, NULL as task_id
FROM coordinator_tasks_2025_12;

-- Provider Tasks View
-- Auto-generated to handle schema differences
-- Note: Tables with incompatible schemas are excluded
DROP VIEW IF EXISTS provider_tasks;
CREATE VIEW provider_tasks AS
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2001_01
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2023_05
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2023_06
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2023_07
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2023_10
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2023_11
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2023_12
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_01
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_02
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_03
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_04
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_05
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_06
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_07
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_08
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_09
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_10
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_11
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2024_12
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_01
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_02
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_03
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_04
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_05
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_06
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_07
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_08
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_09
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_10
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_11
UNION ALL
SELECT provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code, billing_code_description, source_system, imported_at, status, is_deleted
FROM provider_tasks_2025_12;
COMMIT;