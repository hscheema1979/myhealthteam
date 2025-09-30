-- validation_checks.sql
-- Basic validation queries to run after transforms
PRAGMA foreign_keys = ON;

SELECT 'SOURCE_COORD_COUNT', COUNT(*) FROM SOURCE_COORDINATOR_TASKS_HISTORY;
SELECT 'STAGING_COORD_COUNT', COUNT(*) FROM staging_coordinator_tasks;
SELECT 'PATIENTS_COUNT', COUNT(*) FROM patients;

-- Example check for one monthly partition; caller can edit or add more
SELECT 'COORD_2025_09_COUNT', COUNT(*) FROM coordinator_tasks_2025_09;

-- Unmatched rows in staging
SELECT 'STAGING_UNMATCHED', COUNT(*) 
FROM staging_coordinator_tasks s
LEFT JOIN patients p ON p.last_first_dob = s.patient_name_raw
WHERE p.patient_id IS NULL;

-- Basic sanity: negative durations
SELECT 'NEGATIVE_MINUTES', COUNT(*) 
FROM staging_coordinator_tasks 
WHERE CAST(minutes_raw AS INTEGER) < 0;