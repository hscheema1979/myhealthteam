-- Setup Staging for October 2025 Import
-- Create normalized views for October 2025 data

.mode csv
.headers on

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

-- Create normalized coordinator tasks view for October 2025
DROP VIEW IF EXISTS NORM_STAGING_COORDINATOR_TASKS_OCT;
CREATE VIEW NORM_STAGING_COORDINATOR_TASKS_OCT AS
SELECT
  coordinator_id,
  coordinator_name,
  patient_id_raw,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_id_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm,
  activity_date as task_date,
  duration_minutes,
  task_type,
  notes
FROM staging_coordinator_tasks
WHERE activity_date LIKE '2025-10%';

-- October 2025 staging data summary
.output scripts/outputs/reports/staging_october_setup_summary.csv
.headers on
SELECT 
  'Staging Provider Tasks Oct 2025' as data_source,
  COUNT(*) as total_records,
  MIN(activity_date) as earliest_date,
  MAX(activity_date) as latest_date,
  COUNT(DISTINCT patient_name_raw) as unique_raw_patients,
  COUNT(DISTINCT patient_id_norm) as unique_normalized_patients,
  COUNT(DISTINCT provider_code) as unique_providers
FROM NORM_STAGING_PROVIDER_TASKS_OCT

UNION ALL

SELECT 
  'Staging Coordinator Tasks Oct 2025' as data_source,
  COUNT(*) as total_records,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(DISTINCT patient_id_raw) as unique_raw_patients,
  COUNT(DISTINCT patient_id_norm) as unique_normalized_patients,
  COUNT(DISTINCT coordinator_id) as unique_coordinators
FROM NORM_STAGING_COORDINATOR_TASKS_OCT;

-- Patient name normalization examples from October 2025
.output scripts/outputs/reports/october_2025_normalization_examples.csv
.headers on
SELECT 
  'Provider Task Normalization' as data_type,
  patient_name_raw as raw_name,
  patient_id_norm as normalized_name,
  provider_code,
  task_date,
  service,
  'staging_provider_tasks' as source_table
FROM NORM_STAGING_PROVIDER_TASKS_OCT
WHERE patient_name_raw LIKE 'ZEN-%' 
   OR patient_name_raw LIKE 'PM-%' 
   OR patient_name_raw LIKE 'BlessedCare-%'
ORDER BY patient_name_raw
LIMIT 10

UNION ALL

SELECT 
  'Coordinator Task Normalization' as data_type,
  patient_id_raw as raw_name,
  patient_id_norm as normalized_name,
  coordinator_id as provider_code,
  task_date,
  task_type,
  'staging_coordinator_tasks' as source_table
FROM NORM_STAGING_COORDINATOR_TASKS_OCT
WHERE patient_id_raw LIKE 'ZEN-%' 
   OR patient_id_raw LIKE 'PM-%' 
   OR patient_id_raw LIKE 'BlessedCare-%'
ORDER BY patient_id_raw
LIMIT 10;

-- Daily volume for October 2025 staging data
.output scripts/outputs/reports/october_2025_daily_volume_staging.csv
.headers on
SELECT 
  activity_date as task_date,
  'Provider Tasks' as task_type,
  COUNT(*) as task_count,
  COUNT(DISTINCT patient_name_raw) as unique_raw_patients,
  COUNT(DISTINCT patient_id_norm) as unique_normalized_patients,
  COUNT(DISTINCT provider_code) as unique_providers
FROM NORM_STAGING_PROVIDER_TASKS_OCT
GROUP BY activity_date
ORDER BY activity_date;

.output stdout