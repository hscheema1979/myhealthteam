-- Create normalized views for September 2025 staging data validation
-- Fix coordinator tasks activity_date derivation and ensure full coverage

-- Drop existing normalized views
DROP VIEW IF EXISTS NORM_STAGING_PROVIDER_TASKS;
DROP VIEW IF EXISTS NORM_STAGING_COORDINATOR_TASKS;
DROP VIEW IF EXISTS NORM_SHEETS_PROVIDER_TASKS;
DROP VIEW IF EXISTS NORM_SHEETS_COORDINATOR_TASKS;

-- Staging provider tasks: normalized patient_id (September 2025 included)
DROP VIEW IF EXISTS NORM_STAGING_PROVIDER_TASKS_SEPT;
CREATE VIEW NORM_STAGING_PROVIDER_TASKS_SEPT AS
SELECT
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
  activity_date AS activity_date,
  provider_code AS provider_code,
  service AS service,
  minutes_of_service AS minutes_of_service,
  notes AS notes
FROM staging_provider_tasks
WHERE activity_date IS NOT NULL
  AND activity_date >= '2025-09-01';

-- Staging coordinator tasks: fix activity_date derivation (September 2025 included)
-- Derive activity_date from year_month when activity_date is NULL
DROP VIEW IF EXISTS NORM_STAGING_COORDINATOR_TASKS_SEPT;
CREATE VIEW NORM_STAGING_COORDINATOR_TASKS_SEPT AS
SELECT
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
  COALESCE(activity_date, 
    CASE 
      WHEN year_month IS NOT NULL AND year_month != '' AND length(year_month) = 7
      THEN substr(year_month, 1, 4) || '-' || substr(year_month, 6, 2) || '-01'
      ELSE NULL
    END) AS activity_date,
  staff_code AS staff_code,
  task_type AS task_type,
  notes AS notes,
  minutes_raw AS minutes_raw
FROM staging_coordinator_tasks
WHERE COALESCE(activity_date, 
    CASE 
      WHEN year_month IS NOT NULL AND year_month != '' AND length(year_month) = 7
      THEN substr(year_month, 1, 4) || '-' || substr(year_month, 6, 2) || '-01'
      ELSE NULL
    END) IS NOT NULL
  AND COALESCE(activity_date, 
    CASE 
      WHEN year_month IS NOT NULL AND year_month != '' AND length(year_month) = 7
      THEN substr(year_month, 1, 4) || '-' || substr(year_month, 6, 2) || '-01'
      ELSE NULL
    END) >= '2025-09-01';

-- September 2025 Provider Summary for validation
CREATE TEMP TABLE SEPT_2025_PROVIDER_SUMMARY AS
SELECT 
  'Staging Provider Tasks' as source,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM NORM_STAGING_PROVIDER_TASKS_SEPT
WHERE activity_date >= '2025-09-01' AND activity_date <= '2025-09-30';

CREATE TEMP TABLE SEPT_2025_COORDINATOR_SUMMARY AS
SELECT 
  'Staging Coordinator Tasks' as source,
  COUNT(*) as total_rows,
  COUNT(DISTINCT patient_id) as unique_patients,
  MIN(activity_date) as min_date,
  MAX(activity_date) as max_date
FROM NORM_STAGING_COORDINATOR_TASKS_SEPT
WHERE activity_date >= '2025-09-01' AND activity_date <= '2025-09-30';

-- Output September 2025 validation summary
.output scripts/outputs/reports/september_2025_staging_validation_summary.csv
.headers on
SELECT * FROM SEPT_2025_PROVIDER_SUMMARY
UNION ALL
SELECT * FROM SEPT_2025_COORDINATOR_SUMMARY;
.output stdout

-- Sample of normalized September data for verification
.output scripts/outputs/reports/september_2025_normalized_samples.csv
.headers on
SELECT 'Provider' as task_type, patient_id, activity_date, provider_code, service 
FROM NORM_STAGING_PROVIDER_TASKS_SEPT 
WHERE activity_date >= '2025-09-20' AND activity_date <= '2025-09-30'
LIMIT 10;
.output stdout

.output scripts/outputs/reports/september_2025_normalized_samples.csv
.headers on
SELECT 'Coordinator' as task_type, patient_id, activity_date, staff_code, task_type as task_name
FROM NORM_STAGING_COORDINATOR_TASKS_SEPT 
WHERE activity_date >= '2025-09-20' AND activity_date <= '2025-09-30'
LIMIT 10;
.output stdout