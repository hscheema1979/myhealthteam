-- Correct October 2025 Normalization
-- Properly parse "LAST, FIRST DOB" format

-- Drop and recreate with proper normalization
DROP VIEW IF EXISTS NORM_STAGING_PROVIDER_TASKS_OCT;
CREATE VIEW NORM_STAGING_PROVIDER_TASKS_OCT AS
SELECT
  provider_code,
  patient_name_raw,
  -- Extract just the name portion (before DOB) and convert to "FIRST LAST" format
  TRIM(
    SUBSTR(patient_name_raw, INSTR(patient_name_raw, ',') + 1, 
           LENGTH(patient_name_raw) - INSTR(REVERSE(patient_name_raw), ' ') - INSTR(patient_name_raw, ',')) || ' ' ||
    SUBSTR(patient_name_raw, 1, INSTR(patient_name_raw, ',') - 1)
  ) AS patient_name_normalized,
  -- Extract DOB (last part after last space)
  TRIM(SUBSTR(patient_name_raw, LENGTH(patient_name_raw) - INSTR(REVERSE(patient_name_raw), ' ') + 1)) AS date_of_birth,
  service,
  billing_code,
  minutes_raw,
  activity_date as task_date,
  year_month
FROM staging_provider_tasks
WHERE activity_date LIKE '2025-10%';

-- Test the normalization
SELECT 'Normalization Test Results:' as test_label;
SELECT 
  patient_name_raw,
  patient_name_normalized,
  date_of_birth,
  provider_code
FROM NORM_STAGING_PROVIDER_TASKS_OCT 
LIMIT 10;