-- Add Billing Tracking Columns to provider_tasks Table
-- This script adds comprehensive billing status tracking directly to the provider_tasks table

-- Add billing status tracking columns
ALTER TABLE provider_tasks ADD COLUMN billing_status TEXT DEFAULT 'Not Billed';
ALTER TABLE provider_tasks ADD COLUMN is_billed INTEGER DEFAULT 0;
ALTER TABLE provider_tasks ADD COLUMN is_invoiced INTEGER DEFAULT 0;
ALTER TABLE provider_tasks ADD COLUMN is_claim_submitted INTEGER DEFAULT 0;
ALTER TABLE provider_tasks ADD COLUMN is_insurance_processed INTEGER DEFAULT 0;
ALTER TABLE provider_tasks ADD COLUMN is_approved_to_pay INTEGER DEFAULT 0;
ALTER TABLE provider_tasks ADD COLUMN is_paid INTEGER DEFAULT 0;
ALTER TABLE provider_tasks ADD COLUMN is_carried_over INTEGER DEFAULT 0;

-- Add billing week tracking
ALTER TABLE provider_tasks ADD COLUMN billing_week TEXT;
ALTER TABLE provider_tasks ADD COLUMN original_billing_week TEXT;

-- Add billing dates
ALTER TABLE provider_tasks ADD COLUMN billed_date DATETIME;
ALTER TABLE provider_tasks ADD COLUMN invoiced_date DATETIME;
ALTER TABLE provider_tasks ADD COLUMN claim_submitted_date DATETIME;
ALTER TABLE provider_tasks ADD COLUMN insurance_processed_date DATETIME;
ALTER TABLE provider_tasks ADD COLUMN approved_to_pay_date DATETIME;
ALTER TABLE provider_tasks ADD COLUMN paid_date DATETIME;

-- Add billing notes and reason tracking
ALTER TABLE provider_tasks ADD COLUMN billing_notes TEXT;
ALTER TABLE provider_tasks ADD COLUMN carryover_reason TEXT;

-- Populate billing_week and original_billing_week for existing records
UPDATE provider_tasks 
SET billing_week = strftime('%Y-%W', task_date),
    original_billing_week = strftime('%Y-%W', task_date)
WHERE task_date IS NOT NULL;

-- Set initial billing status based on billing_code
UPDATE provider_tasks 
SET billing_status = CASE 
    WHEN billing_code IS NULL OR billing_code = '' OR billing_code = 'Not_Billable' THEN 'Not Billable'
    ELSE 'Not Billed'
END;

-- Create index for better performance on billing queries
CREATE INDEX IF NOT EXISTS idx_provider_tasks_billing_week ON provider_tasks(billing_week);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_billing_status ON provider_tasks(billing_status);
CREATE INDEX IF NOT EXISTS idx_provider_tasks_is_billed ON provider_tasks(is_billed);

-- Verification queries
SELECT 'Column Addition Summary' as description;

SELECT 
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN billing_status = 'Not Billed' THEN 1 END) as not_billed,
    COUNT(CASE WHEN billing_status = 'Not Billable' THEN 1 END) as not_billable,
    COUNT(CASE WHEN billing_status = 'Billed' THEN 1 END) as billed,
    COUNT(DISTINCT billing_week) as total_weeks,
    MIN(task_date) as earliest_task,
    MAX(task_date) as latest_task
FROM provider_tasks;

-- Show recent weeks summary
SELECT 
    billing_week,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN billing_status = 'Not Billed' THEN 1 END) as not_billed,
    COUNT(CASE WHEN billing_status = 'Not Billable' THEN 1 END) as not_billable,
    COUNT(CASE WHEN is_billed = 1 THEN 1 END) as billed_tasks
FROM provider_tasks
WHERE billing_week IS NOT NULL
GROUP BY billing_week
ORDER BY billing_week DESC
LIMIT 10;