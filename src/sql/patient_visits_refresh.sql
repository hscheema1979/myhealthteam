-- Reusable script to create and populate patient_visits table with latest visit date and service_type per patient (using patient_name as key)
-- Drop old patient_visits table if it exists
DROP TABLE IF EXISTS patient_visits;
-- Create new patient_visits table
CREATE TABLE patient_visits (
    patient_id TEXT PRIMARY KEY,
    last_visit_date TEXT,
    service_type TEXT
);
-- Populate patient_visits with latest visit date and service_type per patient
INSERT OR REPLACE INTO patient_visits (patient_id, last_visit_date, service_type)
WITH all_pt AS (
    SELECT patient_name AS patient_id, task_date AS activity_date, service_type FROM provider_tasks
    UNION ALL
    SELECT patient_name, task_date, service_type FROM provider_tasks_2025_07
    UNION ALL
    SELECT patient_name, task_date, service_type FROM provider_tasks_2025_08
    UNION ALL
    SELECT patient_name, task_date, service_type FROM provider_tasks_2025_09
    UNION ALL
    SELECT patient_name, task_date, service_type FROM provider_tasks_2025_10
    UNION ALL
    SELECT patient_name, task_date, service_type FROM provider_tasks_2025_11
),
last_dates AS (
    SELECT patient_id, MAX(activity_date) AS last_date
    FROM all_pt
    WHERE patient_id IS NOT NULL AND TRIM(patient_id) != ''
    GROUP BY patient_id
)
SELECT a.patient_id, l.last_date AS last_visit_date, a.service_type
FROM all_pt a
JOIN last_dates l
  ON l.patient_id = a.patient_id AND l.last_date = a.activity_date;