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

-- Normalization comparison
.output scripts/outputs/reports/patient_normalization_comparison.csv
.headers on
SELECT 
  'Production Normalized Count' as metric,
  COUNT(*) as value
FROM (
  SELECT TRIM(first_name || ' ' || last_name) as full_name_normalized
  FROM patients
)

UNION ALL

SELECT 
  'Production Unique Normalized Count' as metric,
  COUNT(DISTINCT TRIM(first_name || ' ' || last_name)) as value
FROM patients

UNION ALL

SELECT 
  'Staging Normalized Count' as metric,
  COUNT(*) as value
FROM (
  SELECT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(`Pt Name`, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) as normalized_name
  FROM staging.SOURCE_PATIENT_DATA
)

UNION ALL

SELECT 
  'Staging Unique Normalized Count' as metric,
  COUNT(DISTINCT TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(`Pt Name`, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', ''))) as value
FROM staging.SOURCE_PATIENT_DATA;

-- Sample normalization examples from both databases
.output scripts/outputs/reports/normalization_examples.csv
.headers on
SELECT * FROM (
  SELECT 
    'Production Example' as source_type,
    first_name as raw_first_name,
    last_name as raw_last_name,
    TRIM(first_name || ' ' || last_name) as normalized_name,
    date_of_birth,
    '2025-09-17 validation' as validation_note
  FROM patients
  WHERE first_name LIKE 'ZEN-%' OR last_name LIKE 'PM-%' OR first_name LIKE 'BlessedCare-%'
  
  UNION ALL
  
  SELECT 
    'Staging Example' as source_type,
    SUBSTR(`Pt Name`, 1, INSTR(`Pt Name`, ' ') - 1) as raw_first_name,
    SUBSTR(`Pt Name`, INSTR(`Pt Name`, ' ') + 1) as raw_last_name,
    TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(`Pt Name`, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) as normalized_name,
    `LAST FIRST DOB` as date_of_birth,
    '2025-09-17 validation' as validation_note
  FROM staging.SOURCE_PATIENT_DATA
  WHERE `Pt Name` LIKE 'ZEN-%' OR `Pt Name` LIKE 'PM-%' OR `Pt Name` LIKE 'BlessedCare-%'
)
ORDER BY source_type, raw_first_name, raw_last_name
LIMIT 10;

-- Patient name analysis - focus on potential matches
.output scripts/outputs/reports/patient_name_analysis.csv
.headers on
SELECT 
  'Production Patient Names with Prefixes' as category,
  first_name || ' ' || last_name as patient_name,
  date_of_birth
FROM patients
WHERE first_name LIKE 'ZEN-%' OR first_name LIKE 'PM-%' OR first_name LIKE 'BlessedCare-%'
   OR last_name LIKE 'ZEN-%' OR last_name LIKE 'PM-%' OR last_name LIKE 'BlessedCare-%'
ORDER BY first_name, last_name;

.output scripts/outputs/reports/patient_name_analysis.csv
.headers on
SELECT 
  'Staging Patient Names with Prefixes' as category,
  `Pt Name` as patient_name,
  `LAST FIRST DOB` as date_of_birth
FROM staging.SOURCE_PATIENT_DATA
WHERE `Pt Name` LIKE 'ZEN-%' OR `Pt Name` LIKE 'PM-%' OR `Pt Name` LIKE 'BlessedCare-%'
ORDER BY `Pt Name`;

.output stdout