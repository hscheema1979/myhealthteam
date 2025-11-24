-- Compare production staging tables vs normalized views in sheets_data.db
.mode csv
.headers on

ATTACH '.\scripts\sheets_data.db' AS sheets;

-- 1) Provider tasks: rows present in sheets view but missing in staging (normalized join keys)
.output outputs/reports/provider_rows_missing_in_staging_views.csv
WITH sheets_provider AS (
  SELECT DISTINCT
         REPLACE(
           REPLACE(
             REPLACE(
               REPLACE(
                 REPLACE(
                   REPLACE(
                     REPLACE(
                       REPLACE(
                         REPLACE(TRIM(REPLACE(vp.patient_id, ',', ' ')), 'ZEN-', ''),
                         'PM-', ''
                       ),
                       'ZMN-', ''
                     ),
                     'BlessedCare-', ''
                   ),
                   'BLESSEDCARE-', ''
                 ),
                 'BleessedCare-', ''
               ),
               'BLEESSEDCARE-', ''
             ),
             '3PR-', ''
           ),
           '3PR -', ''
         ) AS patient_id,
         vp.activity_date AS activity_date,
         UPPER(TRIM(vp.provider_code)) AS provider_code_norm,
         TRIM(vp.service) AS service
  FROM sheets.V_PROVIDER_TASKS_NORM vp
  WHERE vp.activity_date IS NOT NULL
), staging_provider AS (
  SELECT DISTINCT
         TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(patient_name_raw, ',', ' '), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
         activity_date,
         UPPER(TRIM(provider_code)) AS provider_code_norm,
         TRIM(service) AS service
  FROM staging_provider_tasks
  WHERE activity_date IS NOT NULL
)
SELECT sp.patient_id, sp.activity_date, sp.provider_code_norm AS provider_code, sp.service
FROM sheets_provider sp
LEFT JOIN staging_provider st
  ON st.patient_id = sp.patient_id
 AND st.activity_date = sp.activity_date
 AND st.provider_code_norm = sp.provider_code_norm
 AND st.service = sp.service
WHERE st.activity_date IS NULL;
.output stdout

-- 2) Provider tasks: rows present in staging but missing in sheets view (normalized join keys)
.output outputs/reports/provider_rows_missing_in_sheets_views.csv
WITH sheets_provider AS (
  SELECT DISTINCT
         REPLACE(
           REPLACE(
             REPLACE(
               REPLACE(
                 REPLACE(
                   REPLACE(
                     REPLACE(
                       REPLACE(
                         REPLACE(TRIM(REPLACE(vp.patient_id, ',', ' ')), 'ZEN-', ''),
                         'PM-', ''
                       ),
                       'ZMN-', ''
                     ),
                     'BlessedCare-', ''
                   ),
                   'BLESSEDCARE-', ''
                 ),
                 'BleessedCare-', ''
               ),
               'BLEESSEDCARE-', ''
             ),
             '3PR-', ''
           ),
           '3PR -', ''
         ) AS patient_id,
         vp.activity_date AS activity_date,
         UPPER(TRIM(vp.provider_code)) AS provider_code_norm,
         TRIM(vp.service) AS service
  FROM sheets.V_PROVIDER_TASKS_NORM vp
  WHERE vp.activity_date IS NOT NULL
), staging_provider AS (
  SELECT DISTINCT
         TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(patient_name_raw, ',', ' '), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
         activity_date,
         UPPER(TRIM(provider_code)) AS provider_code_norm,
         TRIM(service) AS service
  FROM staging_provider_tasks
  WHERE activity_date IS NOT NULL
)
SELECT st.patient_id, st.activity_date, st.provider_code_norm AS provider_code, st.service
FROM staging_provider st
LEFT JOIN sheets_provider sp
  ON sp.patient_id = st.patient_id
 AND sp.activity_date = st.activity_date
 AND sp.provider_code_norm = st.provider_code_norm
 AND sp.service = st.service
WHERE sp.activity_date IS NULL;
.output stdout

