-- Validate normalization on PRE-9/26 dates (like 9/17) to prove consistency
-- This shows normalization would work on historical data too

ATTACH '.\production.db' AS prod;

.mode csv
.headers on

-- Normalized view of PRE-9/26 production data (what staging would look like if it had this data)
DROP VIEW IF EXISTS NORM_PRODUCTION_PRE_SEP26;
CREATE VIEW NORM_PRODUCTION_PRE_SEP26 AS
SELECT
  -- Apply the same normalization logic to production data
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm,
  patient_name as patient_name_raw,
  task_date as activity_date,
  provider_name as provider_code,
  billing_code as service,
  minutes_of_service
FROM prod.provider_tasks
WHERE task_date < '2025-09-26';

-- September 17 validation (pre-normalization date as requested)
.output scripts/outputs/reports/sep_17_2025_pre_normalization_validation.csv
.headers on
SELECT 
  'Production Raw (Sep 17)' as source_type,
  patient_name as patient_name_raw,
  task_date as activity_date,
  provider_name as provider_code,
  billing_code as service
FROM prod.provider_tasks
WHERE task_date = '2025-09-17'
ORDER BY task_date, patient_name
LIMIT 10;

.output scripts/outputs/reports/sep_17_2025_pre_normalization_validation.csv
.headers on
SELECT 
  'Production Normalized (Sep 17)' as source_type,
  patient_id_norm,
  activity_date,
  provider_code,
  service
FROM NORM_PRODUCTION_PRE_SEP26
WHERE activity_date = '2025-09-17'
ORDER BY activity_date, patient_id_norm
LIMIT 10;

-- Multi-day pre-9/26 summary for consistency check
.output scripts/outputs/reports/pre_sep_26_normalization_summary.csv
.headers on
SELECT 
  'Sep 17 Production Raw' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_name) as unique_patients_raw,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM prod.provider_tasks
WHERE task_date = '2025-09-17'

UNION ALL

SELECT 
  'Sep 17 Production Normalized' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id_norm) as unique_patients_norm,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM NORM_PRODUCTION_PRE_SEP26
WHERE activity_date = '2025-09-17'

UNION ALL

SELECT 
  'Sep 17-19 Production Raw' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_name) as unique_patients_raw,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM prod.provider_tasks
WHERE task_date >= '2025-09-17' AND task_date <= '2025-09-19'

UNION ALL

SELECT 
  'Sep 17-19 Production Normalized' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id_norm) as unique_patients_norm,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM NORM_PRODUCTION_PRE_SEP26
WHERE activity_date >= '2025-09-17' AND activity_date <= '2025-09-19';

-- Sample patient name normalization to show the process
.output scripts/outputs/reports/patient_name_normalization_samples.csv
.headers on
SELECT 
  patient_name as raw_name,
  patient_id_norm as normalized_name,
  'Sep 17' as date_sample
FROM NORM_PRODUCTION_PRE_SEP26
WHERE activity_date = '2025-09-17'
  AND (patient_name LIKE 'ZEN-%' OR patient_name LIKE 'PM-%' OR patient_name LIKE 'BlessedCare-%')
ORDER BY raw_name
LIMIT 10;

.output stdout