-- Reusable script to create and populate patient_visits table with latest visit date per patient (using patient_name as key)
-- Drop old patient_visits table if it exists
DROP TABLE IF EXISTS patient_visits;
-- Create new patient_visits table
CREATE TABLE patient_visits (
    patient_id TEXT PRIMARY KEY,
    last_visit_date TEXT
);
-- Populate patient_visits with latest visit date per patient_name
INSERT
    OR REPLACE INTO patient_visits (patient_id, last_visit_date)
SELECT patient_name AS patient_id,
    MAX(task_date) AS last_visit_date
FROM (
        SELECT patient_name,
            task_date
        FROM provider_tasks
        UNION ALL
        SELECT patient_name,
            task_date
        FROM provider_tasks_2025_07
        UNION ALL
        SELECT patient_name,
            task_date
        FROM provider_tasks_2025_08
        UNION ALL
        SELECT patient_name,
            task_date
        FROM provider_tasks_2025_09
    )
GROUP BY patient_name;