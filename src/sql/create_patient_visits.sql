-- Create patient_visits table
-- Create patient_visits table with service_type
CREATE TABLE IF NOT EXISTS patient_visits (
    patient_id TEXT PRIMARY KEY,
    last_visit_date TEXT,
    service_type TEXT
);
-- Populate patient_visits with latest visit date and service_type per patient
-- Populate patient_visits with latest visit date and service_type per patient (using LAST FIRST DOB format)
-- Populate patient_visits with latest visit date and service_type per patient (using LAST FIRST DOB format, no commas)
-- The following assumes that patient_name in provider_tasks and related tables is in the format 'LASTNAME FIRSTNAME DOB'.
-- If not, you may need to reconstruct this field from separate columns.
INSERT
    OR REPLACE INTO patient_visits (patient_id, last_visit_date, service_type)
SELECT REPLACE(pv.patient_name, ',', '') AS patient_id,
    pv.last_visit_date,
    pt.task_description AS service_type
FROM (
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            MAX(task_date) AS last_visit_date
        FROM (
                SELECT patient_name,
                    task_date
                FROM provider_tasks
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_01
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_02
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_03
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_04
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_05
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_06
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
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_10
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_11
                UNION ALL
                SELECT patient_name,
                    task_date
                FROM provider_tasks_2025_12
            )
        GROUP BY REPLACE(patient_name, ',', '')
    ) pv
    LEFT JOIN (
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_01
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_02
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_03
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_04
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_05
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_06
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_07
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_08
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_09
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_10
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_11
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            task_date,
            task_description
        FROM provider_tasks_2025_12
    ) pt ON pv.patient_name = pt.patient_name
    AND pv.last_visit_date = pt.task_date;