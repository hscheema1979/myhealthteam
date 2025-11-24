-- Staging vs Production Database Comparison
-- Direct comparison of raw vs normalized data

ATTACH '.\sheets_data.db' AS staging;

.mode csv
.headers on

-- Database Summary Comparison
.output scripts/outputs/reports/staging_vs_production_summary.csv
.headers on
SELECT 
  'Production Provider Tasks' as database,
  'Raw Task Data' as data_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_name) as unique_patients,
  COUNT(DISTINCT provider_name) as unique_providers,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  'Normalized system' as status
FROM provider_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Production Coordinator Tasks' as database,
  'Raw Task Data' as data_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  COUNT(DISTINCT coordinator_id) as unique_providers,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  'Normalized system' as status
FROM coordinator_tasks
WHERE task_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Production Patient Panel' as database,
  'Normalized Patient Data' as data_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT first_name || ' ' || last_name) as unique_patients,
  COUNT(DISTINCT provider_name) as unique_providers,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  'Import result' as status
FROM patient_panel

UNION ALL

SELECT 
  'Staging Provider Tasks' as database,
  'Raw Sheet Data' as data_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_name_raw) as unique_patients,
  COUNT(DISTINCT provider_code) as unique_providers,
  MIN(activity_date) as earliest_date,
  MAX(activity_date) as latest_date,
  'Raw source' as status
FROM staging.staging_provider_tasks
WHERE activity_date LIKE '2025-09%'

UNION ALL

SELECT 
  'Staging Patient Data' as database,
  'Raw Sheet Data' as data_type,
  COUNT(*) as total_rows,
  COUNT(DISTINCT `Pt Name`) as unique_patients,
  'N/A' as unique_providers,
  'N/A' as earliest_date,
  'N/A' as latest_date,
  'Raw source' as status
FROM staging.SOURCE_PATIENT_DATA;

-- September 2025 Date Range Comparison
.output scripts/outputs/reports/sept_2025_date_comparison.csv
.headers on
SELECT 
  'Production Provider Tasks Sept 2025' as source,
  COUNT(*) as task_count,
  MIN(task_date) as start_date,
  MAX(task_date) as end_date,
  COUNT(DISTINCT patient_name) as unique_patients
FROM provider_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'

UNION ALL

SELECT 
  'Production Coordinator Tasks Sept 2025' as source,
  COUNT(*) as task_count,
  MIN(task_date) as start_date,
  MAX(task_date) as end_date,
  COUNT(DISTINCT patient_id) as unique_patients
FROM coordinator_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'

UNION ALL

SELECT 
  'Staging Provider Tasks Sept 2025' as source,
  COUNT(*) as task_count,
  MIN(activity_date) as start_date,
  MAX(activity_date) as end_date,
  COUNT(DISTINCT patient_name_raw) as unique_patients
FROM staging.staging_provider_tasks
WHERE activity_date >= '2025-09-02' AND activity_date <= '2025-09-26'

UNION ALL

SELECT 
  'Staging Provider Tasks Sept 26-30 only' as source,
  COUNT(*) as task_count,
  MIN(activity_date) as start_date,
  MAX(activity_date) as end_date,
  COUNT(DISTINCT patient_name_raw) as unique_patients
FROM staging.staging_provider_tasks
WHERE activity_date >= '2025-09-26' AND activity_date <= '2025-09-30';

