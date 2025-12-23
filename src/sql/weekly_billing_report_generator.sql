-- Weekly Billing Report Generator (P00)
-- This script generates the weekly billing report and handles carryover logic
-- Run this script every Saturday to process the billing week

-- Parameters (these would be passed in from the Python script)
-- @current_billing_week: Format YYYY-WW (e.g., '2025-01')
-- @week_start_date: Format YYYY-MM-DD
-- @week_end_date: Format YYYY-MM-DD

-- For testing purposes, we'll use current week
-- In production, these would be parameters

-- Step 1: Create carryover entries for unbilled tasks from previous weeks
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
    is_carried_over,
    original_billing_week,
    carryover_reason,
    created_date,
    billing_notes
)
SELECT 
    pbs.provider_task_id,
    pbs.provider_id,
    pbs.provider_name,
    pbs.patient_id,
    pbs.patient_name,
    pbs.task_date,
    -- Calculate current billing week
    CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
    CASE 
        WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
        THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
        ELSE CAST(strftime('%W', 'now') AS TEXT)
    END as billing_week,
    DATE('now', '-' || ((strftime('%w', 'now') + 6) % 7) || ' days') as week_start_date,
    DATE('now', '+' || (6 - ((strftime('%w', 'now') + 6) % 7)) || ' days') as week_end_date,
    pbs.task_description,
    pbs.minutes_of_service,
    pbs.billing_code,
    pbs.billing_code_description,
    'Not Billed' as billing_status,
    0 as is_billed,
    1 as is_carried_over,
    pbs.billing_week as original_billing_week,
    'Carried over from week ' || pbs.billing_week || ' - not billed in original week' as carryover_reason,
    CURRENT_TIMESTAMP as created_date,
    'CARRYOVER: ' || COALESCE(pbs.billing_notes, '') as billing_notes
FROM provider_task_billing_status pbs
WHERE pbs.billing_status = 'Not Billed'
    AND pbs.billing_week < (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
    )
    AND pbs.is_carried_over = 0;  -- Not already carried over

-- Step 2: Mark original tasks as carried over
UPDATE provider_task_billing_status 
SET is_carried_over = 1,
    updated_date = CURRENT_TIMESTAMP,
    billing_notes = COALESCE(billing_notes, '') || ' [CARRIED OVER TO ' || 
        (CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END) || ']'
WHERE billing_status = 'Not Billed'
    AND billing_week < (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
    )
    AND is_carried_over = 0;

-- Step 3: Process current week's tasks - Mark eligible tasks as "Billed"
-- This happens on Saturday of the billing week
UPDATE provider_task_billing_status 
SET billing_status = 'Billed',
    is_billed = 1,
    billed_date = CURRENT_TIMESTAMP,
    updated_date = CURRENT_TIMESTAMP
WHERE billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
    )
    AND billing_status = 'Not Billed'
    AND billing_code IS NOT NULL 
    AND billing_code != '' 
    AND billing_code != 'Not_Billable'
    AND minutes_of_service > 0;

-- Step 4: Create or update the weekly billing report
INSERT OR REPLACE INTO weekly_billing_reports (
    billing_week,
    week_start_date,
    week_end_date,
    year,
    week_number,
    total_tasks,
    total_billed_tasks,
    total_carried_over_tasks,
    report_status,
    report_generated_date,
    notes
)
SELECT 
    -- Calculate current billing week
    CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
    CASE 
        WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
        THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
        ELSE CAST(strftime('%W', 'now') AS TEXT)
    END as billing_week,
    DATE('now', '-' || ((strftime('%w', 'now') + 6) % 7) || ' days') as week_start_date,
    DATE('now', '+' || (6 - ((strftime('%w', 'now') + 6) % 7)) || ' days') as week_end_date,
    CAST(strftime('%Y', 'now') AS INTEGER) as year,
    CAST(strftime('%W', 'now') AS INTEGER) as week_number,
    
    -- Count all tasks for this billing week
    (SELECT COUNT(*) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )) as total_tasks,
    
    -- Count billed tasks
    (SELECT COUNT(*) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )
       AND pbs.is_billed = 1) as total_billed_tasks,
    
    -- Count carried over tasks
    (SELECT COUNT(*) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )
       AND pbs.is_carried_over = 1) as total_carried_over_tasks,
    
    'FINALIZED' as report_status,
    CURRENT_TIMESTAMP as report_generated_date,
    'Weekly billing report generated on ' || DATE('now') || '. Carryover tasks processed.' as notes;

