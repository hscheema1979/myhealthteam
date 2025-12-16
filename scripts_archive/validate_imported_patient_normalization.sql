-- Validate Import Workflow Patient Normalization
-- Compares raw staging data with imported/normalized production data

ATTACH '.\sheets_data.db' AS staging;

.mode csv
.headers on

-- Import Workflow Summary
.output scripts/outputs/reports/import_workflow_summary.csv
.headers on
SELECT 
  'Production patient_panel' as table_name,
  COUNT(*) as total_rows,
  MIN(created_date) as earliest_created,
  MAX(created_date) as latest_created,
  'Normalized patient data' as data_type
FROM patient_panel

UNION ALL

SELECT 
  'Production patients' as table_name,
  COUNT(*) as total_rows,
  MIN(created_date) as earliest_created,
  MAX(created_date) as latest_created,
  'Master patient data' as data_type
FROM patients

UNION ALL

SELECT 
  'Staging SOURCE_PATIENT_DATA' as table_name,
  COUNT(*) as total_rows,
  'N/A' as earliest_created,
  'N/A' as latest_created,
  'Raw patient data' as data_type
FROM staging.SOURCE_PATIENT_DATA;

-- Validate normalization in patient_panel vs raw staging data
.output scripts/outputs/reports/patient_normalization_validation.csv
.headers on
SELECT 
  pp.first_name || ' ' || pp.last_name as normalized_name,
  pp.date_of_birth,
  pp.source_table,
  pp.provider_name,
  pp.coordinator_name,
  'patient_panel' as data_source,
  '2025-09-17 validation' as validation_note
FROM patient_panel pp
WHERE pp.last_first_dob IS NOT NULL
  AND (pp.first_name LIKE 'ZEN-%' OR pp.first_name LIKE 'PM-%' OR pp.first_name LIKE 'BlessedCare-%')
ORDER BY pp.first_name, pp.last_name
LIMIT 10;

-- Check raw staging data for comparison
.output scripts/outputs/reports/patient_normalization_validation.csv
.headers on
SELECT 
  `Pt Name` as normalized_name,
  `LAST FIRST DOB` as date_of_birth,
  'staging_data' as source_table,
  'N/A' as provider_name,
  'N/A' as coordinator_name,
  'SOURCE_PATIENT_DATA' as data_source,
  '2025-09-17 validation' as validation_note
FROM staging.SOURCE_PATIENT_DATA
WHERE `Pt Name` LIKE 'ZEN-%' OR `Pt Name` LIKE 'PM-%' OR `Pt Name` LIKE 'BlessedCare-%'
ORDER BY `Pt Name`
LIMIT 10;

-- Patient panel source analysis
.output scripts/outputs/reports/patient_panel_sources.csv
.headers on
SELECT 
  source_table,
  COUNT(*) as patient_count,
  COUNT(DISTINCT provider_name) as unique_providers,
  COUNT(DISTINCT coordinator_name) as unique_coordinators,
  MIN(created_date) as earliest_import,
  MAX(created_date) as latest_import
FROM patient_panel
GROUP BY source_table
ORDER BY patient_count DESC;

-- Validate September 2025 normalization in tasks
.output scripts/outputs/reports/september_2025_task_normalization.csv
.headers on
SELECT 
  'Production provider_tasks Sept 2025' as data_source,
  COUNT(*) as total_tasks,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date
FROM provider_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Production coordinator_tasks Sept 2025' as data_source,
  COUNT(*) as total_tasks,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date
FROM coordinator_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Staging staging_provider_tasks Sept 2025' as data_source,
  COUNT(*) as total_tasks,
  MIN(activity_date) as earliest_date,
  MAX(activity_date) as latest_date
FROM staging.staging_provider_tasks
WHERE activity_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Staging staging_coordinator_tasks Sept 2025' as data_source,
  COUNT(*) as total_tasks,
  MIN(activity_date) as earliest_date,
  MAX(activity_date) as latest_date
FROM staging.staging_coordinator_tasks
WHERE activity_date LIKE '2025-09%';

.output stdout