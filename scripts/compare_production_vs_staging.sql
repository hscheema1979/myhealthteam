.mode csv
.headers on

-- Provider tasks: production vs staging (normalized keys)
.output outputs/reports/provider_rows_missing_in_staging_production.csv
SELECT p.patient_id, p.activity_date
FROM P_PROVIDER_TASKS_EQUIV p
LEFT JOIN NORM_STAGING_PROVIDER_TASKS st
  ON st.patient_id = p.patient_id AND st.activity_date = p.activity_date
WHERE st.activity_date IS NULL;
.output stdout

.output outputs/reports/provider_rows_missing_in_production_staging.csv
SELECT st.patient_id, st.activity_date
FROM NORM_STAGING_PROVIDER_TASKS st
LEFT JOIN P_PROVIDER_TASKS_EQUIV p
  ON p.patient_id = st.patient_id AND p.activity_date = st.activity_date
WHERE p.activity_date IS NULL;
.output stdout

-- Coordinator tasks: production vs staging (normalized keys)
.output outputs/reports/coordinator_rows_missing_in_staging_production.csv
SELECT p.patient_id, p.activity_date
FROM P_COORDINATOR_TASKS_EQUIV p
LEFT JOIN NORM_STAGING_COORDINATOR_TASKS st
  ON st.patient_id = p.patient_id AND st.activity_date = p.activity_date
WHERE st.activity_date IS NULL;
.output stdout

.output outputs/reports/coordinator_rows_missing_in_production_staging.csv
SELECT st.patient_id, st.activity_date
FROM NORM_STAGING_COORDINATOR_TASKS st
LEFT JOIN P_COORDINATOR_TASKS_EQUIV p
  ON p.patient_id = st.patient_id AND p.activity_date = st.activity_date
WHERE p.activity_date IS NULL;
.output stdout

-- Patients: production vs staging
.output outputs/reports/patients_in_staging_missing_in_production.csv
SELECT sp.patient_id
FROM staging_patients sp
LEFT JOIN patients p ON p.patient_id = sp.patient_id OR p.last_first_dob = sp.last_first_dob
WHERE p.patient_id IS NULL;
.output stdout

.output outputs/reports/patients_in_production_missing_in_staging.csv
SELECT p.patient_id
FROM patients p
LEFT JOIN staging_patients sp ON sp.patient_id = p.patient_id OR sp.last_first_dob = p.last_first_dob
WHERE sp.patient_id IS NULL;
.output stdout

-- Patient visits: production vs staging
.output outputs/reports/patient_visits_rows_missing_in_staging.csv
SELECT 
  CASE 
    WHEN LENGTH(TRIM(pv.last_visit_date)) = 8 THEN '20' || substr(TRIM(pv.last_visit_date),1,2) || '-' || substr(TRIM(pv.last_visit_date),4,2) || '-' || substr(TRIM(pv.last_visit_date),7,2)
    ELSE TRIM(pv.last_visit_date)
  END AS last_visit_date_norm,
  TRIM(pv.service_type) AS service_type,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(pv.patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id
FROM patient_visits pv
LEFT JOIN staging_patient_visits sv
  ON sv.patient_id = TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(pv.patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', ''))
 AND 
  (
    CASE 
      WHEN LENGTH(TRIM(pv.last_visit_date)) = 8 THEN '20' || substr(TRIM(pv.last_visit_date),1,2) || '-' || substr(TRIM(pv.last_visit_date),4,2) || '-' || substr(TRIM(pv.last_visit_date),7,2)
      ELSE TRIM(pv.last_visit_date)
    END
  ) = sv.last_visit_date
 AND TRIM(pv.service_type) = sv.service_type
WHERE sv.patient_id IS NULL;
.output stdout

.output outputs/reports/patient_visits_rows_missing_in_production.csv
SELECT sv.patient_id, sv.last_visit_date, sv.service_type
FROM staging_patient_visits sv
LEFT JOIN patient_visits pv
  ON TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(pv.patient_id, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) = sv.patient_id
 AND 
  (
    CASE 
      WHEN LENGTH(TRIM(pv.last_visit_date)) = 8 THEN '20' || substr(TRIM(pv.last_visit_date),1,2) || '-' || substr(TRIM(pv.last_visit_date),4,2) || '-' || substr(TRIM(pv.last_visit_date),7,2)
      ELSE TRIM(pv.last_visit_date)
    END
  ) = sv.last_visit_date
 AND TRIM(pv.service_type) = sv.service_type
WHERE pv.patient_id IS NULL;
.output stdout

-- Panel presence
.output outputs/reports/panel_patients_missing_in_staging.csv
SELECT p.patient_id
FROM patient_panel p
LEFT JOIN staging_patient_panel sp ON sp.patient_id = p.patient_id
WHERE sp.patient_id IS NULL;
.output stdout

.output outputs/reports/panel_patients_missing_in_production.csv
SELECT sp.patient_id
FROM staging_patient_panel sp
LEFT JOIN patient_panel p ON p.patient_id = sp.patient_id
WHERE p.patient_id IS NULL;
.output stdout