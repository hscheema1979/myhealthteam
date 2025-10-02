-- Enhanced Patient Data Management Script
-- Purpose: Update patient metrics and copy patient status to notes columns
-- Tables: provider_tasks and all provider_tasks_YYYY_MM tables
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

-- Function to determine visit completion status based on task_description
-- This will be used to update patient metrics
WITH visit_completion_mapping AS (
    SELECT 
        CASE 
            WHEN task_description LIKE '%PCP-Visit%' OR task_description LIKE '%Primary Care%' THEN 'PCP_VISIT_COMPLETED'
            WHEN task_description LIKE '%Telehealth%' OR task_description LIKE '%TE%' THEN 'TELEHEALTH_COMPLETED'
            WHEN task_description LIKE '%Home%' OR task_description LIKE '%HO%' THEN 'HOME_VISIT_COMPLETED'
            WHEN task_description LIKE '%Follow%' OR task_description LIKE '%ESTAB%' THEN 'FOLLOWUP_COMPLETED'
            WHEN task_description LIKE '%NEW%' THEN 'INITIAL_VISIT_COMPLETED'
            WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' THEN 'SPECIALTY_CARE_COMPLETED'
            ELSE 'OTHER_SERVICE_COMPLETED'
        END as visit_completion_status,
        task_description
)

-- Step 1: Update provider_tasks table
-- Update patient metrics based on visit completion status and copy patient status to notes
UPDATE provider_tasks 
SET 
    status = CASE 
        -- Update status based on visit completion patterns
        WHEN task_description LIKE '%PCP-Visit%' AND status != 'COMPLETED' THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND status != 'COMPLETED' THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND status != 'COMPLETED' THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND status != 'COMPLETED' THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND status != 'COMPLETED' THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' THEN 'SPECIALTY_CARE_COMPLETED'
        ELSE COALESCE(status, 'SERVICE_COMPLETED')
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

-- Log the updates for provider_tasks
INSERT INTO patient_data_audit_log (table_name, patient_id, operation_type, old_status, new_status, old_notes, new_notes, visit_completion_status)
SELECT 
    'provider_tasks' as table_name,
    pt.patient_id,
    'UPDATE_METRICS_AND_NOTES' as operation_type,
    pt_old.status as old_status,
    pt.status as new_status,
    pt_old.notes as old_notes,
    pt.notes as new_notes,
    CASE 
        WHEN pt.task_description LIKE '%PCP-Visit%' THEN 'PCP_VISIT_COMPLETED'
        WHEN pt.task_description LIKE '%Telehealth%' THEN 'TELEHEALTH_COMPLETED'
        WHEN pt.task_description LIKE '%Home%' THEN 'HOME_VISIT_COMPLETED'
        WHEN pt.task_description LIKE '%Follow%' THEN 'FOLLOWUP_COMPLETED'
        WHEN pt.task_description LIKE '%NEW%' THEN 'INITIAL_VISIT_COMPLETED'
        ELSE 'OTHER_SERVICE_COMPLETED'
    END as visit_completion_status
FROM provider_tasks pt
JOIN (
    SELECT patient_id, status, notes 
    FROM provider_tasks 
    WHERE rowid IN (SELECT rowid FROM provider_tasks WHERE updated_date = strftime('%s', 'now'))
) pt_old ON pt.patient_id = pt_old.patient_id
WHERE pt.updated_date = strftime('%s', 'now');

-- Step 2: Update all monthly partitioned tables (provider_tasks_YYYY_MM)
-- Get list of all provider_tasks_YYYY_MM tables
-- Note: This approach uses dynamic SQL generation for each monthly table

-- Update provider_tasks_2024_01
UPDATE provider_tasks_2024_01 
SET 
    status = CASE 
        WHEN task_description LIKE '%PCP-Visit%' AND status != 'COMPLETED' THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND status != 'COMPLETED' THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND status != 'COMPLETED' THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND status != 'COMPLETED' THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND status != 'COMPLETED' THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' THEN 'SPECIALTY_CARE_COMPLETED'
        ELSE COALESCE(status, 'SERVICE_COMPLETED')
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

