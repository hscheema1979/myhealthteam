.mode csv
.headers on

ATTACH '.\scripts\sheets_data.db' AS sheets;

-- 1) Provider tasks: counts by month in staging vs sheets
.output outputs/reports/compare_provider_counts_by_month.csv
WITH staging AS (
  SELECT year_month, COUNT(*) AS cnt
  FROM staging_provider_tasks
  WHERE year_month IS NOT NULL
  GROUP BY year_month
), sheets_norm AS (
  SELECT CASE
    WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
    WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
    ELSE NULL
  END AS year_month
  FROM sheets.SOURCE_PROVIDER_TASKS_HISTORY
), sheets AS (
  SELECT year_month, COUNT(*) AS cnt
  FROM sheets_norm
  WHERE year_month IS NOT NULL
  GROUP BY year_month
)
SELECT year_month, staging_cnt, sheets_cnt, staging_cnt - sheets_cnt AS diff
FROM (
  SELECT s.year_month AS year_month,
         s.cnt AS staging_cnt,
         COALESCE(sh.cnt,0) AS sheets_cnt
  FROM staging s
  LEFT JOIN sheets sh ON sh.year_month = s.year_month
  UNION
  SELECT sh.year_month AS year_month,
         COALESCE(s.cnt,0) AS staging_cnt,
         sh.cnt AS sheets_cnt
  FROM sheets sh
  LEFT JOIN staging s ON s.year_month = sh.year_month
  WHERE s.year_month IS NULL
);
.output stdout

-- 2) Provider tasks: rows present in sheets but missing in staging (normalized key)
.output outputs/reports/provider_rows_missing_in_staging.csv
WITH sheets_provider AS (
  SELECT DISTINCT
         REPLACE("Patient Last, First DOB", ',', '') AS patient_id,
         TRIM("Prov") AS provider_code,
         TRIM("Service") AS service,
         CASE
           WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           ELSE NULL
         END AS activity_date
  FROM sheets.SOURCE_PROVIDER_TASKS_HISTORY
  WHERE "Patient Last, First DOB" IS NOT NULL AND TRIM("Patient Last, First DOB") != ''
), staging_provider AS (
  SELECT DISTINCT
         REPLACE(patient_name_raw, ',', '') AS patient_id,
         TRIM(provider_code) AS provider_code,
         TRIM(service) AS service,
         activity_date
  FROM staging_provider_tasks
  WHERE activity_date IS NOT NULL
)
SELECT sp.patient_id, sp.activity_date, sp.provider_code, sp.service
FROM sheets_provider sp
LEFT JOIN staging_provider st
  ON st.patient_id = sp.patient_id
 AND st.activity_date = sp.activity_date
 AND st.provider_code = sp.provider_code
 AND st.service = sp.service
WHERE st.activity_date IS NULL;
.output stdout

-- 3) Provider tasks: rows present in staging but missing in sheets (normalized key)
.output outputs/reports/provider_rows_missing_in_sheets.csv
WITH sheets_provider AS (
  SELECT DISTINCT
         REPLACE("Patient Last, First DOB", ',', '') AS patient_id,
         TRIM("Prov") AS provider_code,
         TRIM("Service") AS service,
         CASE
           WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           ELSE NULL
         END AS activity_date
  FROM sheets.SOURCE_PROVIDER_TASKS_HISTORY
  WHERE "Patient Last, First DOB" IS NOT NULL AND TRIM("Patient Last, First DOB") != ''
), staging_provider AS (
  SELECT DISTINCT
         REPLACE(patient_name_raw, ',', '') AS patient_id,
         TRIM(provider_code) AS provider_code,
         TRIM(service) AS service,
         activity_date
  FROM staging_provider_tasks
  WHERE activity_date IS NOT NULL
)
SELECT st.patient_id, st.activity_date, st.provider_code, st.service
FROM staging_provider st
LEFT JOIN sheets_provider sp
  ON sp.patient_id = st.patient_id
 AND sp.activity_date = st.activity_date
 AND sp.provider_code = st.provider_code
 AND sp.service = st.service
WHERE sp.activity_date IS NULL;
.output stdout

