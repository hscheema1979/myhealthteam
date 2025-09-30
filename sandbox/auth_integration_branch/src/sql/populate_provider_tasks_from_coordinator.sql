-- Transform phone review tasks from coordinator_tasks to provider_tasks
-- Only inserts tasks with phone-related task_type
INSERT INTO provider_tasks (
        provider_task_id,
        task_id,
        provider_id,
        provider_name,
        patient_name,
        user_id,
        patient_id,
        status,
        notes,
        minutes_of_service,
        billing_code_id,
        created_date,
        updated_date,
        task_date,
        month,
        year,
        billing_code,
        billing_code_description,
        task_description,
        source_system,
        imported_at
    )
SELECT NULL AS provider_task_id,
    NULL AS task_id,
    NULL AS provider_id,
    -- No direct mapping from coordinator_tasks
    ct.coordinator_id AS provider_name,
    -- Use coordinator_id as provider_name
    ct.patient_id AS patient_name,
    NULL AS user_id,
    ct.patient_id,
    NULL AS status,
    ct.notes,
    ct.duration_minutes AS minutes_of_service,
    NULL AS billing_code_id,
    CURRENT_TIMESTAMP AS created_date,
    NULL AS updated_date,
    ct.task_date,
    strftime('%m', ct.task_date) AS month,
    strftime('%Y', ct.task_date) AS year,
    NULL AS billing_code,
    NULL AS billing_code_description,
    ct.task_type AS task_description,
    'coordinator_tasks' AS source_system,
    CURRENT_TIMESTAMP AS imported_at
FROM coordinator_tasks ct
WHERE ct.task_type LIKE '%phone%';