-- September 2-26, 2025 Normalization Validation
-- Focus on specific date range requested by user

.mode csv
.headers on

-- September 2-26 Task Summary
.output scripts/outputs/reports/sept_2_to_26_task_summary.csv
.headers on
SELECT 
  'Provider Tasks (Raw)' as data_type,
  COUNT(*) as total_tasks,
  COUNT(DISTINCT patient_name) as unique_patients,
  COUNT(DISTINCT provider_name) as unique_providers,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  'Raw patient names with potential prefixes' as data_quality
FROM provider_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'

UNION ALL

SELECT 
  'Coordinator Tasks (Raw)' as data_type,
  COUNT(*) as total_tasks,
  COUNT(DISTINCT patient_id) as unique_patients,
  COUNT(DISTINCT coordinator_id) as unique_coordinators,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  'Raw patient IDs' as data_quality
FROM coordinator_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'

UNION ALL

SELECT 
  'Patient Panel (Normalized)' as data_type,
  COUNT(*) as total_patients,
  COUNT(DISTINCT first_name || ' ' || last_name) as unique_patients,
  COUNT(DISTINCT provider_name) as unique_providers,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  'Clean normalized patient names' as data_quality
FROM patient_panel
WHERE (task_date >= '2025-09-02' AND task_date <= '2025-09-26') OR task_date IS NULL;

-- Raw Patient Names from Provider Tasks (Sept 2-26)
.output scripts/outputs/reports/provider_tasks_raw_patients_sept_2_26.csv
.headers on
SELECT 
  patient_name as raw_patient_name,
  provider_name,
  task_date,
  minutes_of_service,
  billing_code,
  COUNT(*) as task_count,
  'provider_tasks' as source_table,
  'Raw data with potential normalization needed' as data_type
FROM provider_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'
  AND patient_name LIKE 'ZEN-%' OR patient_name LIKE 'PM-%' OR patient_name LIKE 'BlessedCare-%'
GROUP BY patient_name, provider_name
ORDER BY patient_name
LIMIT 20;

-- Matched Normalized Patient Names from Patient Panel
.output scripts/outputs/reports/patient_panel_normalized_sept_2_26.csv
.headers on
SELECT 
  first_name || ' ' || last_name as normalized_patient_name,
  provider_name as assigned_provider,
  date_of_birth,
  'patient_panel' as source_table,
  'Normalized clean data' as data_type
FROM patient_panel
WHERE (first_name LIKE 'ZEN-%' OR first_name LIKE 'PM-%' OR first_name LIKE 'BlessedCare-%')
  AND (task_date >= '2025-09-02' AND task_date <= '2025-09-26' OR task_date IS NULL)
ORDER BY first_name, last_name
LIMIT 20;

-- Direct Name Matching Analysis
.output scripts/outputs/reports/direct_name_matching_sept_2_26.csv
.headers on
SELECT 
  pt.patient_name as raw_provider_task_name,
  pp.first_name || ' ' || pp.last_name as normalized_patient_panel_name,
  pp.date_of_birth,
  pt.provider_name as task_provider,
  pp.provider_name as panel_provider,
  pt.task_date,
  'Direct match found' as match_status
FROM provider_tasks pt
INNER JOIN patient_panel pp ON pt.patient_name = pp.first_name || ' ' || pp.last_name
WHERE pt.task_date >= '2025-09-02' AND pt.task_date <= '2025-09-26'
  AND (pp.task_date >= '2025-09-02' AND pp.task_date <= '2025-09-26' OR pp.task_date IS NULL)
ORDER BY pt.patient_name
LIMIT 10;

-- Patient Coverage Analysis for Sept 2-26
.output scripts/outputs/reports/patient_coverage_sept_2_26.csv
.headers on
SELECT 
  'Provider Tasks Patients' as category,
  COUNT(DISTINCT patient_name) as patient_count,
  'Raw patient names from tasks' as source
FROM provider_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'

UNION ALL

SELECT 
  'Coordinator Tasks Patients' as category,
  COUNT(DISTINCT patient_id) as patient_count,
  'Raw patient IDs from tasks' as source
FROM coordinator_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'

UNION ALL

SELECT 
  'Patient Panel Patients' as category,
  COUNT(DISTINCT first_name || ' ' || last_name) as patient_count,
  'Normalized patient names' as source
FROM patient_panel
WHERE (task_date >= '2025-09-02' AND task_date <= '2025-09-26') OR task_date IS NULL;

-- Daily Task Volume Sept 2-26
.output scripts/outputs/reports/daily_task_volume_sept_2_26.csv
.headers on
SELECT * FROM (
  SELECT 
    task_date,
    'Provider Tasks' as task_type,
    COUNT(*) as task_count,
    COUNT(DISTINCT patient_name) as unique_patients,
    COUNT(DISTINCT provider_name) as unique_providers
  FROM provider_tasks
  WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'
  GROUP BY task_date

  UNION ALL

  SELECT 
    task_date,
    'Coordinator Tasks' as task_type,
    COUNT(*) as task_count,
    COUNT(DISTINCT patient_id) as unique_patients,
    COUNT(DISTINCT coordinator_id) as unique_providers
  FROM coordinator_tasks
  WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'
  GROUP BY task_date
)
ORDER BY task_date, task_type;

-- Provider Activity Sept 2-26
.output scripts/outputs/reports/provider_activity_sept_2_26.csv
.headers on
SELECT 
  provider_name,
  COUNT(*) as total_tasks,
  COUNT(DISTINCT patient_name) as unique_patients,
  SUM(minutes_of_service) as total_minutes,
  MIN(task_date) as first_task_date,
  MAX(task_date) as last_task_date,
  'Provider task activity' as activity_type
FROM provider_tasks
WHERE task_date >= '2025-09-02' AND task_date <= '2025-09-26'
GROUP BY provider_name
ORDER BY total_tasks DESC;

.output stdout