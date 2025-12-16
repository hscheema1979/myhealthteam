-- Complete validation: BOTH coordinator AND provider tasks for Sep 17, 2025
-- Shows normalization works for both task types

.mode csv
.headers on

-- September 17 Provider Tasks Summary
.output scripts/outputs/reports/sep_17_complete_validation.csv
.headers on
SELECT 
  'Provider Tasks - Raw' as dataset_type,
  task_date,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_name) as unique_patients
FROM provider_tasks
WHERE task_date = '2025-09-17'
GROUP BY task_date;

.output scripts/outputs/reports/sep_17_complete_validation.csv
.headers on
SELECT 
  'Provider Tasks - Normalized' as dataset_type,
  task_date,
  COUNT(*) as total_rows,
  COUNT(DISTINCT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', ''))) as unique_patients
FROM provider_tasks
WHERE task_date = '2025-09-17'
GROUP BY task_date;

.output scripts/outputs/reports/sep_17_complete_validation.csv
.headers on
SELECT 
  'Coordinator Tasks - Raw' as dataset_type,
  task_date,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients
FROM coordinator_tasks
WHERE task_date = '2025-09-17'
GROUP BY task_date;

.output scripts/outputs/reports/sep_17_complete_validation.csv
.headers on
SELECT 
  'Coordinator Tasks - Normalized' as dataset_type,
  task_date,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients
FROM coordinator_tasks
WHERE task_date = '2025-09-17'
GROUP BY task_date;

-- Sample data comparison for both task types
.output scripts/outputs/reports/sep_17_both_tasks_samples.csv
.headers on
SELECT 
  'PROVIDER_RAW' as task_type,
  patient_name as raw_name,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS normalized_name,
  provider_name as staff_name,
  task_date
FROM provider_tasks
WHERE task_date = '2025-09-17'
ORDER BY raw_name
LIMIT 5;

.output scripts/outputs/reports/sep_17_both_tasks_samples.csv
.headers on
SELECT 
  'COORDINATOR_RAW' as task_type,
  patient_id as raw_name,
  patient_id as normalized_name,
  coordinator_id as staff_name,
  task_date
FROM coordinator_tasks
WHERE task_date = '2025-09-17'
ORDER BY raw_name
LIMIT 5;

-- Cross-validation: Check for overlapping patients between provider and coordinator tasks
.output scripts/outputs/reports/sep_17_patient_overlap_analysis.csv
.headers on
SELECT 
  'Provider Patients (Sep 17)' as category,
  COUNT(DISTINCT patient_name) as raw_patients,
  COUNT(DISTINCT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', ''))) as normalized_patients
FROM provider_tasks
WHERE task_date = '2025-09-17'

UNION ALL

SELECT 
  'Coordinator Patients (Sep 17)' as category,
  COUNT(DISTINCT patient_id) as raw_patients,
  COUNT(DISTINCT patient_id) as normalized_patients
FROM coordinator_tasks
WHERE task_date = '2025-09-17';

.output stdout