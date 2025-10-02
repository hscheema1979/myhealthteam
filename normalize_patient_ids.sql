-- Patient ID Normalization Script
-- Purpose: Standardize patient_id formats to "LASTNAME FIRSTNAME MM/DD/YYYY"
-- Created: $(Get-Date)
-- Backup: production_backup_YYYYMMDD_HHMMSS.db

-- ============================================================================
-- PHASE 1: CRITICAL TABLES - IMMEDIATE PRIORITY
-- ============================================================================

-- Disable foreign key constraints during normalization
PRAGMA foreign_keys = OFF;

-- Pre-normalization validation
SELECT 'PRE-NORMALIZATION COUNTS' as validation_step;
SELECT 'coordinator_tasks' as table_name, COUNT(*) as record_count FROM coordinator_tasks;
SELECT 'provider_tasks' as table_name, COUNT(*) as record_count FROM provider_tasks;
SELECT 'coordinator_tasks_2025_10' as table_name, COUNT(*) as record_count FROM coordinator_tasks_2025_10;
SELECT 'provider_tasks_2025_10' as table_name, COUNT(*) as record_count FROM provider_tasks_2025_10;

-- Sample current formats
SELECT 'CURRENT FORMATS - coordinator_tasks' as validation_step;
SELECT DISTINCT patient_id, LENGTH(patient_id) as id_length 
FROM coordinator_tasks 
WHERE patient_id NOT LIKE 'TEST_%' 
LIMIT 5;

SELECT 'CURRENT FORMATS - provider_tasks' as validation_step;
SELECT DISTINCT patient_id, LENGTH(patient_id) as id_length 
FROM provider_tasks 
WHERE patient_id NOT LIKE 'TEST_%' 
LIMIT 5;

-- ============================================================================
-- TRANSFORMATION 1: Remove comma from coordinator_tasks
-- ============================================================================

SELECT 'STARTING: coordinator_tasks normalization' as status;

-- Update coordinator_tasks: "LASTNAME, FIRSTNAME MM/DD/YYYY" -> "LASTNAME FIRSTNAME MM/DD/YYYY"
UPDATE coordinator_tasks 
SET patient_id = REPLACE(patient_id, ', ', ' ')
WHERE patient_id LIKE '%,%' 
  AND patient_id NOT LIKE 'TEST_%';

-- Verify transformation
SELECT 'POST-TRANSFORM coordinator_tasks' as validation_step;
SELECT COUNT(*) as records_with_comma FROM coordinator_tasks WHERE patient_id LIKE '%,%';
SELECT DISTINCT patient_id FROM coordinator_tasks WHERE patient_id NOT LIKE 'TEST_%' LIMIT 3;

-- ============================================================================
-- TRANSFORMATION 2: Remove comma from provider_tasks
-- ============================================================================

SELECT 'STARTING: provider_tasks normalization' as status;

-- Update provider_tasks: "LASTNAME, FIRSTNAME MM/DD/YYYY" -> "LASTNAME FIRSTNAME MM/DD/YYYY"
UPDATE provider_tasks 
SET patient_id = REPLACE(patient_id, ', ', ' ')
WHERE patient_id LIKE '%,%' 
  AND patient_id NOT LIKE 'TEST_%';

-- Verify transformation
SELECT 'POST-TRANSFORM provider_tasks' as validation_step;
SELECT COUNT(*) as records_with_comma FROM provider_tasks WHERE patient_id LIKE '%,%';
SELECT DISTINCT patient_id FROM provider_tasks WHERE patient_id NOT LIKE 'TEST_%' LIMIT 3;

-- ============================================================================
-- TRANSFORMATION 3: Remove test data from October 2025 tables
-- ============================================================================

SELECT 'STARTING: Test data removal from October 2025 tables' as status;

-- Count test records before deletion
SELECT 'TEST DATA COUNTS - BEFORE DELETION' as validation_step;
SELECT COUNT(*) as test_records FROM coordinator_tasks_2025_10 WHERE patient_id LIKE 'TEST_%';
SELECT COUNT(*) as test_records FROM provider_tasks_2025_10 WHERE patient_id LIKE 'TEST_%';

-- Delete test data from coordinator_tasks_2025_10
DELETE FROM coordinator_tasks_2025_10 WHERE patient_id LIKE 'TEST_%';

-- Delete test data from provider_tasks_2025_10  
DELETE FROM provider_tasks_2025_10 WHERE patient_id LIKE 'TEST_%';

-- Verify test data removal
SELECT 'POST-DELETION TEST DATA COUNTS' as validation_step;
SELECT COUNT(*) as remaining_test_records FROM coordinator_tasks_2025_10 WHERE patient_id LIKE 'TEST_%';
SELECT COUNT(*) as remaining_test_records FROM provider_tasks_2025_10 WHERE patient_id LIKE 'TEST_%';

-- ============================================================================
-- VALIDATION: Check foreign key compatibility
-- ============================================================================

SELECT 'FOREIGN KEY VALIDATION' as validation_step;

-- Check if patient_ids in task tables exist in patients table
SELECT 'coordinator_tasks orphaned records' as check_type, COUNT(*) as orphaned_count
FROM coordinator_tasks ct
LEFT JOIN patients p ON ct.patient_id = p.patient_id
WHERE p.patient_id IS NULL AND ct.patient_id NOT LIKE 'TEST_%';

SELECT 'provider_tasks orphaned records' as check_type, COUNT(*) as orphaned_count
FROM provider_tasks pt
LEFT JOIN patients p ON pt.patient_id = p.patient_id
WHERE p.patient_id IS NULL AND pt.patient_id NOT LIKE 'TEST_%';

-- Sample matching records
SELECT 'MATCHING RECORDS SAMPLE' as validation_step;
SELECT ct.patient_id as coordinator_id, p.patient_id as patients_id, 
       CASE WHEN ct.patient_id = p.patient_id THEN 'MATCH' ELSE 'NO_MATCH' END as status
FROM coordinator_tasks ct
JOIN patients p ON ct.patient_id = p.patient_id
LIMIT 5;

-- ============================================================================
-- POST-NORMALIZATION SUMMARY
-- ============================================================================

SELECT 'POST-NORMALIZATION SUMMARY' as validation_step;
SELECT 'coordinator_tasks' as table_name, COUNT(*) as final_count FROM coordinator_tasks;
SELECT 'provider_tasks' as table_name, COUNT(*) as final_count FROM provider_tasks;
SELECT 'coordinator_tasks_2025_10' as table_name, COUNT(*) as final_count FROM coordinator_tasks_2025_10;
SELECT 'provider_tasks_2025_10' as table_name, COUNT(*) as final_count FROM provider_tasks_2025_10;

-- Check format consistency
SELECT 'FORMAT CONSISTENCY CHECK' as validation_step;
SELECT 
    'coordinator_tasks' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN patient_id LIKE '%,%' THEN 1 END) as records_with_comma,
    COUNT(CASE WHEN patient_id LIKE 'TEST_%' THEN 1 END) as test_records
FROM coordinator_tasks;

SELECT 
    'provider_tasks' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN patient_id LIKE '%,%' THEN 1 END) as records_with_comma,
    COUNT(CASE WHEN patient_id LIKE 'TEST_%' THEN 1 END) as test_records
FROM provider_tasks;

-- Re-enable foreign key constraints (will be done separately after validation)
-- PRAGMA foreign_keys = ON;

SELECT 'NORMALIZATION PHASE 1 COMPLETE' as final_status;
SELECT 'Next step: Validate results and re-enable foreign keys' as next_action;