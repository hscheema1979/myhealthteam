-- October 2025 Data Integrity Validation
-- Validates that normalization didn't introduce duplicates or errors

-- VALIDATION 1: Source vs Staging Patient Counts
SELECT 
    'SOURCE_PATIENT_DATA' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT `LAST FIRST DOB`) as unique_patient_ids
FROM SOURCE_PATIENT_DATA
WHERE `LAST FIRST DOB` IS NOT NULL AND `LAST FIRST DOB` != '' AND `LAST FIRST DOB` != 'LAST FIRST DOB'

UNION ALL

SELECT 
    'staging_patients' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT patient_id) as unique_patient_ids
FROM staging_patients;

-- VALIDATION 2: Check for duplicate patients in staging
SELECT 
    patient_id,
    COUNT(*) as duplicate_count,
    first_name,
    last_name,
    date_of_birth
FROM staging_patients
GROUP BY patient_id
HAVING COUNT(*) > 1;

-- VALIDATION 3: Validate patient name normalization
SELECT 
    COUNT(*) as patients_with_issues,
    'Missing First Name' as issue_type
FROM staging_patients
WHERE first_name IS NULL OR first_name = '' OR first_name LIKE 'z%'

UNION ALL

SELECT 
    COUNT(*) as patients_with_issues,
    'Missing Last Name' as issue_type
FROM staging_patients
WHERE last_name IS NULL OR last_name = '' OR last_name LIKE 'z%'

UNION ALL

SELECT 
    COUNT(*) as patients_with_issues,
    'Missing DOB' as issue_type
FROM staging_patients
WHERE date_of_birth IS NULL OR date_of_birth = '' OR date_of_birth LIKE 'z%';

-- VALIDATION 4: Source vs Staging assignments match
SELECT 
    COUNT(DISTINCT patient_id) as staging_patients,
    COUNT(*) as staging_assignments
FROM staging_patient_assignments;

-- VALIDATION 5: Coordinator task data integrity
SELECT 
    'SOURCE_CM_TASKS_2025_10' as table_name,
    COUNT(*) as total_tasks,
    COUNT(DISTINCT `LAST FIRST DOB`) as unique_patients,
    COUNT(CASE WHEN `Date Only` IS NOT NULL AND `Date Only` != '' THEN 1 END) as tasks_with_dates
FROM SOURCE_CM_TASKS_2025_10

UNION ALL

SELECT 
    'staging_coordinator_tasks' as table_name,
    COUNT(*) as total_tasks,
    COUNT(DISTINCT patient_id) as unique_patients,
    COUNT(CASE WHEN activity_date IS NOT NULL THEN 1 END) as tasks_with_dates
FROM staging_coordinator_tasks
WHERE year_month = '2025_10';

-- VALIDATION 6: Provider task data integrity  
SELECT 
    'SOURCE_PSL_TASKS_2025_10' as table_name,
    COUNT(*) as total_tasks,
    COUNT(DISTINCT `LAST FIRST DOB`) as unique_patients,
    COUNT(CASE WHEN DOS IS NOT NULL AND DOS != '' THEN 1 END) as tasks_with_dates
FROM SOURCE_PSL_TASKS_2025_10

UNION ALL

SELECT 
    'staging_provider_tasks' as table_name,
    COUNT(*) as total_tasks,
    COUNT(DISTINCT patient_id) as unique_patients,
    COUNT(CASE WHEN activity_date IS NOT NULL THEN 1 END) as tasks_with_dates
FROM staging_provider_tasks
WHERE year_month = '2025_10';