.mode csv
.headers on

-- A) Latest task date vs panel last_visit_date mismatches
.output outputs/reports/staging_panel_vs_tasks_date_mismatches.csv
WITH norm_tasks AS (
  SELECT REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
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
  SELECT REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
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
  SELECT REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
         activity_date,
         TRIM(provider_code) AS provider_code
  FROM staging_provider_tasks
  WHERE activity_date IS NOT NULL
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
         LOWER(COALESCE(spp.provider_name,'')) AS provider_lower
  FROM staging_patient_panel spp
), clean_panel AS (
  SELECT patient_id,
         TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(provider_lower, 'md',''), 'np',''), 'pa',''), 'zz',''), '.', ''), '  ', ' ')) AS provider_name_norm
  FROM norm_panel
), norm_task_provider AS (
  SELECT ltp.patient_id,
         TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(COALESCE(ltp.provider_code,'')), 'md',''), 'np',''), 'pa',''), 'zz',''), '.', ''), '  ', ' ')) AS provider_code_norm
  FROM latest_task_provider ltp
)
SELECT ntp.patient_id,
       ntp.provider_code_norm AS latest_task_provider_code,
       spp.provider_name AS panel_provider_name,
       CASE
         WHEN ntp.provider_code_norm = cp.provider_name_norm THEN 'OK'
         ELSE 'PROVIDER_NAME_MISMATCH'
       END AS provider_alignment
FROM norm_task_provider ntp
LEFT JOIN staging_patient_panel spp ON spp.patient_id = ntp.patient_id
LEFT JOIN clean_panel cp ON cp.patient_id = ntp.patient_id
WHERE COALESCE(ntp.provider_code_norm,'') <> COALESCE(cp.provider_name_norm,'');
.output stdout

-- D) Patients present in tasks but missing in panel
.output outputs/reports/staging_tasks_without_panel.csv
WITH norm_tasks AS (
  SELECT DISTINCT REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id
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
  SELECT DISTINCT REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id
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
  SELECT REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE("Pt Name", ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
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