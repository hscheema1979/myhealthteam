-- Production Database Simple Validation
-- September 2025 Normalization Check

.mode csv
.headers on

-- Data Summary
.output scripts/outputs/reports/production_db_summary.csv
.headers on
SELECT 
  'patients table' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN first_name != '' AND last_name != '' THEN 1 END) as valid_names,
  MIN(created_date) as earliest_date,
  MAX(created_date) as latest_date
FROM patients

UNION ALL

SELECT 
  'patient_panel table' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN first_name != '' AND last_name != '' THEN 1 END) as valid_names,
  MIN(created_date) as earliest_date,
  MAX(created_date) as latest_date
FROM patient_panel

UNION ALL

SELECT 
  'provider_tasks table' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN patient_name IS NOT NULL AND patient_name != '' THEN 1 END) as valid_names,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date
FROM provider_tasks

UNION ALL

SELECT 
  'coordinator_tasks table' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN patient_id IS NOT NULL AND patient_id != '' THEN 1 END) as valid_names,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date
FROM coordinator_tasks;

-- September 2025 Task Validation
.output scripts/outputs/reports/sept2025_validation.csv
.headers on
SELECT 
  'Provider Tasks Sept 2025' as task_type,
  COUNT(*) as total_tasks,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(DISTINCT patient_name) as unique_patients,
  COUNT(DISTINCT provider_name) as unique_providers
FROM provider_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Coordinator Tasks Sept 2025' as task_type,
  COUNT(*) as total_tasks,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(DISTINCT patient_id) as unique_patients,
  COUNT(DISTINCT coordinator_id) as unique_coordinators
FROM coordinator_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Patient Panel Sept 2025' as task_type,
  COUNT(*) as total_patients,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(DISTINCT first_name || ' ' || last_name) as unique_patients,
  COUNT(DISTINCT provider_name) as unique_providers
FROM patient_panel
WHERE task_date LIKE '2025-09%' OR task_date IS NULL;

-- Normalization Examples
.output scripts/outputs/reports/normalization_examples_production.csv
.headers on
SELECT * FROM (
  SELECT 
    'Provider Task Raw' as data_type,
    patient_name as patient_name,
    NULL as provider_name,
    task_date,
    'raw_data' as source
  FROM provider_tasks
  WHERE patient_name LIKE 'ZEN-%' OR patient_name LIKE 'PM-%' OR patient_name LIKE 'BlessedCare-%'
    AND task_date LIKE '2025-09%'
  
  UNION ALL
  
  SELECT 
    'Patient Panel Normalized' as data_type,
    first_name || ' ' || last_name as patient_name,
    provider_name,
    task_date,
    'normalized_data' as source
  FROM patient_panel
  WHERE (first_name LIKE 'ZEN-%' OR first_name LIKE 'PM-%' OR first_name LIKE 'BlessedCare-%')
    AND (task_date LIKE '2025-09%' OR task_date IS NULL)
)
ORDER BY data_type, patient_name
LIMIT 10;

-- Provider/Coordinator Assignments
.output scripts/outputs/reports/assignments_production.csv
.headers on
SELECT 
  provider_name,
  COUNT(*) as patient_count,
  COUNT(DISTINCT first_name || ' ' || last_name) as unique_patients,
  MIN(task_date) as earliest_task,
  MAX(task_date) as latest_task
FROM patient_panel
WHERE provider_name IS NOT NULL
GROUP BY provider_name
ORDER BY patient_count DESC;

.output stdout