-- Simple validation queries for October 2025 data
.mode csv

-- VALIDATION 1: Check source data
.headers on
SELECT 'SOURCE_PATIENT_DATA', COUNT(*) as total_records
FROM SOURCE_PATIENT_DATA
WHERE "LAST FIRST DOB" IS NOT NULL AND "LAST FIRST DOB" != '' AND "LAST FIRST DOB" != 'LAST FIRST DOB';

SELECT 'Unique patients in source', COUNT(DISTINCT "LAST FIRST DOB")
FROM SOURCE_PATIENT_DATA
WHERE "LAST FIRST DOB" IS NOT NULL AND "LAST FIRST DOB" != '' AND "LAST FIRST DOB" != 'LAST FIRST DOB';

-- VALIDATION 2: Check staging data  
SELECT 'staging_patients', COUNT(*) as total_records
FROM staging_patients;

SELECT 'Unique patients in staging', COUNT(DISTINCT patient_id)
FROM staging_patients;

-- VALIDATION 3: Check for duplicates
SELECT 'Duplicate patient IDs', patient_id, COUNT(*)
FROM staging_patients
GROUP BY patient_id
HAVING COUNT(*) > 1;

-- VALIDATION 4: Check coordinator tasks
SELECT 'SOURCE_CM_TASKS_2025_10', COUNT(*) as total_tasks
FROM SOURCE_CM_TASKS_2025_10;

SELECT 'staging_coordinator_tasks Oct 2025', COUNT(*) as total_tasks
FROM staging_coordinator_tasks
WHERE year_month = '2025_10';

-- VALIDATION 5: Check provider tasks
SELECT 'SOURCE_PSL_TASKS_2025_10', COUNT(*) as total_tasks  
FROM SOURCE_PSL_TASKS_2025_10;

SELECT 'staging_provider_tasks Oct 2025', COUNT(*) as total_tasks
FROM staging_provider_tasks
WHERE year_month = '2025_10';