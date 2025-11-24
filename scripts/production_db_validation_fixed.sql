-- Production Database Comprehensive Validation
-- Fixed schema and ordering issues

.mode csv
.headers on

-- Data Quality Assessment
.output scripts/outputs/reports/production_data_quality.csv
.headers on
SELECT 
  'patients table' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN first_name != '' AND last_name != '' THEN 1 END) as valid_names,
  COUNT(CASE WHEN first_name = '' OR last_name = '' OR first_name IS NULL OR last_name IS NULL THEN 1 END) as invalid_names,
  MIN(created_date) as earliest_created,
  MAX(created_date) as latest_created,
  'Master patient data with quality issues' as notes
FROM patients

UNION ALL

SELECT 
  'patient_panel table' as table_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN first_name != '' AND last_name != '' THEN 1 END) as valid_names,
  0 as invalid_names,
  MIN(created_date) as earliest_created,
  MAX(created_date) as latest_created,
  'Imported/normalized patient data' as notes
FROM patient_panel;

-- September 2025 Production Database Validation
.output scripts/outputs/reports/september_2025_production_validation.csv
.headers on
SELECT 
  'Production Provider Tasks Sept 2025' as data_source,
  'Raw Provider Data' as data_type,
  COUNT(*) as total_records,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(DISTINCT patient_name) as unique_patients,
  COUNT(DISTINCT provider_code) as unique_providers
FROM provider_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Production Coordinator Tasks Sept 2025' as data_source,
  'Raw Coordinator Data' as data_type,
  COUNT(*) as total_records,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(DISTINCT patient_id) as unique_patients,
  COUNT(DISTINCT coordinator_id) as unique_coordinators
FROM coordinator_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Production Patient Panel Sept 2025' as data_source,
  'Normalized Patient Data' as data_type,
  COUNT(*) as total_records,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(DISTINCT first_name || ' ' || last_name) as unique_patients,
  COUNT(DISTINCT provider_id) as unique_providers
FROM patient_panel
WHERE task_date LIKE '2025-09%' OR task_date IS NULL;

-- Normalization Examples from Production Data
.output scripts/outputs/reports/production_normalization_examples.csv
.headers on
SELECT * FROM (
  SELECT 
    'Provider Task Name (Raw)' as data_type,
    patient_name as raw_patient_name,
    NULL as normalized_name,
    NULL as date_of_birth,
    provider_code,
    task_date,
    'provider_tasks' as source_table
  FROM provider_tasks
  WHERE patient_name LIKE 'ZEN-%' OR patient_name LIKE 'PM-%' OR patient_name LIKE 'BlessedCare-%'
    AND task_date LIKE '2025-09%'

  UNION ALL

  SELECT 
    'Patient Panel Name (Normalized)' as data_type,
    first_name || ' ' || last_name as raw_patient_name,
    first_name || ' ' || last_name as normalized_name,
    date_of_birth,
    provider_name as provider_code,
    task_date,
    'patient_panel' as source_table
  FROM patient_panel
  WHERE (first_name LIKE 'ZEN-%' OR first_name LIKE 'PM-%' OR first_name LIKE 'BlessedCare-%')
    AND (task_date LIKE '2025-09%' OR task_date IS NULL)
)
ORDER BY data_type, raw_patient_name
LIMIT 10;

-- Task Volume Comparison by Date
.output scripts/outputs/reports/task_volume_by_date_sept2025.csv
.headers on
SELECT * FROM (
  SELECT 
    'Provider Tasks' as task_type,
    task_date as activity_date,
    COUNT(*) as task_count,
    COUNT(DISTINCT patient_name) as unique_patients,
    COUNT(DISTINCT provider_code) as unique_providers
  FROM provider_tasks
  WHERE task_date LIKE '2025-09%'
  GROUP BY task_date

  UNION ALL

  SELECT 
    'Coordinator Tasks' as task_type,
    task_date as activity_date,
    COUNT(*) as task_count,
    COUNT(DISTINCT patient_id) as unique_patients,
    COUNT(DISTINCT coordinator_id) as unique_coordinators
  FROM coordinator_tasks
  WHERE task_date LIKE '2025-09%'
  GROUP BY task_date
)
ORDER BY task_type, activity_date;

-- Provider/Coordinator Assignment Analysis
.output scripts/outputs/reports/provider_coordinator_assignments.csv
.headers on
SELECT * FROM (
  SELECT 
    'Provider Assignments' as assignment_type,
    provider_name,
    COUNT(*) as patient_count,
    MIN(task_date) as earliest_task,
    MAX(task_date) as latest_task,
    COUNT(DISTINCT patient_name) as unique_patients
  FROM patient_panel
  WHERE provider_name IS NOT NULL
  GROUP BY provider_name

  UNION ALL

  SELECT 
    'Coordinator Assignments' as assignment_type,
    coordinator_name as provider_name,
    COUNT(*) as patient_count,
    MIN(task_date) as earliest_task,
    MAX(task_date) as latest_task,
    COUNT(DISTINCT first_name || ' ' || last_name) as unique_patients
  FROM patient_panel
  WHERE coordinator_name IS NOT NULL
  GROUP BY coordinator_name
)
ORDER BY assignment_type, patient_count DESC;

.output stdout