-- Step 6: Log status changes in history table
INSERT INTO billing_status_history (
    billing_status_id,
    provider_task_id,
    previous_status,
    new_status,
    change_reason,
    changed_by,
    change_date,
    additional_notes
)
SELECT 
    pbs.billing_status_id,
    pbs.provider_task_id,
    'Not Billed' as previous_status,
    'Billed' as new_status,
    'Weekly billing report processing - Saturday billing cycle' as change_reason,
    1 as changed_by, -- System user ID
    CURRENT_TIMESTAMP as change_date,
    'Automatically billed during week ' || pbs.billing_week || ' processing' as additional_notes
FROM provider_task_billing_status pbs
WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
    )
    AND pbs.is_billed = 1
    AND pbs.billed_date >= DATE('now');

-- Step 5: Generate summary report for review
SELECT 
    'WEEKLY BILLING REPORT SUMMARY' as report_type,
    -- Calculate current billing week
    CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
    CASE 
        WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
        THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
        ELSE CAST(strftime('%W', 'now') AS TEXT)
    END as billing_week,
    DATE('now', '-' || ((strftime('%w', 'now') + 6) % 7) || ' days') as week_start_date,
    DATE('now', '+' || (6 - ((strftime('%w', 'now') + 6) % 7)) || ' days') as week_end_date,
    
    -- Current week statistics
    (SELECT COUNT(*) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )) as total_tasks_this_week,
    
    (SELECT COUNT(*) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )
       AND pbs.is_billed = 1) as billed_tasks_this_week,
    
    (SELECT COUNT(*) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )
       AND pbs.billing_status = 'Not Billed') as not_billed_tasks_this_week,
    
    (SELECT COUNT(*) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )
       AND pbs.is_carried_over = 1) as carried_over_tasks_this_week,
    
    -- Financial summary
    (SELECT SUM(pbs.minutes_of_service) 
     FROM provider_task_billing_status pbs 
     WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
     )
       AND pbs.is_billed = 1) as total_billable_minutes,
    
    CURRENT_TIMESTAMP as report_generated_at;

-- Step 6: Provider-level summary for the current week
SELECT 
    'PROVIDER SUMMARY' as report_type,
    pbs.provider_id,
    pbs.provider_name,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN pbs.is_billed = 1 THEN 1 END) as billed_tasks,
    COUNT(CASE WHEN pbs.billing_status = 'Not Billed' THEN 1 END) as not_billed_tasks,
    COUNT(CASE WHEN pbs.is_carried_over = 1 THEN 1 END) as carried_over_tasks,
    SUM(pbs.minutes_of_service) as total_minutes,
    SUM(CASE WHEN pbs.is_billed = 1 THEN pbs.minutes_of_service ELSE 0 END) as billable_minutes
FROM provider_task_billing_status pbs
WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
    )
GROUP BY pbs.provider_id, pbs.provider_name
ORDER BY pbs.provider_name;

-- Step 7: Tasks requiring attention (not billed and not billable)
SELECT 
    'TASKS REQUIRING ATTENTION' as report_type,
    pbs.provider_task_id,
    pbs.provider_name,
    pbs.patient_name,
    pbs.task_date,
    pbs.task_description,
    pbs.billing_code,
    pbs.minutes_of_service,
    pbs.billing_status,
    CASE 
        WHEN pbs.billing_code IS NULL OR pbs.billing_code = '' THEN 'Missing billing code'
        WHEN pbs.billing_code = 'Not_Billable' THEN 'Marked as not billable'
        WHEN pbs.minutes_of_service = 0 THEN 'Zero minutes of service'
        ELSE 'Other issue'
    END as attention_reason
FROM provider_task_billing_status pbs
WHERE pbs.billing_week = (
        CAST(strftime('%Y', 'now') AS TEXT) || '-' || 
        CASE 
            WHEN CAST(strftime('%W', 'now') AS INTEGER) < 10 
            THEN '0' || CAST(strftime('%W', 'now') AS INTEGER)
            ELSE CAST(strftime('%W', 'now') AS TEXT)
        END
    )
    AND pbs.billing_status = 'Not Billed'
    AND pbs.is_billed = 0
