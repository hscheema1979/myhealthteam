-- Build curated candidate export tables inside sheets_data.db so we can copy to production safely
-- This script is intended to be executed with sqlite3 against sheets_data.db directly

-- 1) Export patient visits from SOURCE_PROVIDER_TASKS_HISTORY
DROP TABLE IF EXISTS EXPORT_PATIENT_VISITS;
CREATE TABLE EXPORT_PATIENT_VISITS (
  patient_id TEXT,
  last_visit_date TEXT,
  service_type TEXT
);

WITH norm AS (
  SELECT REPLACE("Patient Last, First DOB", ',', '') AS patient_id,
         CASE
           WHEN "DOS" IS NOT NULL AND "DOS" != '' THEN
             substr("DOS", 7, 4) || '-' || substr("DOS", 1, 2) || '-' || substr("DOS", 4, 2)
           ELSE NULL
         END AS activity_date,
         TRIM("Service") AS service
  FROM SOURCE_PROVIDER_TASKS_HISTORY
  WHERE "Patient Last, First DOB" IS NOT NULL
    AND "Patient Last, First DOB" != ''
    AND "Patient Last, First DOB" != 'Patient Last, First DOB'
)
, latest AS (
  SELECT patient_id, MAX(activity_date) AS last_visit_date
  FROM norm
  WHERE activity_date IS NOT NULL
  GROUP BY patient_id
)
INSERT INTO EXPORT_PATIENT_VISITS (patient_id, last_visit_date, service_type)
SELECT l.patient_id,
       l.last_visit_date,
       MIN(n.service) AS service_type
FROM latest l
LEFT JOIN norm n
  ON n.patient_id = l.patient_id AND n.activity_date = l.last_visit_date
GROUP BY l.patient_id, l.last_visit_date;

-- 2) Export patient panel last visit fields keyed by normalized patient_id
DROP TABLE IF EXISTS EXPORT_PATIENT_PANEL_LAST_VISIT;
CREATE TABLE EXPORT_PATIENT_PANEL_LAST_VISIT (
  patient_id TEXT,
  last_visit_date TEXT,
  last_visit_service_type TEXT
);

INSERT INTO EXPORT_PATIENT_PANEL_LAST_VISIT (patient_id, last_visit_date, last_visit_service_type)
SELECT e.patient_id,
       e.last_visit_date,
       e.service_type AS last_visit_service_type
FROM EXPORT_PATIENT_VISITS e;

-- Optional: patients last_visit export (same as visits, used to update patients table)
DROP TABLE IF EXISTS EXPORT_PATIENTS_LAST_VISIT;
CREATE TABLE EXPORT_PATIENTS_LAST_VISIT (
  patient_id TEXT,
  last_visit_date TEXT,
  service_type TEXT
);
INSERT INTO EXPORT_PATIENTS_LAST_VISIT (patient_id, last_visit_date, service_type)
SELECT patient_id, last_visit_date, service_type FROM EXPORT_PATIENT_VISITS;