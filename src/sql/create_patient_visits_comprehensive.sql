-- Create comprehensive patient_visits table with ALL provider_tasks tables (2024 and 2025)
-- Drop and recreate patient_visits table
DROP TABLE IF EXISTS patient_visits;

CREATE TABLE patient_visits (
    patient_id TEXT PRIMARY KEY,
    last_visit_date TEXT,
    service_type TEXT
);

-- Populate patient_visits with latest visit date and service_type per patient from ALL provider_tasks tables
INSERT OR REPLACE INTO patient_visits (patient_id, last_visit_date, service_type)
SELECT REPLACE(pv.patient_name, ',', '') AS patient_id,
    pv.last_visit_date,
    pt.task_description AS service_type
FROM (
        SELECT REPLACE(patient_name, ',', '') AS patient_name,
            MAX(task_date) AS last_visit_date
        FROM (
                SELECT patient_name, task_date FROM provider_tasks
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_01
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_02
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_03
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_04
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_05
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_06
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_07
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_08
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_09
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_10
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_11
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2024_12
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_01
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_02
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_03
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_04
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_05
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_06
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_07
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_08
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_09
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_10
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_11
                UNION ALL
                SELECT patient_name, task_date FROM provider_tasks_2025_12
            )
        GROUP BY REPLACE(patient_name, ',', '')
    ) pv
    LEFT JOIN (
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_01
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_02
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_03
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_04
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_05
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_06
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_07
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_08
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_09
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_10
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_11
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2024_12
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_01
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_02
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_03
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_04
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_05
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_06
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_07
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_08
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_09
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_10
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_11
        UNION ALL
        SELECT REPLACE(patient_name, ',', '') AS patient_name, task_date, task_description FROM provider_tasks_2025_12
    ) pt ON pv.patient_name = pt.patient_name
    AND pv.last_visit_date = pt.task_date;

-- Show results
SELECT 'patient_visits updated' as status, COUNT(*) as total_rows, COUNT(last_visit_date) as with_last_visit, COUNT(service_type) as with_service_type FROM patient_visits;