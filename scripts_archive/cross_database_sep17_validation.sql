-- CRITICAL: Cross-database validation production.db vs sheets_data.db for Sep 17
-- This proves the staging database has NO pre-9/26 data, only production has it

ATTACH '.\sheets_data.db' AS staging;

.mode csv
.headers on

-- Cross-database comparison for September 17, 2025
.output scripts/outputs/reports/cross_db_sep17_validation.csv
.headers on
SELECT 
  'Production Provider Tasks (Sep 17)' as database,
  COUNT(*) as total_rows,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM provider_tasks
WHERE task_date = '2025-09-17'

UNION ALL

SELECT 
  'Production Coordinator Tasks (Sep 17)' as database,
  COUNT(*) as total_rows,
  MIN(task_date) as min_date,
  MAX(task_date) as max_date
FROM coordinator_tasks
WHERE task_date = '2025-09-17'

UNION ALL

SELECT 
  'Staging Provider Tasks (Sep 17)' as database,
  COUNT(*) as total_rows,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM staging.staging_provider_tasks
WHERE activity_date = '2025-09-17'

UNION ALL

SELECT 
  'Staging Coordinator Tasks (Sep 17)' as database,
  COUNT(*) as total_rows,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM staging.staging_coordinator_tasks
WHERE activity_date = '2025-09-17';

-- Date range comparison: what data exists in each database
.output scripts/outputs/reports/date_range_comparison.csv
.headers on
SELECT 
  'Production Provider Tasks' as table_name,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(*) as total_rows
FROM provider_tasks

UNION ALL

SELECT 
  'Production Coordinator Tasks' as table_name,
  MIN(task_date) as earliest_date,
  MAX(task_date) as latest_date,
  COUNT(*) as total_rows
FROM coordinator_tasks

UNION ALL

SELECT 
  'Staging Provider Tasks' as table_name,
  MIN(activity_date) as earliest_date,
  MAX(activity_date) as latest_date,
  COUNT(*) as total_rows
FROM staging.staging_provider_tasks

UNION ALL

SELECT 
  'Staging Coordinator Tasks' as table_name,
  MIN(activity_date) as earliest_date,
  MAX(activity_date) as latest_date,
  COUNT(*) as total_rows
FROM staging.staging_coordinator_tasks;

-- Validate normalization alignment: compare Sep 26 data that SHOULD exist in both
.output scripts/outputs/reports/sep26_alignment_check.csv
.headers on
SELECT 
  'Production Provider (Sep 26)' as source,
  patient_name as raw_patient_id,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS normalized_patient_id,
  task_date
FROM provider_tasks
WHERE task_date = '2025-09-26'
ORDER BY raw_patient_id
LIMIT 5;

.output scripts/outputs/reports/sep26_alignment_check.csv
.headers on
SELECT 
  'Staging Provider (Sep 26)' as source,
  patient_name_raw as raw_patient_id,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS normalized_patient_id,
  activity_date
FROM staging.staging_provider_tasks
WHERE activity_date = '2025-09-26'
ORDER BY raw_patient_id
LIMIT 5;

.output stdout