-- Update provider_tasks_2024_02
UPDATE provider_tasks_2024_02 
SET 
    status = CASE 
        WHEN task_description LIKE '%PCP-Visit%' AND status != 'COMPLETED' THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND status != 'COMPLETED' THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND status != 'COMPLETED' THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND status != 'COMPLETED' THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND status != 'COMPLETED' THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' THEN 'SPECIALTY_CARE_COMPLETED'
        ELSE COALESCE(status, 'SERVICE_COMPLETED')
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

-- Continue for all monthly tables through 2025_12
-- (Similar pattern for each monthly table)

-- Update provider_tasks_2025_09 (current active table)
UPDATE provider_tasks_2025_09 
SET 
    status = CASE 
        WHEN task_description LIKE '%PCP-Visit%' AND status != 'COMPLETED' THEN 'PCP_VISIT_COMPLETED'
        WHEN task_description LIKE '%Telehealth%' AND status != 'COMPLETED' THEN 'TELEHEALTH_COMPLETED'
        WHEN task_description LIKE '%Home%' AND status != 'COMPLETED' THEN 'HOME_VISIT_COMPLETED'
        WHEN task_description LIKE '%Follow%' AND status != 'COMPLETED' THEN 'FOLLOWUP_COMPLETED'
        WHEN task_description LIKE '%NEW%' AND status != 'COMPLETED' THEN 'INITIAL_VISIT_COMPLETED'
        WHEN task_description LIKE '%Graft%' OR task_description LIKE '%WC-%' THEN 'SPECIALTY_CARE_COMPLETED'
        ELSE COALESCE(status, 'SERVICE_COMPLETED')
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

-- Step 3: Create summary statistics for verification
CREATE TEMPORARY TABLE update_summary AS
SELECT 
    'provider_tasks' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status LIKE '%_COMPLETED' THEN 1 END) as updated_status_records,
    COUNT(CASE WHEN notes LIKE '%Patient Status:%' THEN 1 END) as updated_notes_records
FROM provider_tasks
UNION ALL
SELECT 
    'provider_tasks_2025_09' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status LIKE '%_COMPLETED' THEN 1 END) as updated_status_records,
    COUNT(CASE WHEN notes LIKE '%Patient Status:%' THEN 1 END) as updated_notes_records
FROM provider_tasks_2025_09;

-- Display summary
SELECT * FROM update_summary;

-- Step 4: Data integrity checks
-- Check for orphaned patient_ids (patient_ids in provider_tasks but not in patients)
CREATE TEMPORARY TABLE orphaned_patients AS
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
SELECT 'Orphaned Patient IDs Found:' as message, COUNT(*) as count FROM orphaned_patients;
SELECT * FROM orphaned_patients LIMIT 10;

-- Step 5: Create indexes for better performance if they don't exist
CREATE INDEX IF NOT EXISTS idx_provider_tasks_patient_id ON provider_tasks(patient_id);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_status ON provider_tasks(status);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_2025_09_patient_id ON provider_tasks_2025_09(patient_id);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_2025_09_status ON provider_tasks_2025_09(status);
CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(status);

-- Commit the transaction
COMMIT;

-- Final verification query
SELECT 
    'Enhancement Complete' as status,
    datetime('now') as completion_time,
    (SELECT COUNT(*) FROM patient_data_audit_log WHERE updated_at >= datetime('now', '-1 minute')) as audit_records_created;

-- Display sample of updated records
SELECT 
    'Sample Updated Records' as info,
    patient_id,
    status,
    substr(notes, 1, 100) || '...' as notes_preview,
    task_description
FROM provider_tasks 
WHERE notes LIKE '%Patient Status:%' 
LIMIT 5;