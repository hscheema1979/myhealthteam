-- Weekly Billing System Database Schema
-- This script creates the enhanced tables needed for the P00 Weekly Billing Report system

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS weekly_billing_reports;
DROP TABLE IF EXISTS provider_task_billing_status;
DROP TABLE IF EXISTS billing_status_history;

-- Create the main weekly billing reports table
CREATE TABLE weekly_billing_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_week TEXT NOT NULL, -- Format: YYYY-WW (e.g., "2025-01")
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    report_generated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_tasks INTEGER DEFAULT 0,
    total_billed_tasks INTEGER DEFAULT 0,
    total_carried_over_tasks INTEGER DEFAULT 0,
    report_status TEXT DEFAULT 'DRAFT', -- DRAFT, FINALIZED, SUBMITTED
    created_by INTEGER,
    notes TEXT,
    UNIQUE(billing_week)
);

-- Enhanced provider task billing status table
CREATE TABLE provider_task_billing_status (
    billing_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_task_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    patient_id TEXT,
    patient_name TEXT,
    task_date TEXT NOT NULL,
    billing_week TEXT NOT NULL, -- Format: YYYY-WW
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    
    -- Task details
    task_description TEXT,
    minutes_of_service INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    
    -- Billing status progression
    billing_status TEXT DEFAULT 'Not Billed', -- Not Billed, Billed, Invoiced, Claim Submitted, Insurance Processed, Approve to Pay, Paid
    
    -- Status flags for tracking
    is_billed BOOLEAN DEFAULT FALSE,
    is_invoiced BOOLEAN DEFAULT FALSE,
    is_claim_submitted BOOLEAN DEFAULT FALSE,
    is_insurance_processed BOOLEAN DEFAULT FALSE,
    is_approved_to_pay BOOLEAN DEFAULT FALSE,
    is_paid BOOLEAN DEFAULT FALSE,
    
    -- Carryover tracking
    is_carried_over BOOLEAN DEFAULT FALSE,
    original_billing_week TEXT, -- Original week if carried over
    carryover_reason TEXT,
    
    -- External system integration
    external_invoice_id TEXT,
    external_claim_id TEXT,
    external_payment_id TEXT,
    
    -- Timestamps
    billed_date DATETIME,
    invoiced_date DATETIME,
    claim_submitted_date DATETIME,
    insurance_processed_date DATETIME,
    approved_to_pay_date DATETIME,
    paid_date DATETIME,
    
    -- Audit fields
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    
    -- Notes and comments
    billing_notes TEXT,
    payment_notes TEXT,
    
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    UNIQUE(provider_task_id, billing_week)
);

-- Billing status history for audit trail
CREATE TABLE billing_status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_status_id INTEGER NOT NULL,
    provider_task_id INTEGER NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    change_reason TEXT,
    changed_by INTEGER,
    change_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    additional_notes TEXT,
    
    FOREIGN KEY (billing_status_id) REFERENCES provider_task_billing_status(billing_status_id)
);

-- Create indexes for performance
CREATE INDEX idx_provider_task_billing_status_provider ON provider_task_billing_status(provider_id);
CREATE INDEX idx_provider_task_billing_status_week ON provider_task_billing_status(billing_week);
CREATE INDEX idx_provider_task_billing_status_status ON provider_task_billing_status(billing_status);
CREATE INDEX idx_provider_task_billing_status_task_date ON provider_task_billing_status(task_date);
CREATE INDEX idx_provider_task_billing_status_billed ON provider_task_billing_status(is_billed);
CREATE INDEX idx_provider_task_billing_status_paid ON provider_task_billing_status(is_paid);
CREATE INDEX idx_provider_task_billing_status_carryover ON provider_task_billing_status(is_carried_over);

CREATE INDEX idx_weekly_billing_reports_week ON weekly_billing_reports(billing_week);
CREATE INDEX idx_weekly_billing_reports_year_week ON weekly_billing_reports(year, week_number);

CREATE INDEX idx_billing_status_history_billing_id ON billing_status_history(billing_status_id);
CREATE INDEX idx_billing_status_history_task_id ON billing_status_history(provider_task_id);
CREATE INDEX idx_billing_status_history_date ON billing_status_history(change_date);

-- Create a view for easy reporting
DROP VIEW IF EXISTS v_weekly_billing_summary;
CREATE VIEW v_weekly_billing_summary AS
SELECT 
    wb.billing_week,
    wb.week_start_date,
    wb.week_end_date,
    wb.year,
    wb.week_number,
    wb.report_status,
    
    -- Task counts
    COUNT(pbs.billing_status_id) as total_tasks,
    COUNT(CASE WHEN pbs.is_billed = 1 THEN 1 END) as billed_tasks,
    COUNT(CASE WHEN pbs.is_invoiced = 1 THEN 1 END) as invoiced_tasks,
    COUNT(CASE WHEN pbs.is_claim_submitted = 1 THEN 1 END) as claim_submitted_tasks,
    COUNT(CASE WHEN pbs.is_insurance_processed = 1 THEN 1 END) as insurance_processed_tasks,
    COUNT(CASE WHEN pbs.is_approved_to_pay = 1 THEN 1 END) as approved_to_pay_tasks,
    COUNT(CASE WHEN pbs.is_paid = 1 THEN 1 END) as paid_tasks,
    COUNT(CASE WHEN pbs.is_carried_over = 1 THEN 1 END) as carried_over_tasks,
    
    -- Financial totals
    SUM(pbs.minutes_of_service) as total_minutes,
    
    -- Status breakdown
    COUNT(CASE WHEN pbs.billing_status = 'Not Billed' THEN 1 END) as not_billed_count,
    COUNT(CASE WHEN pbs.billing_status = 'Billed' THEN 1 END) as billed_count,
    COUNT(CASE WHEN pbs.billing_status = 'Invoiced' THEN 1 END) as invoiced_count,
    COUNT(CASE WHEN pbs.billing_status = 'Claim Submitted' THEN 1 END) as claim_submitted_count,
    COUNT(CASE WHEN pbs.billing_status = 'Insurance Processed' THEN 1 END) as insurance_processed_count,
    COUNT(CASE WHEN pbs.billing_status = 'Approve to Pay' THEN 1 END) as approve_to_pay_count,
    COUNT(CASE WHEN pbs.billing_status = 'Paid' THEN 1 END) as paid_count,
    
    wb.report_generated_date,
    wb.created_by,
    wb.notes

FROM weekly_billing_reports wb
LEFT JOIN provider_task_billing_status pbs ON wb.billing_week = pbs.billing_week
GROUP BY wb.billing_week, wb.week_start_date, wb.week_end_date, wb.year, wb.week_number, 
         wb.report_status, wb.report_generated_date, wb.created_by, wb.notes;

-- Insert initial data comment
-- This schema supports the full P00 Weekly Billing Report workflow:
-- 1. Tasks start as "Not Billed"
-- 2. On Saturday of billing week, eligible tasks are marked as "Billed"
-- 3. Tasks progress through: Invoiced -> Claim Submitted -> Insurance Processed -> Approve to Pay -> Paid
-- 4. "Not Billed" tasks from previous weeks are carried over to the next billing cycle
-- 5. Full audit trail is maintained for all status changes