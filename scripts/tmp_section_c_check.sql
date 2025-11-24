ATTACH '.\scripts\sheets_data.db' AS staging;
CREATE TEMP VIEW SOURCE_PROVIDER_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_PROVIDER_TASKS_HISTORY;

.mode csv
.headers on
.output outputs/reports/tmp_section_c_check.csv
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