-- Update patient panel with last visit date and provider
-- This updates the patient panel with the most recent visit information
-- Update last visit date and provider from provider tasks
UPDATE patient_panel
SET last_visit_date = (
        SELECT MAX(task_date)
        FROM provider_tasks_2025_09 pt
        WHERE pt.patient_id = patient_panel.patient_id
    ),
    last_visit_provider_id = (
        SELECT pt.provider_id
        FROM provider_tasks_2025_09 pt
        WHERE pt.patient_id = patient_panel.patient_id
            AND pt.task_date = (
                SELECT MAX(task_date)
                FROM provider_tasks_2025_09 pt2
                WHERE pt2.patient_id = patient_panel.patient_id
            )
        LIMIT 1
    ), last_visit_provider_name = (
        SELECT pt.provider_name
        FROM provider_tasks_2025_09 pt
        WHERE pt.patient_id = patient_panel.patient_id
            AND pt.task_date = (
                SELECT MAX(task_date)
                FROM provider_tasks_2025_09 pt2
                WHERE pt2.patient_id = patient_panel.patient_id
            )
        LIMIT 1
    )
WHERE EXISTS (
        SELECT 1
        FROM provider_tasks_2025_09 pt
        WHERE pt.patient_id = patient_panel.patient_id
    );
-- Update last_visit_date in patient_panel from patient_visits
UPDATE patient_panel
SET last_visit_date = (
        SELECT last_visit_date
        FROM patient_visits
        WHERE patient_visits.patient_id = patient_panel.patient_id
    )
WHERE patient_panel.patient_id IN (
        SELECT patient_id
        FROM patient_visits
    );