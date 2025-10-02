-- Populate Weekly Billing System with Existing Data
-- This script migrates existing provider task data into the new weekly billing system

-- Function to calculate billing week in YYYY-WW format
-- Week starts on Monday, and we use ISO week numbering

-- First, let's create a function to get the billing week
-- Since SQLite doesn't have custom functions, we'll use a complex CASE statement

-- Clear existing data (if any)
DELETE FROM provider_task_billing_status;
DELETE FROM weekly_billing_reports;

-- Populate provider_task_billing_status with existing provider tasks
-- We need to union data from all monthly provider_tasks tables
WITH all_provider_tasks AS (
    -- Union all monthly provider task tables
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_09
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_08
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_07
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_06
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_05
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_04
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_03
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_02
    WHERE provider_task_id IS NOT NULL
    
    UNION ALL
    
    SELECT provider_task_id, task_id, provider_id, patient_id, status, minutes_of_service, billing_code, task_date, created_date, task_description, billing_code_description, provider_name, patient_name, notes
    FROM provider_tasks_2025_01
    WHERE provider_task_id IS NOT NULL
)
INSERT OR IGNORE INTO provider_task_billing_status (
    provider_task_id,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    billing_week,
    week_start_date,
    week_end_date,
    task_description,
    minutes_of_service,
    billing_code,
    billing_code_description,
    billing_status,
    is_billed,
    is_invoiced,
    is_claim_submitted,
    is_insurance_processed,
    is_approved_to_pay,
    is_paid,
    created_date,
    billing_notes
)
SELECT 
    pt.provider_task_id,
    CAST(pt.provider_id AS INTEGER) as provider_id,
    pt.provider_name,
    pt.patient_id,
    pt.patient_name,
    pt.task_date,
    
    -- Calculate billing week (YYYY-WW format)
    CAST(strftime('%Y', pt.task_date) AS TEXT) || '-' || 
    CASE 
        WHEN CAST(strftime('%W', pt.task_date) AS INTEGER) < 10 
        THEN '0' || CAST(strftime('%W', pt.task_date) AS INTEGER)
        ELSE CAST(strftime('%W', pt.task_date) AS TEXT)
    END as billing_week,
    
    -- Calculate week start date (Monday)
    DATE(pt.task_date, '-' || ((strftime('%w', pt.task_date) + 6) % 7) || ' days') as week_start_date,
    
    -- Calculate week end date (Sunday)
    DATE(pt.task_date, '+' || (6 - ((strftime('%w', pt.task_date) + 6) % 7)) || ' days') as week_end_date,
    
    pt.task_description,
    COALESCE(pt.minutes_of_service, 0) as minutes_of_service,
    pt.billing_code,
    pt.billing_code_description,
    
    -- Determine initial billing status based on existing data
    CASE 
        WHEN pt.billing_code IS NULL OR pt.billing_code = '' OR pt.billing_code = 'Not_Billable' THEN 'Not Billed'
        WHEN pt.status = 'COMPLETED' AND pt.billing_code IS NOT NULL AND pt.billing_code != '' THEN 'Billed'
        ELSE 'Not Billed'
    END as billing_status,
    
    -- Set flags based on status
    CASE 
        WHEN pt.status = 'COMPLETED' AND pt.billing_code IS NOT NULL AND pt.billing_code != '' AND pt.billing_code != 'Not_Billable' THEN 1
        ELSE 0
    END as is_billed,
    
    0 as is_invoiced, -- Default to false, will be updated from external systems
    0 as is_claim_submitted,
    0 as is_insurance_processed,
    0 as is_approved_to_pay,
    0 as is_paid,
    
    COALESCE(pt.created_date, CURRENT_TIMESTAMP) as created_date,
    pt.notes as billing_notes

FROM all_provider_tasks pt
WHERE pt.task_date IS NOT NULL 
    AND pt.task_date != ''
    AND LENGTH(pt.task_date) = 10
    AND SUBSTR(pt.task_date, 5, 1) = '-'
    AND SUBSTR(pt.task_date, 8, 1) = '-'
    AND CAST(strftime('%Y', pt.task_date) AS INTEGER) >= 2025  -- Only include 2025 data
    AND pt.provider_id IS NOT NULL
    AND pt.provider_id != '';

-- Create weekly billing reports for each unique week
INSERT INTO weekly_billing_reports (
    billing_week,
    week_start_date,
    week_end_date,
    year,
    week_number,
    total_tasks,
    total_billed_tasks,
    total_carried_over_tasks,
    report_status,
    report_generated_date
)
SELECT 
    pbs.billing_week,
    pbs.week_start_date,
    pbs.week_end_date,
    CAST(strftime('%Y', pbs.week_start_date) AS INTEGER) as year,
    CAST(strftime('%W', pbs.week_start_date) AS INTEGER) as week_number,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN pbs.is_billed = 1 THEN 1 END) as total_billed_tasks,
    0 as total_carried_over_tasks, -- Will be calculated in the weekly process
    
    -- Set report status based on week
    CASE 
        WHEN pbs.week_start_date < DATE('now', '-7 days') THEN 'FINALIZED'
        WHEN pbs.week_start_date < DATE('now') THEN 'DRAFT'
        ELSE 'DRAFT'
    END as report_status,
    
    CURRENT_TIMESTAMP as report_generated_date

FROM provider_task_billing_status pbs
GROUP BY pbs.billing_week, pbs.week_start_date, pbs.week_end_date
ORDER BY pbs.billing_week;

-- Update billed_date for tasks that are already marked as billed
UPDATE provider_task_billing_status 
SET billed_date = DATETIME(week_end_date || ' 23:59:59')  -- Set to end of billing week (Saturday)
WHERE is_billed = 1;

-- Create a summary of the migration
SELECT 
    'Migration Summary' as description,
    COUNT(*) as total_tasks_migrated,
    COUNT(CASE WHEN billing_status = 'Billed' THEN 1 END) as billed_tasks,
    COUNT(CASE WHEN billing_status = 'Not Billed' THEN 1 END) as not_billed_tasks,
    COUNT(DISTINCT billing_week) as total_weeks,
    MIN(task_date) as earliest_task_date,
    MAX(task_date) as latest_task_date
FROM provider_task_billing_status;

-- Show weekly summary
SELECT 
    billing_week,
    week_start_date,
    week_end_date,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN is_billed = 1 THEN 1 END) as billed_tasks,
    COUNT(CASE WHEN billing_status = 'Not Billed' THEN 1 END) as not_billed_tasks,
    SUM(minutes_of_service) as total_minutes
FROM provider_task_billing_status
GROUP BY billing_week, week_start_date, week_end_date
ORDER BY billing_week DESC
LIMIT 10;