-- 4) Coordinator tasks: counts by month in staging vs sheets
.output outputs/reports/compare_coordinator_counts_by_month.csv
WITH staging AS (
  SELECT year_month, COUNT(*) AS cnt
  FROM staging_coordinator_tasks
  WHERE year_month IS NOT NULL
  GROUP BY year_month
), sheets_norm AS (
  SELECT CASE
    WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
    WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
    ELSE NULL
  END AS year_month
  FROM sheets.SOURCE_COORDINATOR_TASKS_HISTORY
), sheets AS (
  SELECT year_month, COUNT(*) AS cnt
  FROM sheets_norm
  WHERE year_month IS NOT NULL
  GROUP BY year_month
)
SELECT year_month, staging_cnt, sheets_cnt, staging_cnt - sheets_cnt AS diff
FROM (
  SELECT s.year_month AS year_month,
         s.cnt AS staging_cnt,
         COALESCE(sh.cnt,0) AS sheets_cnt
  FROM staging s
  LEFT JOIN sheets sh ON sh.year_month = s.year_month
  UNION
  SELECT sh.year_month AS year_month,
         COALESCE(s.cnt,0) AS staging_cnt,
         sh.cnt AS sheets_cnt
  FROM sheets sh
  LEFT JOIN staging s ON s.year_month = sh.year_month
  WHERE s.year_month IS NULL
);
.output stdout

-- 5) Coordinator tasks: rows present in sheets but missing in staging (normalized key)
.output outputs/reports/coordinator_rows_missing_in_staging.csv
WITH sheets_coord AS (
  SELECT DISTINCT
         REPLACE("Pt Name", ',', '') AS patient_id,
         TRIM("Staff") AS staff_code,
         TRIM("Type") AS task_type,
         CASE
           WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
           WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
           ELSE NULL
         END AS activity_date
  FROM sheets.SOURCE_COORDINATOR_TASKS_HISTORY
  WHERE "Pt Name" IS NOT NULL AND TRIM("Pt Name") != ''
), staging_coord AS (
  SELECT DISTINCT
         REPLACE(patient_name_raw, ',', '') AS patient_id,
         TRIM(staff_code) AS staff_code,
         TRIM(task_type) AS task_type,
         activity_date
  FROM staging_coordinator_tasks
  WHERE activity_date IS NOT NULL
)
SELECT sc.patient_id, sc.activity_date, sc.staff_code, sc.task_type
FROM sheets_coord sc
LEFT JOIN staging_coord st
  ON st.patient_id = sc.patient_id
 AND st.activity_date = sc.activity_date
 AND st.staff_code = sc.staff_code
 AND st.task_type = sc.task_type
WHERE st.activity_date IS NULL;
.output stdout

-- 6) Coordinator tasks: rows present in staging but missing in sheets (normalized key)
.output outputs/reports/coordinator_rows_missing_in_sheets.csv
WITH sheets_coord AS (
  SELECT DISTINCT
         REPLACE("Pt Name", ',', '') AS patient_id,
         TRIM("Staff") AS staff_code,
         TRIM("Type") AS task_type,
         CASE
           WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
           WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
           ELSE NULL
         END AS activity_date
  FROM sheets.SOURCE_COORDINATOR_TASKS_HISTORY
  WHERE "Pt Name" IS NOT NULL AND TRIM("Pt Name") != ''
), staging_coord AS (
  SELECT DISTINCT
         REPLACE(patient_name_raw, ',', '') AS patient_id,
         TRIM(staff_code) AS staff_code,
         TRIM(task_type) AS task_type,
         activity_date
  FROM staging_coordinator_tasks
  WHERE activity_date IS NOT NULL
)
SELECT st.patient_id, st.activity_date, st.staff_code, st.task_type
FROM staging_coord st
LEFT JOIN sheets_coord sc
  ON sc.patient_id = st.patient_id
 AND sc.activity_date = st.activity_date
 AND sc.staff_code = st.staff_code
 AND sc.task_type = st.task_type
WHERE sc.activity_date IS NULL;
.output stdout

-- 7) Panel presence vs sheets SOURCE_PATIENT_DATA
.output outputs/reports/panel_patients_missing_in_sheets.csv
SELECT p.patient_id
FROM staging_patient_panel p
LEFT JOIN sheets.SOURCE_PATIENT_DATA spd ON spd."LAST FIRST DOB" = p.patient_id
WHERE spd."LAST FIRST DOB" IS NULL;
.output stdout

.output outputs/reports/patients_in_sheets_missing_in_panel.csv
SELECT spd."LAST FIRST DOB" AS patient_id
FROM sheets.SOURCE_PATIENT_DATA spd
LEFT JOIN staging_patient_panel p ON p.patient_id = spd."LAST FIRST DOB"
WHERE p.patient_id IS NULL;
.output stdout