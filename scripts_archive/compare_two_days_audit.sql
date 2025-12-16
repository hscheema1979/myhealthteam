.mode csv
.headers on

-- Two-day audit dates
.param set :d1 '2025-09-20'
.param set :d2 '2025-09-21'

ATTACH '.\scripts\sheets_data.db' AS sheets;

-- Provider: production → staging (missing in staging)
.output scripts/outputs/reports/provider_prod_missing_in_staging_two_days.csv
SELECT p.patient_id, p.activity_date, p.provider_code_norm AS provider_code, p.service
FROM P_PROVIDER_TASKS_EQUIV p
LEFT JOIN staging_provider_tasks st
  ON TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(st.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) = p.patient_id
 AND st.activity_date = p.activity_date
 AND TRIM(st.service) = TRIM(p.service)
WHERE p.activity_date IN (:d1, :d2)
  AND st.activity_date IS NULL;
.output stdout

-- Provider: staging → production (missing in production)
.output scripts/outputs/reports/provider_staging_missing_in_prod_two_days.csv
SELECT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(st.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
       st.activity_date,
       UPPER(TRIM(st.provider_code)) AS provider_code,
       st.service
FROM staging_provider_tasks st
LEFT JOIN P_PROVIDER_TASKS_EQUIV p
  ON TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(st.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) = p.patient_id
 AND st.activity_date = p.activity_date
 AND TRIM(st.service) = TRIM(p.service)
WHERE st.activity_date IN (:d1, :d2)
  AND p.activity_date IS NULL;
.output stdout

-- Provider: production ↔ sheets (missing in sheets)
.output scripts/outputs/reports/provider_prod_missing_in_sheets_two_days.csv
WITH sheets_provider AS (
  SELECT vp.patient_id, vp.activity_date, UPPER(TRIM(vp.provider_code)) AS provider_code_norm, TRIM(vp.service) AS service
  FROM sheets.V_PROVIDER_TASKS_NORM vp
  WHERE vp.activity_date IN (:d1, :d2)
)
SELECT p.patient_id, p.activity_date, p.provider_code_norm AS provider_code, p.service
FROM P_PROVIDER_TASKS_EQUIV p
LEFT JOIN sheets_provider sp
  ON sp.patient_id = p.patient_id
 AND sp.activity_date = p.activity_date
 AND sp.provider_code_norm = p.provider_code_norm
 AND sp.service = p.service
WHERE p.activity_date IN (:d1, :d2)
  AND sp.activity_date IS NULL;
.output stdout

-- Provider: sheets ↔ production (missing in production)
.output scripts/outputs/reports/provider_sheets_missing_in_prod_two_days.csv
WITH sheets_provider AS (
  SELECT vp.patient_id, vp.activity_date, UPPER(TRIM(vp.provider_code)) AS provider_code_norm, TRIM(vp.service) AS service
  FROM sheets.V_PROVIDER_TASKS_NORM vp
  WHERE vp.activity_date IN (:d1, :d2)
)
SELECT sp.patient_id, sp.activity_date, sp.provider_code_norm AS provider_code, sp.service
FROM sheets_provider sp
LEFT JOIN P_PROVIDER_TASKS_EQUIV p
  ON p.patient_id = sp.patient_id
 AND p.activity_date = sp.activity_date
 AND p.provider_code_norm = sp.provider_code_norm
 AND p.service = sp.service
WHERE sp.activity_date IN (:d1, :d2)
  AND p.activity_date IS NULL;
.output stdout

-- Coordinator: production → staging (missing in staging)
.output scripts/outputs/reports/coordinator_prod_missing_in_staging_two_days.csv
SELECT p.patient_id, p.activity_date, p.staff_code_norm AS staff_code, p.task_type
FROM P_COORDINATOR_TASKS_EQUIV p
LEFT JOIN staging_coordinator_tasks st
  ON TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(st.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) = p.patient_id
 AND st.activity_date = p.activity_date
 AND UPPER(TRIM(st.staff_code)) = p.staff_code_norm
WHERE p.activity_date IN (:d1, :d2)
  AND st.activity_date IS NULL;
.output stdout

-- Coordinator: staging → production (missing in production)
.output scripts/outputs/reports/coordinator_staging_missing_in_prod_two_days.csv
SELECT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(st.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
       st.activity_date,
       UPPER(TRIM(st.staff_code)) AS staff_code,
       st.task_type
FROM staging_coordinator_tasks st
LEFT JOIN P_COORDINATOR_TASKS_EQUIV p
  ON TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(st.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) = p.patient_id
 AND st.activity_date = p.activity_date
 AND UPPER(TRIM(st.staff_code)) = p.staff_code_norm
WHERE st.activity_date IN (:d1, :d2)
  AND p.activity_date IS NULL;
.output stdout

-- Coordinator: production ↔ sheets (missing in sheets)
.output scripts/outputs/reports/coordinator_prod_missing_in_sheets_two_days.csv
WITH sheets_coord AS (
  SELECT vc.patient_id, vc.activity_date, UPPER(TRIM(vc.staff_code)) AS staff_code_norm, TRIM(vc.task_type) AS task_type
  FROM sheets.V_COORDINATOR_TASKS_NORM vc
  WHERE vc.activity_date IN (:d1, :d2)
)
SELECT p.patient_id, p.activity_date, p.staff_code_norm AS staff_code, p.task_type
FROM P_COORDINATOR_TASKS_EQUIV p
LEFT JOIN sheets_coord sc
  ON sc.patient_id = p.patient_id
 AND sc.activity_date = p.activity_date
 AND sc.staff_code_norm = p.staff_code_norm
 AND sc.task_type = p.task_type
WHERE p.activity_date IN (:d1, :d2)
  AND sc.activity_date IS NULL;
.output stdout

-- Coordinator: sheets ↔ production (missing in production)
.output scripts/outputs/reports/coordinator_sheets_missing_in_prod_two_days.csv
WITH sheets_coord AS (
  SELECT vc.patient_id, vc.activity_date, UPPER(TRIM(vc.staff_code)) AS staff_code_norm, TRIM(vc.task_type) AS task_type
  FROM sheets.V_COORDINATOR_TASKS_NORM vc
  WHERE vc.activity_date IN (:d1, :d2)
)
SELECT sc.patient_id, sc.activity_date, sc.staff_code_norm AS staff_code, sc.task_type
FROM sheets_coord sc
LEFT JOIN P_COORDINATOR_TASKS_EQUIV p
  ON p.patient_id = sc.patient_id
 AND p.activity_date = sc.activity_date
 AND p.staff_code_norm = sc.staff_code_norm
 AND p.task_type = sc.task_type
WHERE sc.activity_date IN (:d1, :d2)
  AND p.activity_date IS NULL;
.output stdout