-- Raw vs Normalized Patient Name Comparison
.output scripts/outputs/reports/raw_vs_normalized_names.csv
.headers on
SELECT * FROM (
  -- Production provider task raw names
  SELECT 
    'Production Provider Task' as data_source,
    patient_name as raw_name,
    NULL as normalized_name,
    provider_name,
    task_date,
    'Raw production data' as source_type
  FROM provider_tasks
  WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'
    AND patient_name LIKE '%MARIA%' OR patient_name LIKE '%JUAN%' OR patient_name LIKE '%JOSÉ%'
  
  UNION ALL
  
  -- Production patient panel normalized names
  SELECT 
    'Production Patient Panel' as data_source,
    NULL as raw_name,
    first_name || ' ' || last_name as normalized_name,
    provider_name,
    task_date,
    'Normalized production data' as source_type
  FROM patient_panel
  WHERE (first_name LIKE '%MARIA%' OR first_name LIKE '%JUAN%' OR first_name LIKE '%JOSÉ%')
    AND (task_date >= '2025-09-02' AND task_date <= '2025-09-26' OR task_date IS NULL)
  
  UNION ALL
  
  -- Staging provider task raw names
  SELECT 
    'Staging Provider Task' as data_source,
    patient_name_raw as raw_name,
    patient_id as normalized_name,
    provider_code,
    activity_date,
    'Raw staging data' as source_type
  FROM staging.staging_provider_tasks
  WHERE activity_date >= '2025-09-02' AND activity_date <= '2025-09-26'
    AND (patient_name_raw LIKE '%MARIA%' OR patient_name_raw LIKE '%JUAN%' OR patient_name_raw LIKE '%JOSÉ%')
  
  UNION ALL
  
  -- Staging patient data raw names
  SELECT 
    'Staging Patient Data' as data_source,
    `Pt Name` as raw_name,
    `LAST FIRST DOB` as normalized_name,
    NULL as provider_name,
    NULL as task_date,
    'Raw staging sheet data' as source_type
  FROM staging.SOURCE_PATIENT_DATA
  WHERE `Pt Name` LIKE '%MARIA%' OR `Pt Name` LIKE '%JUAN%' OR `Pt Name` LIKE '%JOSÉ%'
)
ORDER BY data_source, task_date, raw_name
LIMIT 20;

-- Data Coverage Analysis
.output scripts/outputs/reports/data_coverage_analysis.csv
.headers on
SELECT 
  'Production Complete Sept Coverage' as coverage_type,
  'Sept 1-30 Provider Tasks' as description,
  COUNT(*) as total_records,
  '199 provider tasks + 2913 coordinator tasks' as details,
  'Complete data' as status
FROM (
  SELECT 1 FROM provider_tasks WHERE task_date LIKE '2025-09-%'
  UNION
  SELECT 1 FROM coordinator_tasks WHERE task_date LIKE '2025-09-%'
)

UNION ALL

SELECT 
  'Staging Limited Sept Coverage' as coverage_type,
  'Sept 26-30 Provider Tasks Only' as description,
  COUNT(*) as total_records,
  '34 provider tasks, 0 coordinator tasks' as details,
  'Partial data (import design)' as status
FROM (
  SELECT 1 FROM staging.staging_provider_tasks WHERE activity_date LIKE '2025-09-%'
)

UNION ALL

SELECT 
  'Staging Patient Data Coverage' as coverage_type,
  'SOURCE_PATIENT_DATA' as description,
  COUNT(*) as total_records,
  '621 patients in raw sheet format' as details,
  'Source data for import' as status
FROM staging.SOURCE_PATIENT_DATA;

-- Provider Code Comparison
.output scripts/outputs/reports/provider_code_comparison.csv
.headers on
SELECT * FROM (
  SELECT 
    'Production Provider Names' as source_type,
    provider_name as code_or_name,
    COUNT(*) as patient_count,
    'Clean provider names' as status
  FROM patient_panel
  WHERE provider_name IS NOT NULL
  GROUP BY provider_name
  
  UNION ALL
  
  SELECT 
    'Staging Provider Codes' as source_type,
    provider_code as code_or_name,
    COUNT(*) as patient_count,
    'Raw provider codes' as status
  FROM staging.staging_provider_tasks
  WHERE provider_code IS NOT NULL
  GROUP BY provider_code
)
ORDER BY source_type, patient_count DESC;

.output stdout