-- Validate September 2025 normalization: staging vs production comparison
-- Two-day window (Sep 26-30) for proper comparison

ATTACH '.\production.db' AS prod;

.mode csv
.headers on

.param set :start_date '2025-09-26'
.param set :end_date '2025-09-30'

-- Provider tasks validation: staging vs production
.output scripts/outputs/reports/provider_tasks_sept_26_30_validation.csv
SELECT 
  'STAGING' as source,
  patient_id,
  activity_date as task_date,
  provider_code,
  service,
  minutes_of_service
FROM NORM_STAGING_PROVIDER_TASKS_SEPT
WHERE activity_date >= :start_date AND activity_date <= :end_date
ORDER BY activity_date, patient_id;

-- Production provider tasks for same window
.output scripts/outputs/reports/provider_tasks_sept_26_30_validation.csv
.headers on
SELECT 
  'PRODUCTION' as source,
  patient_id,
  task_date,
  provider_name as provider_code,
  billing_code as service,
  minutes_of_service
FROM prod.provider_tasks
WHERE task_date >= :start_date AND task_date <= :end_date
ORDER BY task_date, patient_id;

-- Count comparison summary
.output scripts/outputs/reports/sept_26_30_comparison_summary.csv
.headers on
SELECT 
  'Staging Provider Tasks' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM NORM_STAGING_PROVIDER_TASKS_SEPT
WHERE activity_date >= :start_date AND activity_date <= :end_date
UNION ALL
SELECT 
  'Production Provider Tasks' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM prod.provider_tasks
WHERE task_date >= :start_date AND task_date <= :end_date;

-- Check production coordinator tasks for comparison
.output scripts/outputs/reports/coordinator_tasks_sept_26_30_comparison.csv
.headers on
SELECT 
  'Production Coordinator Tasks' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM prod.coordinator_tasks
WHERE task_date >= :start_date AND task_date <= :end_date;

.output stdout