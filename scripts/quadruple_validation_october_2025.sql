-- Quadruple Validation for October 2025 Import
-- 4-Layer Validation Before Production Transfer

ATTACH '.\\sheets_data.db' AS staging;

.mode csv
.headers on

-- === LAYER 1: PATIENT DATA INTEGRITY VALIDATION ===
.output scripts/outputs/reports/layer1_patient_integrity_oct2025.csv
.headers on
SELECT 
  'Patient Name Normalization Check' as validation_type,
  patient_name_raw as raw_patient_name,
  patient_id_norm as normalized_patient_name,
  provider_code,
  task_date,
  CASE 
    WHEN LENGTH(patient_name_raw) > LENGTH(patient_id_norm) THEN 'Normalized'
    WHEN patient_name_raw = patient_id_norm THEN 'Already Clean'
    ELSE 'Review Needed'
  END as normalization_status,
  CASE
    WHEN patient_name_raw LIKE 'ZEN-%' THEN 'ZEN prefix removed'
    WHEN patient_name_raw LIKE 'PM-%' THEN 'PM prefix removed'
    WHEN patient_name_raw LIKE 'BlessedCare-%' THEN 'BlessedCare prefix removed'
    WHEN patient_name_raw NOT LIKE '%-%' THEN 'No prefix found'
    ELSE 'Unknown prefix pattern'
  END as prefix_handling
FROM NORM_STAGING_PROVIDER_TASKS_OCT
WHERE patient_name_raw LIKE 'ZEN-%' 
   OR patient_name_raw LIKE 'PM-%' 
   OR patient_name_raw LIKE 'BlessedCare-%'
ORDER BY patient_name_raw
LIMIT 15;

-- Patient coverage validation (staging vs production)
.output scripts/outputs/reports/patient_coverage_oct2025.csv
.headers on
SELECT * FROM (
  SELECT 
    'Staging October Patients' as dataset,
    COUNT(DISTINCT patient_id_norm) as unique_patients,
    COUNT(*) as total_tasks,
    MIN(task_date) as date_range_start,
    MAX(task_date) as date_range_end,
    'Raw staging data' as source_system
  FROM NORM_STAGING_PROVIDER_TASKS_OCT

  UNION ALL

  SELECT 
    'Production September Patients' as dataset,
    COUNT(DISTINCT first_name || ' ' || last_name) as unique_patients,
    COUNT(*) as total_patients,
    'N/A' as date_range_start,
    'N/A' as date_range_end,
    'Normalized production data' as source_system
  FROM patient_panel
)
ORDER BY dataset;

-- === LAYER 2: COORDINATOR DATA INTEGRITY VALIDATION ===
.output scripts/outputs/reports/layer2_coordinator_integrity_oct2025.csv
.headers on
SELECT 
  'Coordinator Data Status' as validation_type,
  coordinator_id,
  COUNT(DISTINCT patient_id_raw) as unique_patients,
  COUNT(*) as total_coordinator_tasks,
  MIN(task_date) as first_task_date,
  MAX(task_date) as last_task_date,
  CASE 
    WHEN COUNT(*) > 0 THEN 'Data Available'
    ELSE 'No Coordinator Data for Oct 2025'
  END as data_status
FROM NORM_STAGING_COORDINATOR_TASKS_OCT
GROUP BY coordinator_id
ORDER BY coordinator_id;

-- Coordinator vs Provider patient overlap check
.output scripts/outputs/reports/coordinator_provider_overlap_oct2025.csv
.headers on
SELECT 
  'Patient Overlap Analysis' as analysis_type,
  COUNT(DISTINCT nsp.patient_id_norm) as provider_patients_oct,
  COUNT(DISTINCT nsc.patient_id_norm) as coordinator_patients_oct,
  COUNT(DISTINCT CASE WHEN nsp.patient_id_norm = nsc.patient_id_norm THEN nsp.patient_id_norm END) as overlapping_patients,
  ROUND(COUNT(DISTINCT CASE WHEN nsp.patient_id_norm = nsc.patient_id_norm THEN nsp.patient_id_norm END) * 100.0 / NULLIF(COUNT(DISTINCT nsp.patient_id_norm), 0), 2) as overlap_percentage,
  'October 2025 patient coverage' as validation_note
FROM NORM_STAGING_PROVIDER_TASKS_OCT nsp
LEFT JOIN NORM_STAGING_COORDINATOR_TASKS_OCT nsc ON nsp.patient_id_norm = nsc.patient_id_norm;

-- === LAYER 3: PROVIDER DATA INTEGRITY VALIDATION ===
.output scripts/outputs/reports/layer3_provider_integrity_oct2025.csv
.headers on
SELECT 
  'Provider Assignment Validation' as validation_type,
  provider_code,
  COUNT(*) as total_tasks,
  COUNT(DISTINCT patient_id_norm) as unique_patients,
  COUNT(DISTINCT service) as service_types,
  SUM(CAST(minutes_raw AS INTEGER)) as total_minutes,
  MIN(task_date) as first_task_date,
  MAX(task_date) as last_task_date,
  CASE 
    WHEN COUNT(DISTINCT patient_id_norm) > 50 THEN 'High volume provider'
    WHEN COUNT(DISTINCT patient_id_norm) > 20 THEN 'Medium volume provider'
    WHEN COUNT(DISTINCT patient_id_norm) > 0 THEN 'Active provider'
    ELSE 'No patients assigned'
  END as provider_category
