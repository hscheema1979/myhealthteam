-- Simple October 2025 Normalization
-- Correctly parse "LAST NAME, FIRST NAME DOB" format

-- Drop and recreate with simplified normalization
DROP VIEW IF EXISTS NORM_STAGING_PROVIDER_TASKS_OCT;
CREATE VIEW NORM_STAGING_PROVIDER_TASKS_OCT AS
SELECT
  provider_code,
  patient_name_raw,
  -- Simple approach: reverse the name parts and remove DOB
  TRIM(
    SUBSTR(patient_name_raw, INSTR(patient_name_raw, ',') + 1,
           INSTR(SUBSTR(patient_name_raw, INSTR(patient_name_raw, ',') + 1), ' ') - 1) || ' ' ||
    SUBSTR(patient_name_raw, 1, INSTR(patient_name_raw, ',') - 1)
  ) AS patient_name_normalized,
  -- Extract DOB from the end
  TRIM(SUBSTR(patient_name_raw, INSTR(REVERSE(patient_name_raw), ' '))) AS date_of_birth,
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
    SUBSTR(patient_name_raw, INSTR(patient_name_raw, ',') + 1,
           INSTR(SUBSTR(patient_name_raw, INSTR(patient_name_raw, ',') + 1), ' ') - 1) || ' ' ||
    SUBSTR(patient_name_raw, 1, INSTR(patient_name_raw, ',') - 1)
  ) AS patient_name_normalized,
  TRIM(SUBSTR(patient_name_raw, INSTR(REVERSE(patient_name_raw), ' '))) AS date_of_birth,
  activity_date as task_date,
  minutes_raw as duration_minutes,
  task_type,
  notes
FROM staging_coordinator_tasks
WHERE activity_date LIKE '2025-10%';

-- Test the normalization
SELECT 'Normalization Test:' as test;
SELECT 
  patient_name_raw,
  patient_name_normalized,
  date_of_birth,
  provider_code,
  task_date
FROM NORM_STAGING_PROVIDER_TASKS_OCT 
LIMIT 8;