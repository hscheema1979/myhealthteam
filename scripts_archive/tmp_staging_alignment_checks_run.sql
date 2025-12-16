ATTACH '.\scripts\sheets_data.db' AS staging;
CREATE TEMP VIEW SOURCE_PROVIDER_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_PROVIDER_TASKS_HISTORY;

.mode csv
.headers on

-- A) Latest task date vs panel last_visit_date mismatches
.output outputs/reports/staging_panel_vs_tasks_date_mismatches.csv
WITH norm_tasks AS (
  SELECT REPLACE(patient_name_raw, ',', '') AS patient_id,
         activity_date
  FROM staging_provider_tasks
  WHERE activity_date IS NOT NULL
), latest_task AS (
  SELECT patient_id, MAX(activity_date) AS last_task_date
  FROM norm_tasks
  GROUP BY patient_id
)
SELECT p.patient_id,
       p.provider_name,
       p.coordinator_name,
       p.last_visit_date AS panel_last_visit_date,
       lt.last_task_date AS tasks_last_visit_date,
       CASE WHEN p.last_visit_date = lt.last_task_date THEN 'OK' ELSE 'DATE_MISMATCH' END AS date_alignment
FROM staging_patient_panel p
LEFT JOIN latest_task lt ON lt.patient_id = p.patient_id
WHERE COALESCE(p.last_visit_date,'') <> COALESCE(lt.last_task_date,'');
.output stdout

-- B) Detailed per-patient latest task services vs panel last_visit_service_type
.output outputs/reports/staging_panel_vs_tasks_service_mismatches.csv
WITH norm_tasks AS (
  SELECT REPLACE(patient_name_raw, ',', '') AS patient_id,
         activity_date,
         service
  FROM staging_provider_tasks
  WHERE activity_date IS NOT NULL
), latest_task AS (
  SELECT patient_id, MAX(activity_date) AS last_task_date
  FROM norm_tasks
  GROUP BY patient_id
), latest_services AS (
  SELECT nt.patient_id,
         nt.activity_date AS last_task_date,
         GROUP_CONCAT(DISTINCT TRIM(nt.service)) AS last_task_services
  FROM norm_tasks nt
  JOIN latest_task lt ON lt.patient_id = nt.patient_id AND lt.last_task_date = nt.activity_date
  GROUP BY nt.patient_id, nt.activity_date
)
SELECT p.patient_id,
       p.provider_name,
       p.coordinator_name,
       p.last_visit_service_type AS panel_last_service_type,
       ls.last_task_services,
       CASE WHEN p.last_visit_service_type = ls.last_task_services THEN 'OK' ELSE 'SERVICE_MISMATCH' END AS service_alignment
FROM staging_patient_panel p
LEFT JOIN latest_services ls ON ls.patient_id = p.patient_id
WHERE COALESCE(p.last_visit_service_type,'') <> COALESCE(ls.last_task_services,'');
.output stdout

-- C) Provider name alignment: latest task provider_code vs panel provider_name (normalized)
.output outputs/reports/staging_provider_name_alignment.csv
WITH norm_tasks AS (
  SELECT REPLACE("Patient Last, First DOB", ',', '') AS patient_id,
         CASE
           WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           ELSE NULL
         END AS activity_date,
         TRIM("Prov") AS provider_code
  FROM SOURCE_PROVIDER_TASKS_HISTORY
  WHERE (CASE
           WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
           ELSE NULL
         END) IS NOT NULL
), latest_task AS (
  SELECT patient_id, MAX(activity_date) AS last_task_date
  FROM norm_tasks
  GROUP BY patient_id
), latest_task_provider AS (
  SELECT nt.patient_id,
         nt.activity_date AS last_task_date,
         nt.provider_code
  FROM norm_tasks nt
  JOIN latest_task lt ON lt.patient_id = nt.patient_id AND lt.last_task_date = nt.activity_date
), norm_panel AS (
  SELECT spp.patient_id,
         TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(COALESCE(spp.provider_name,''))), 'md',''), 'np',''), 'pa',''), 'zz',''), '.', ''), '  ', ' ')) AS provider_name_norm
  FROM staging_patient_panel spp
)
SELECT ltp.patient_id,
       ltp.provider_code AS latest_task_provider_code,
       spp.provider_name AS panel_provider_name,
       CASE
         WHEN TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(COALESCE(ltp.provider_code,''))), 'md',''), 'np',''), 'pa',''), 'zz',''), '.', ''), '  ', ' '))
              = np.provider_name_norm THEN 'OK'
         ELSE 'PROVIDER_NAME_MISMATCH'
       END AS provider_alignment
FROM latest_task_provider ltp
LEFT JOIN staging_patient_panel spp ON spp.patient_id = ltp.patient_id
LEFT JOIN norm_panel np ON np.patient_id = ltp.patient_id
WHERE COALESCE(ltp.provider_code,'') <> COALESCE(spp.provider_name,'');
.output stdout

-- D) Patients present in tasks but missing in panel
.output outputs/reports/staging_tasks_without_panel.csv
WITH norm_tasks AS (
  SELECT DISTINCT REPLACE(patient_name_raw, ',', '') AS patient_id
  FROM staging_provider_tasks
)
SELECT nt.patient_id
FROM norm_tasks nt
LEFT JOIN staging_patient_panel p ON p.patient_id = nt.patient_id
WHERE p.patient_id IS NULL;
.output stdout

-- E) Patients present in panel but no tasks in staging
.output outputs/reports/staging_panel_without_tasks.csv
WITH norm_tasks AS (
  SELECT DISTINCT REPLACE(patient_name_raw, ',', '') AS patient_id
  FROM staging_provider_tasks
)
SELECT p.patient_id
FROM staging_patient_panel p
LEFT JOIN norm_tasks nt ON nt.patient_id = p.patient_id
WHERE nt.patient_id IS NULL;
.output stdout

-- F) Coordinator task presence around latest visit (raw extract)
.output outputs/reports/staging_coordinator_activity_latest_month.csv
WITH visits AS (
  SELECT patient_id,
         last_visit_date,
         substr(last_visit_date,1,7) AS year_month
  FROM staging_patient_visits
), coord AS (
  SELECT REPLACE("Pt Name", ',', '') AS patient_id,
         activity_date,
         staff_code,
         year_month
  FROM staging_coordinator_tasks
)
SELECT v.patient_id,
       v.last_visit_date,
       v.year_month,
       COUNT(*) AS coordinator_tasks_in_visit_month,
       GROUP_CONCAT(DISTINCT TRIM(coord.staff_code)) AS staff_codes
FROM visits v
LEFT JOIN coord ON coord.patient_id = v.patient_id AND coord.year_month = substr(v.last_visit_date,1,7)
GROUP BY v.patient_id, v.last_visit_date, v.year_month;
.output stdout