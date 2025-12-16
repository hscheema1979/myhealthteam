-- Patient population comparison: production vs staging
-- This validates that normalization works by checking patient overlap

ATTACH '.\sheets_data.db' AS staging;

.mode csv
.headers on

-- Patient population summary
.output scripts/outputs/reports/patient_population_summary.csv
.headers on
SELECT 
  'Production Patients' as source,
  COUNT(*) as total_patients,
  MIN(created_date) as earliest_created,
  MAX(created_date) as latest_created
FROM patients

UNION ALL

SELECT 
  'Staging Patients' as source,
  COUNT(*) as total_patients,
  'N/A' as earliest_created,
  'N/A' as latest_created
FROM staging.SOURCE_PATIENT_DATA;

-- Production patient normalization (local query)
-- Patient matching analysis
.output scripts/outputs/reports/patient_matching_analysis.csv
.headers on
SELECT 
  'Production Normalized Patients' as category,
  COUNT(*) as total_count,
  COUNT(DISTINCT patient_id_norm) as unique_patients
FROM (
  SELECT
    TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm
  FROM patients
) AS prod_norm

UNION ALL

SELECT 
  'Staging Normalized Patients' as category,
  COUNT(*) as total_count,
  COUNT(DISTINCT patient_id_norm) as unique_patients
FROM (
  SELECT
    TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm
  FROM staging.SOURCE_PATIENT_DATA
) AS staging_norm;

-- Sample matching patients to verify normalization
.output scripts/outputs/reports/patient_matching_samples.csv
.headers on
SELECT 
  'Matched Patients' as match_type,
  prod_norm.patient_id_norm as normalized_patient_id,
  prod_raw.patient_name as production_name,
  staging_raw.patient_name_raw as staging_name,
  prod_raw.date_of_birth as prod_dob,
  staging_raw.date_of_birth as staging_dob,
  CASE WHEN prod_raw.date_of_birth = staging_raw.date_of_birth THEN 'MATCH' ELSE 'MISMATCH' END as dob_status
FROM (
  SELECT
    TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm,
    patient_name
  FROM patients
) AS prod_norm
INNER JOIN patients AS prod_raw ON prod_norm.patient_name = prod_raw.patient_name
INNER JOIN (
  SELECT
    TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id_norm,
    patient_name_raw
  FROM staging.SOURCE_PATIENT_DATA
) AS staging_norm ON prod_norm.patient_id_norm = staging_norm.patient_id_norm
INNER JOIN staging.SOURCE_PATIENT_DATA AS staging_raw ON staging_norm.patient_name_raw = staging_raw.patient_name_raw
WHERE prod_raw.date_of_birth = staging_raw.date_of_birth
ORDER BY prod_norm.patient_id_norm
LIMIT 10;

-- Sample patients with normalization applied (showing the process)
.output scripts/outputs/reports/normalization_process_samples.csv
.headers on
SELECT 
  'Production Patient' as source_type,
  patient_name as raw_name,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS normalized_name,
  date_of_birth,
  '2025-09-17 validation' as validation_note
FROM patients
WHERE patient_name LIKE 'ZEN-%' OR patient_name LIKE 'PM-%' OR patient_name LIKE 'BlessedCare-%'
ORDER BY patient_name
LIMIT 5;

UNION ALL

SELECT 
  'Staging Patient' as source_type,
  patient_name_raw as raw_name,
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS normalized_name,
  date_of_birth,
  '2025-09-17 validation' as validation_note
FROM staging.SOURCE_PATIENT_DATA
WHERE patient_name_raw LIKE 'ZEN-%' OR patient_name_raw LIKE 'PM-%' OR patient_name_raw LIKE 'BlessedCare-%'
ORDER BY patient_name_raw
LIMIT 5;

.output stdout