-- Validate normalization on PRE-9/26 dates (like 9/17) within production database
-- This proves the normalization logic works consistently across all dates

.mode csv
.headers on

-- September 17 validation (pre-normalization date as requested)
.output scripts/outputs/reports/sep_17_2025_raw_vs_normalized.csv
.headers on
SELECT 
  'RAW' as data_type,
  patient_name as patient_name_raw,
  task_date as activity_date,
  provider_name as provider_code,
  billing_code as service
FROM provider_tasks
WHERE task_date = '2025-09-17'
ORDER BY task_date, patient_name
LIMIT 10;

.output scripts/outputs/reports/sep_17_2025_raw_vs_normalized.csv
.headers on
SELECT 
  'NORMALIZED' as data_type,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm,
  task_date as activity_date,
  provider_name as provider_code,
  billing_code as service
FROM provider_tasks
WHERE task_date = '2025-09-17'
ORDER BY task_date, patient_id_norm
LIMIT 10;

-- Multi-day summary showing normalization consistency
.output scripts/outputs/reports/pre_sep_26_normalization_summary.csv
.headers on
SELECT 
  'Sep 17 Raw' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_name) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM provider_tasks
WHERE task_date = '2025-09-17'

UNION ALL

SELECT 
  'Sep 17 Normalized' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', ''))) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM provider_tasks
WHERE task_date = '2025-09-17'

UNION ALL

SELECT 
  'Sep 17-19 Raw' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_name) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM provider_tasks
WHERE task_date >= '2025-09-17' AND task_date <= '2025-09-19'

UNION ALL

SELECT 
  'Sep 17-19 Normalized' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', ''))) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM provider_tasks
WHERE task_date >= '2025-09-17' AND task_date <= '2025-09-19';

-- Sample patient name normalization showing the prefix removal
.output scripts/outputs/reports/patient_name_normalization_samples.csv
.headers on
SELECT 
  patient_name as raw_name,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS normalized_name,
  task_date as activity_date,
  'Sep 17' as date_sample
FROM provider_tasks
WHERE task_date = '2025-09-17'
  AND (patient_name LIKE 'ZEN-%' OR patient_name LIKE 'PM-%' OR patient_name LIKE 'BlessedCare-%')
ORDER BY raw_name
LIMIT 10;

.output stdout