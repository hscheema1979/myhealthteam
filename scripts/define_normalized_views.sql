-- Normalized views for consistent comparison keys

-- Staging provider tasks: normalized patient_id and activity_date
DROP VIEW IF EXISTS NORM_STAGING_PROVIDER_TASKS;
CREATE VIEW NORM_STAGING_PROVIDER_TASKS AS
SELECT 
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
  activity_date AS activity_date
FROM staging_provider_tasks
WHERE activity_date IS NOT NULL;

-- Staging coordinator tasks: normalized patient_id and activity_date
DROP VIEW IF EXISTS NORM_STAGING_COORDINATOR_TASKS;
CREATE VIEW NORM_STAGING_COORDINATOR_TASKS AS
SELECT 
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
  activity_date AS activity_date
FROM staging_coordinator_tasks
WHERE activity_date IS NOT NULL;

-- Sheets provider tasks are already normalized in V_PROVIDER_TASKS_NORM
DROP VIEW IF EXISTS NORM_SHEETS_PROVIDER_TASKS;
CREATE VIEW NORM_SHEETS_PROVIDER_TASKS AS
SELECT patient_id, activity_date
FROM V_PROVIDER_TASKS_NORM
WHERE activity_date IS NOT NULL;

-- Sheets coordinator tasks are already normalized in V_COORDINATOR_TASKS_NORM
DROP VIEW IF EXISTS NORM_SHEETS_COORDINATOR_TASKS;
CREATE VIEW NORM_SHEETS_COORDINATOR_TASKS AS
SELECT patient_id, activity_date
FROM V_COORDINATOR_TASKS_NORM
WHERE activity_date IS NOT NULL;