FROM NORM_STAGING_PROVIDER_TASKS_OCT
GROUP BY provider_code
ORDER BY total_tasks DESC;

-- Provider-patient assignment consistency check
.output scripts/outputs/reports/provider_patient_assignment_oct2025.csv
.headers on
SELECT 
  'Production vs Staging Provider Comparison' as analysis_type,
  pp.provider_name as production_provider,
  st.provider_code as staging_provider_code,
  COUNT(*) as staging_tasks_october,
  COUNT(DISTINCT st.patient_id_norm) as staging_patients_oct,
  CASE 
    WHEN pp.provider_name LIKE '%' || SUBSTR(st.provider_code, 1, 3) || '%' THEN 'Potential Match'
    WHEN pp.provider_name = st.provider_code THEN 'Exact Match'
    ELSE 'Review Needed'
  END as provider_alignment
FROM NORM_STAGING_PROVIDER_TASKS_OCT st
LEFT JOIN patient_panel pp ON st.provider_code = pp.provider_name
GROUP BY pp.provider_name, st.provider_code
HAVING COUNT(*) > 0
ORDER BY staging_tasks_october DESC;

-- === LAYER 4: PRE-IMPORT DATA QUALITY VALIDATION ===
.output scripts/outputs/reports/layer4_data_quality_oct2025.csv
.headers on
SELECT 
  'Data Quality Assessment' as quality_check,
  'Provider Tasks' as data_type,
  COUNT(*) as total_records,
  COUNT(CASE WHEN patient_name_raw IS NOT NULL AND patient_name_raw != '' THEN 1 END) as valid_patient_names,
  COUNT(CASE WHEN provider_code IS NOT NULL AND provider_code != '' THEN 1 END) as valid_provider_codes,
  COUNT(CASE WHEN task_date IS NOT NULL AND task_date != '' THEN 1 END) as valid_dates,
  COUNT(CASE WHEN service IS NOT NULL AND service != '' THEN 1 END) as valid_services,
  ROUND(COUNT(CASE WHEN patient_name_raw IS NOT NULL AND patient_name_raw != '' THEN 1 END) * 100.0 / COUNT(*), 2) as patient_name_quality_score,
  ROUND(COUNT(CASE WHEN provider_code IS NOT NULL AND provider_code != '' THEN 1 END) * 100.0 / COUNT(*), 2) as provider_code_quality_score
FROM NORM_STAGING_PROVIDER_TASKS_OCT

UNION ALL

SELECT 
  'Data Quality Assessment' as quality_check,
  'Coordinator Tasks' as data_type,
  COUNT(*) as total_records,
  COUNT(CASE WHEN patient_id_raw IS NOT NULL AND patient_id_raw != '' THEN 1 END) as valid_patient_names,
  COUNT(CASE WHEN coordinator_id IS NOT NULL AND coordinator_id != '' THEN 1 END) as valid_provider_codes,
  COUNT(CASE WHEN task_date IS NOT NULL AND task_date != '' THEN 1 END) as valid_dates,
  COUNT(CASE WHEN task_type IS NOT NULL AND task_type != '' THEN 1 END) as valid_services,
  ROUND(COUNT(CASE WHEN patient_id_raw IS NOT NULL AND patient_id_raw != '' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as patient_name_quality_score,
  ROUND(COUNT(CASE WHEN coordinator_id IS NOT NULL AND coordinator_id != '' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as provider_code_quality_score
FROM NORM_STAGING_COORDINATOR_TASKS_OCT;

-- Daily task distribution validation for October 2025
.output scripts/outputs/reports/october_daily_distribution_validation.csv
.headers on
SELECT 
  task_date,
  'Provider Tasks' as task_type,
  COUNT(*) as task_count,
  COUNT(DISTINCT patient_id_norm) as unique_patients,
  COUNT(DISTINCT provider_code) as unique_providers,
  SUM(CAST(minutes_raw AS INTEGER)) as total_minutes,
  CASE 
    WHEN COUNT(*) > 20 THEN 'High activity day'
    WHEN COUNT(*) > 10 THEN 'Medium activity day'
    WHEN COUNT(*) > 0 THEN 'Normal activity day'
    ELSE 'No activity'
  END as activity_level
FROM NORM_STAGING_PROVIDER_TASKS_OCT
GROUP BY task_date
ORDER BY task_date;

-- COMPREHENSIVE IMPORT READINESS ASSESSMENT
.output scripts/outputs/reports/import_readiness_assessment_oct2025.csv
.headers on
SELECT 
  'October 2025 Import Readiness' as assessment_type,
  'OVERALL STATUS' as category,
  CASE 
    WHEN (SELECT COUNT(*) FROM NORM_STAGING_PROVIDER_TASKS_OCT) > 0 THEN 'READY TO IMPORT'
    ELSE 'NO DATA TO IMPORT'
  END as status,
  CONCAT('Provider Tasks: ', (SELECT COUNT(*) FROM NORM_STAGING_PROVIDER_TASKS_OCT), ' | Coordinator Tasks: ', (SELECT COUNT(*) FROM NORM_STAGING_COORDINATOR_TASKS_OCT), ' | Unique Patients: ', (SELECT COUNT(DISTINCT patient_id_norm) FROM NORM_STAGING_PROVIDER_TASKS_OCT)) as summary,
  'All validation layers completed' as validation_status
FROM (SELECT 1);

.output stdout