-- 3) Coordinator tasks: rows present in sheets view but missing in staging (normalized join keys, last 3 months)
.output outputs/reports/coordinator_rows_missing_in_staging_views.csv
WITH sheets_coord AS (
  SELECT DISTINCT
         REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(vc.patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
         vc.activity_date AS activity_date,
         UPPER(TRIM(vc.staff_code)) AS staff_code_norm,
         TRIM(vc.task_type) AS task_type
  FROM sheets.V_COORDINATOR_TASKS_NORM vc
  WHERE vc.activity_date IS NOT NULL
    AND vc.activity_date >= date('now','-3 months')
), staging_coord AS (
  SELECT DISTINCT
         TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(patient_name_raw, ',', ' '), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
         activity_date,
         UPPER(TRIM(staff_code)) AS staff_code_norm,
         TRIM(task_type) AS task_type
  FROM staging_coordinator_tasks
  WHERE activity_date IS NOT NULL
    AND activity_date >= date('now','-3 months')
)
SELECT sc.patient_id, sc.activity_date, sc.staff_code_norm AS staff_code, sc.task_type
FROM sheets_coord sc
LEFT JOIN staging_coord st
  ON st.patient_id = sc.patient_id
 AND st.activity_date = sc.activity_date
 AND st.staff_code_norm = sc.staff_code_norm
 AND st.task_type = sc.task_type
WHERE st.activity_date IS NULL;
.output stdout

-- 4) Coordinator tasks: rows present in staging but missing in sheets view (normalized join keys, last 3 months)
.output outputs/reports/coordinator_rows_missing_in_sheets_views.csv
WITH sheets_coord AS (
  SELECT DISTINCT
         REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(vc.patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
         vc.activity_date AS activity_date,
         UPPER(TRIM(vc.staff_code)) AS staff_code_norm,
         TRIM(vc.task_type) AS task_type
  FROM sheets.V_COORDINATOR_TASKS_NORM vc
  WHERE vc.activity_date IS NOT NULL
    AND vc.activity_date >= date('now','-3 months')
), staging_coord AS (
  SELECT DISTINCT
         TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(patient_name_raw, ',', ' '), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
         activity_date,
         UPPER(TRIM(staff_code)) AS staff_code_norm,
         TRIM(task_type) AS task_type
  FROM staging_coordinator_tasks
  WHERE activity_date IS NOT NULL
    AND activity_date >= date('now','-3 months')
)
SELECT st.patient_id, st.activity_date, st.staff_code_norm AS staff_code, st.task_type
FROM staging_coord st
LEFT JOIN sheets_coord sc
  ON sc.patient_id = st.patient_id
 AND sc.activity_date = st.activity_date
 AND sc.staff_code_norm = st.staff_code_norm
 AND sc.task_type = st.task_type
WHERE sc.activity_date IS NULL;
.output stdout

-- 5) Patient visits equivalence: compare V_PATIENT_VISITS_EQUIV vs curated patient_visits
.output outputs/reports/patient_visits_rows_missing_in_staging_views.csv
WITH sheets_visits AS (
  SELECT 
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
    CASE 
      WHEN LENGTH(TRIM(last_visit_date)) = 8 THEN '20' || substr(TRIM(last_visit_date),1,2) || '-' || substr(TRIM(last_visit_date),4,2) || '-' || substr(TRIM(last_visit_date),7,2)
      ELSE TRIM(last_visit_date)
    END AS last_visit_date_norm,
    TRIM(service_type) AS service_type
  FROM sheets.V_PATIENT_VISITS_EQUIV
  WHERE last_visit_date IS NOT NULL
), staging_visits AS (
  SELECT 
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
    CASE 
      WHEN LENGTH(TRIM(last_visit_date)) = 8 THEN '20' || substr(TRIM(last_visit_date),1,2) || '-' || substr(TRIM(last_visit_date),4,2) || '-' || substr(TRIM(last_visit_date),7,2)
      ELSE TRIM(last_visit_date)
    END AS last_visit_date_norm,
    TRIM(service_type) AS service_type
  FROM patient_visits
  WHERE last_visit_date IS NOT NULL
)
SELECT sv.patient_id, sv.last_visit_date_norm AS last_visit_date, sv.service_type
FROM sheets_visits sv
LEFT JOIN staging_visits st
  ON st.patient_id = sv.patient_id
 AND st.last_visit_date_norm = sv.last_visit_date_norm
 AND st.service_type = sv.service_type
WHERE st.patient_id IS NULL;
.output stdout

.output outputs/reports/patient_visits_rows_missing_in_sheets_views.csv
WITH sheets_visits AS (
  SELECT 
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
    CASE 
      WHEN LENGTH(TRIM(last_visit_date)) = 8 THEN '20' || substr(TRIM(last_visit_date),1,2) || '-' || substr(TRIM(last_visit_date),4,2) || '-' || substr(TRIM(last_visit_date),7,2)
      ELSE TRIM(last_visit_date)
    END AS last_visit_date_norm,
    TRIM(service_type) AS service_type
  FROM sheets.V_PATIENT_VISITS_EQUIV
  WHERE last_visit_date IS NOT NULL
), staging_visits AS (
  SELECT 
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '') AS patient_id,
    CASE 
      WHEN LENGTH(TRIM(last_visit_date)) = 8 THEN '20' || substr(TRIM(last_visit_date),1,2) || '-' || substr(TRIM(last_visit_date),4,2) || '-' || substr(TRIM(last_visit_date),7,2)
      ELSE TRIM(last_visit_date)
    END AS last_visit_date_norm,
    TRIM(service_type) AS service_type
  FROM patient_visits
  WHERE last_visit_date IS NOT NULL
)
SELECT st.patient_id, st.last_visit_date_norm AS last_visit_date, st.service_type
FROM staging_visits st
LEFT JOIN sheets_visits sv
  ON sv.patient_id = st.patient_id
 AND sv.last_visit_date_norm = st.last_visit_date_norm
 AND sv.service_type = st.service_type
WHERE sv.patient_id IS NULL;
.output stdout

-- 6) Panel presence vs sheets patients view
.output outputs/reports/panel_patients_missing_in_sheets_views.csv
SELECT p.patient_id
FROM staging_patient_panel p
LEFT JOIN sheets.V_PATIENTS_EQUIV spd ON spd.patient_id = p.patient_id
WHERE spd.patient_id IS NULL;
.output stdout

.output outputs/reports/patients_in_sheets_missing_in_panel_views.csv
SELECT spd.patient_id
FROM sheets.V_PATIENTS_EQUIV spd
LEFT JOIN staging_patient_panel p ON p.patient_id = spd.patient_id
WHERE p.patient_id IS NULL;
.output stdout

-- 7) Collision report: normalized patient_id duplicates in sheets patients view
.output outputs/reports/patient_id_norm_collisions_views.csv
SELECT patient_id, COUNT(*) AS cnt
FROM sheets.V_PATIENTS_EQUIV
GROUP BY patient_id
HAVING cnt > 1
ORDER BY cnt DESC, patient_id ASC;
.output stdout