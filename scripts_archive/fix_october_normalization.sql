-- Fix October 2025 Normalization
-- Correct patient name extraction and format conversion

-- Drop and recreate with proper normalization
DROP VIEW IF EXISTS NORM_STAGING_PROVIDER_TASKS_OCT;
CREATE VIEW NORM_STAGING_PROVIDER_TASKS_OCT AS
SELECT
  provider_code,
  patient_name_raw,
  -- Extract patient name from "LAST, FIRST DOB" format and convert to "FIRST LAST" format
  TRIM(
    SUBSTR(patient_name_raw, INSTR(patient_name_raw, ',') + 1) || ' ' ||
    SUBSTR(patient_name_raw, 1, INSTR(patient_name_raw, ',') - 1)
  ) AS patient_name_normalized,
  -- Extract DOB for validation
  TRIM(SUBSTR(patient_name_raw, INSTR(patient_name_raw, ' '))) AS extracted_dob,
  service,
  billing_code,
  minutes_raw,
  activity_date as task_date,
  year_month
FROM staging_provider_tasks
WHERE activity_date LIKE '2025-10%';

-- Drop and recreate coordinator tasks view (corrected)
DROP VIEW IF EXISTS NORM_STAGING_COORDINATOR_TASKS_OCT;
CREATE VIEW NORM_STAGING_COORDINATOR_TASKS_OCT AS
SELECT
  staff_code as coordinator_id,
  patient_name_raw,
  TRIM(
    SUBSTR(patient_name_raw, INSTR(patient_name_raw, ',') + 1) || ' ' ||
    SUBSTR(patient_name_raw, 1, INSTR(patient_name_raw, ',') - 1)
  ) AS patient_name_normalized,
  activity_date as task_date,
  minutes_raw as duration_minutes,
  task_type,
  notes
FROM staging_coordinator_tasks
WHERE activity_date LIKE '2025-10%';