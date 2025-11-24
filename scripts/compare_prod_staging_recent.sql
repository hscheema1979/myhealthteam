.mode csv
.headers on

-- Limit window to recent activity (post baseline)
-- Set baseline here; adjust as needed
ATTACH '.\scripts\sheets_data.db' AS sheets;
.output scripts/outputs/reports/provider_rows_missing_in_staging_production_recent.csv
SELECT p.patient_id, p.activity_date
FROM P_PROVIDER_TASKS_EQUIV p
LEFT JOIN NORM_STAGING_PROVIDER_TASKS st
  ON st.patient_id = p.patient_id AND st.activity_date = p.activity_date
WHERE p.activity_date >= '2025-09-26'
  AND st.activity_date IS NULL;
.output stdout

.output scripts/outputs/reports/provider_rows_missing_in_production_staging_recent.csv
SELECT st.patient_id,
       st.activity_date
FROM NORM_STAGING_PROVIDER_TASKS st
LEFT JOIN P_PROVIDER_TASKS_EQUIV p
  ON p.patient_id = st.patient_id AND p.activity_date = st.activity_date
WHERE st.activity_date >= '2025-09-26'
  AND p.activity_date IS NULL;
.output stdout

.output scripts/outputs/reports/coordinator_rows_missing_in_staging_production_recent.csv
SELECT p.patient_id, p.activity_date
FROM P_COORDINATOR_TASKS_EQUIV p
LEFT JOIN NORM_STAGING_COORDINATOR_TASKS st
  ON st.patient_id = p.patient_id AND st.activity_date = p.activity_date
WHERE p.activity_date >= '2025-09-26'
  AND st.activity_date IS NULL;
.output stdout

.output scripts/outputs/reports/coordinator_rows_missing_in_production_staging_recent.csv
SELECT st.patient_id,
       st.activity_date
FROM NORM_STAGING_COORDINATOR_TASKS st
LEFT JOIN P_COORDINATOR_TASKS_EQUIV p
  ON p.patient_id = st.patient_id AND p.activity_date = st.activity_date
WHERE st.activity_date >= '2025-09-26'
  AND p.activity_date IS NULL;
.output stdout