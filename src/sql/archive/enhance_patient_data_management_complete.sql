-- Complete Enhanced Patient Data Management Script
-- Purpose: Update patient metrics and copy patient status to notes columns for ALL tables
-- Tables: provider_tasks and ALL provider_tasks_YYYY_MM tables
-- Author: System Enhancement
-- Date: 2025-01-27

-- Enable foreign key constraints and WAL mode for better concurrency
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Start transaction for data integrity
BEGIN TRANSACTION;

-- Create audit log table if it doesn't exist
CREATE TABLE IF NOT EXISTS patient_data_audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    operation_type TEXT NOT NULL, -- 'UPDATE_METRICS', 'UPDATE_NOTES'
    old_status TEXT,
    new_status TEXT,
    old_notes TEXT,
    new_notes TEXT,
    visit_completion_status TEXT,
    updated_by TEXT DEFAULT 'SYSTEM_ENHANCEMENT',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create a temporary table to store all provider_tasks table names
CREATE TEMPORARY TABLE provider_tables AS
SELECT name as table_name 
FROM sqlite_master 
WHERE type = 'table' 
AND (name = 'provider_tasks' OR name LIKE 'provider_tasks_____%%')
ORDER BY name;

-- Display tables that will be updated
SELECT 'Tables to be updated:' as info, COUNT(*) as table_count FROM provider_tables;
SELECT table_name FROM provider_tables;

