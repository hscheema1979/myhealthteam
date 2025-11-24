-- Final September 2025 normalization validation
-- Direct comparison without parameter binding issues

ATTACH '.\production.db' AS prod;

.mode csv
.headers on

-- September 2025 staging data summary
.output scripts/outputs/reports/sept_2025_final_validation_summary.csv
SELECT 
  'Staging Provider Tasks (Sept 26-30)' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM NORM_STAGING_PROVIDER_TASKS_SEPT
WHERE activity_date >= '2025-09-26' AND activity_date <= '2025-09-30'

UNION ALL

SELECT 
  'Production Provider Tasks (Sept 26-30)' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM prod.provider_tasks
WHERE task_date >= '2025-09-26' AND task_date <= '2025-09-30'

UNION ALL

SELECT 
  'Production Provider Tasks (All Sept 2025)' as dataset,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM prod.provider_tasks
WHERE task_date >= '2025-09-01' AND task_date <= '2025-09-30';

-- Sample comparison for verification
.output scripts/outputs/reports/sept_2025_sample_comparison.csv
.headers on
SELECT 'STAGING' as source, patient_id, activity_date as task_date, provider_code, service 
FROM NORM_STAGING_PROVIDER_TASKS_SEPT
WHERE activity_date >= '2025-09-26' AND activity_date <= '2025-09-30'
ORDER BY activity_date, patient_id
LIMIT 10;

.output scripts/outputs/reports/sept_2025_sample_comparison.csv
.headers on
SELECT 'PRODUCTION' as source, patient_id, task_date, provider_name as provider_code, billing_code as service 
FROM prod.provider_tasks
WHERE task_date >= '2025-09-26' AND task_date <= '2025-09-30'
ORDER BY task_date, patient_id
LIMIT 10;

.output stdout