-- Create October 2025 Normalized Views in Staging
-- Simple view creation for October 2025 data

-- Create normalized provider tasks view for October 2025
DROP VIEW IF EXISTS NORM_STAGING_PROVIDER_TASKS_OCT;
CREATE VIEW NORM_STAGING_PROVIDER_TASKS_OCT AS
SELECT
  provider_code,
  patient_name_raw,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm,
  service,
  billing_code,
  minutes_raw,
  activity_date as task_date,
  year_month
FROM staging_provider_tasks
WHERE activity_date LIKE '2025-10%';

-- Create normalized coordinator tasks view for October 2025 (corrected schema)
DROP VIEW IF EXISTS NORM_STAGING_COORDINATOR_TASKS_OCT;
CREATE VIEW NORM_STAGING_COORDINATOR_TASKS_OCT AS
SELECT
  staff_code as coordinator_id,
  patient_name_raw as patient_id_raw,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm,
  activity_date as task_date,
  minutes_raw as duration_minutes,
  task_type,
  notes
FROM staging_coordinator_tasks
WHERE activity_date LIKE '2025-10%';