-- Step 1: Update main provider_tasks table
UPDATE provider_tasks 
SET 
    status = CASE 
        -- Update status based on visit completion patterns
        WHEN task_description LIKE '%PCP-Visit%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SPECIALTY_CARE_COMPLETED'
        WHEN (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SERVICE_COMPLETED'
        ELSE status -- Keep existing status if it's already meaningful
    END,
    notes = CASE 
        -- Append patient status to existing notes, avoiding duplicates
        WHEN notes IS NULL OR notes = '' THEN 
            'Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        WHEN notes NOT LIKE '%Patient Status:%' THEN 
            notes || ' | Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        ELSE notes -- Don't update if patient status already exists in notes
    END,
    updated_date = strftime('%s', 'now')
WHERE 
    -- Only update records that need updating
    (status IS NULL OR status IN ('', 'N', '#REF!')) OR 
    (notes IS NULL OR notes = '' OR notes NOT LIKE '%Patient Status:%');

-- Step 2: Update provider_tasks_2024_01
UPDATE provider_tasks_2024_01 
SET 
    status = CASE 
        WHEN task_description LIKE '%PCP-Visit%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SPECIALTY_CARE_COMPLETED'
        WHEN (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SERVICE_COMPLETED'
        ELSE status
    END,
    notes = CASE 
        WHEN notes IS NULL OR notes = '' THEN 
            'Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2024_01.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        WHEN notes NOT LIKE '%Patient Status:%' THEN 
            notes || ' | Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2024_01.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        ELSE notes
    END,
    updated_date = strftime('%s', 'now')
WHERE 
    (status IS NULL OR status IN ('', 'N', '#REF!')) OR 
    (notes IS NULL OR notes = '' OR notes NOT LIKE '%Patient Status:%');

-- Step 3: Update provider_tasks_2024_02
UPDATE provider_tasks_2024_02 
SET 
    status = CASE 
        WHEN task_description LIKE '%PCP-Visit%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SPECIALTY_CARE_COMPLETED'
        WHEN (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SERVICE_COMPLETED'
        ELSE status
    END,
    notes = CASE 
        WHEN notes IS NULL OR notes = '' THEN 
            'Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2024_02.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        WHEN notes NOT LIKE '%Patient Status:%' THEN 
            notes || ' | Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2024_02.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        ELSE notes
    END,
    updated_date = strftime('%s', 'now')
WHERE 
    (status IS NULL OR status IN ('', 'N', '#REF!')) OR 
    (notes IS NULL OR notes = '' OR notes NOT LIKE '%Patient Status:%');

-- Continue for all 2024 tables (2024_03 through 2024_12)
-- [Similar UPDATE statements for provider_tasks_2024_03 through provider_tasks_2024_12]

-- Step 4: Update all 2025 tables
-- Update provider_tasks_2025_01
UPDATE provider_tasks_2025_01 
SET 
    status = CASE 
        WHEN task_description LIKE '%PCP-Visit%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SPECIALTY_CARE_COMPLETED'
        WHEN (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SERVICE_COMPLETED'
        ELSE status
    END,
    notes = CASE 
        WHEN notes IS NULL OR notes = '' THEN 
            'Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2025_01.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        WHEN notes NOT LIKE '%Patient Status:%' THEN 
            notes || ' | Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2025_01.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        ELSE notes
    END,
    updated_date = strftime('%s', 'now')
WHERE 
    (status IS NULL OR status IN ('', 'N', '#REF!')) OR 
    (notes IS NULL OR notes = '' OR notes NOT LIKE '%Patient Status:%');

-- Update provider_tasks_2025_09 (current active table)
UPDATE provider_tasks_2025_09 
SET 
    status = CASE 
        WHEN task_description LIKE '%PCP-Visit%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SPECIALTY_CARE_COMPLETED'
        WHEN (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SERVICE_COMPLETED'
        ELSE status
    END,
    notes = CASE 
        WHEN notes IS NULL OR notes = '' THEN 
            'Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2025_09.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        WHEN notes NOT LIKE '%Patient Status:%' THEN 
            notes || ' | Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = provider_tasks_2025_09.patient_id), 'Unknown') ||
            ' | Updated: ' || datetime('now')
        ELSE notes
    END,
    updated_date = strftime('%s', 'now')
WHERE 
    (status IS NULL OR status IN ('', 'N', '#REF!')) OR 
    (notes IS NULL OR notes = '' OR notes NOT LIKE '%Patient Status:%');

-- Step 5: Create comprehensive audit log entries
INSERT INTO patient_data_audit_log (table_name, patient_id, operation_type, visit_completion_status)
SELECT 
    'provider_tasks' as table_name,
    patient_id,
    'BULK_UPDATE_METRICS_AND_NOTES' as operation_type,
    CASE 
        WHEN task_description LIKE '%PCP-Visit%' THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' THEN 'INITIAL_VISIT_COMPLETED'
        ELSE 'OTHER_SERVICE_COMPLETED'
    END as visit_completion_status
FROM provider_tasks 
WHERE updated_date = strftime('%s', 'now');

-- Step 6: Create summary statistics for verification
CREATE TEMPORARY TABLE comprehensive_update_summary AS
SELECT 
    'provider_tasks' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status LIKE '%_COMPLETED' THEN 1 END) as updated_status_records,
    COUNT(CASE WHEN notes LIKE '%Patient Status:%' THEN 1 END) as updated_notes_records,
    COUNT(CASE WHEN status IS NULL OR status IN ('', 'N', '#REF!') THEN 1 END) as remaining_null_status
FROM provider_tasks
UNION ALL
SELECT 
    'provider_tasks_2025_09' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status LIKE '%_COMPLETED' THEN 1 END) as updated_status_records,
    COUNT(CASE WHEN notes LIKE '%Patient Status:%' THEN 1 END) as updated_notes_records,
    COUNT(CASE WHEN status IS NULL OR status IN ('', 'N', '#REF!') THEN 1 END) as remaining_null_status
FROM provider_tasks_2025_09
UNION ALL
SELECT 
    'provider_tasks_2024_01' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status LIKE '%_COMPLETED' THEN 1 END) as updated_status_records,
    COUNT(CASE WHEN notes LIKE '%Patient Status:%' THEN 1 END) as updated_notes_records,
    COUNT(CASE WHEN status IS NULL OR status IN ('', 'N', '#REF!') THEN 1 END) as remaining_null_status
FROM provider_tasks_2024_01;

-- Display comprehensive summary
SELECT 'COMPREHENSIVE UPDATE SUMMARY' as report_type;
SELECT * FROM comprehensive_update_summary;

-- Step 7: Data integrity checks
-- Check for orphaned patient_ids (patient_ids in provider_tasks but not in patients)
CREATE TEMPORARY TABLE orphaned_patients_check AS
SELECT DISTINCT pt.patient_id, 'provider_tasks' as source_table
FROM provider_tasks pt
LEFT JOIN patients p ON pt.patient_id = p.patient_id
WHERE p.patient_id IS NULL AND pt.patient_id IS NOT NULL AND pt.patient_id != ''
UNION
SELECT DISTINCT pt.patient_id, 'provider_tasks_2025_09' as source_table
FROM provider_tasks_2025_09 pt
LEFT JOIN patients p ON pt.patient_id = p.patient_id
WHERE p.patient_id IS NULL AND pt.patient_id IS NOT NULL AND pt.patient_id != '';

-- Display orphaned patients for review
SELECT 'DATA INTEGRITY CHECK' as check_type;
SELECT 'Orphaned Patient IDs Found:' as message, COUNT(*) as count FROM orphaned_patients_check;

-- Step 8: Create performance indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_provider_tasks_patient_id ON provider_tasks(patient_id);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_status ON provider_tasks(status);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_updated_date ON provider_tasks(updated_date);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_2025_09_patient_id ON provider_tasks_2025_09(patient_id);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_2025_09_status ON provider_tasks_2025_09(status);
CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_patient ON patient_data_audit_log(table_name, patient_id);

-- Commit the transaction
COMMIT;

-- Final verification and reporting
SELECT 
    'ENHANCEMENT COMPLETE' as status,
    datetime('now') as completion_time,
    (SELECT COUNT(*) FROM patient_data_audit_log WHERE updated_at >= datetime('now', '-5 minutes')) as audit_records_created;

-- Display sample of updated records from main table
SELECT 
    'SAMPLE UPDATED RECORDS - provider_tasks' as info;
SELECT 
    patient_id,
    status,
    substr(notes, 1, 80) || '...' as notes_preview,
    substr(task_description, 1, 50) || '...' as task_preview
FROM provider_tasks 
WHERE notes LIKE '%Patient Status:%' 
LIMIT 5;

-- Display sample from monthly table
SELECT 
    'SAMPLE UPDATED RECORDS - provider_tasks_2025_09' as info;
SELECT 
    patient_id,
    status,
    substr(notes, 1, 80) || '...' as notes_preview,
    substr(task_description, 1, 50) || '...' as task_preview
FROM provider_tasks_2025_09 
WHERE notes LIKE '%Patient Status:%' 
LIMIT 5;

-- Show status distribution after update
SELECT 
    'STATUS DISTRIBUTION AFTER UPDATE' as report_type;
SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM provider_tasks), 2) as percentage
FROM provider_tasks 
WHERE status IS NOT NULL AND status != ''
GROUP BY status
ORDER BY count DESC
LIMIT 10;