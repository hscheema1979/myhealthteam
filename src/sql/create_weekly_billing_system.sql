-- Create weekly billing system tables
-- This script sets up the provider_task_billing_status table and related structures
-- Create provider_task_billing_status table if it doesn't exist
CREATE TABLE IF NOT EXISTS provider_task_billing_status (
    billing_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_task_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    task_date TEXT NOT NULL,
    billing_week TEXT NOT NULL,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    task_description TEXT NOT NULL,
    minutes_of_service INTEGER NOT NULL,
    billing_code TEXT,
    billing_code_description TEXT,
    billing_status TEXT DEFAULT 'Pending' NOT NULL,
    is_billed INTEGER DEFAULT 0 NOT NULL,
    billed_date TEXT,
    billed_by INTEGER,
    is_invoiced INTEGER DEFAULT 0 NOT NULL,
    invoiced_date TEXT,
    is_claim_submitted INTEGER DEFAULT 0 NOT NULL,
    claim_submitted_date TEXT,
    is_insurance_processed INTEGER DEFAULT 0 NOT NULL,
    insurance_processed_date TEXT,
    is_approved_to_pay INTEGER DEFAULT 0 NOT NULL,
    approved_to_pay_date TEXT,
    is_paid INTEGER DEFAULT 0 NOT NULL,
    paid_date TEXT,
    is_carried_over INTEGER DEFAULT 0 NOT NULL,
    original_billing_week TEXT,
    carryover_reason TEXT,
    billing_notes TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    billing_company TEXT
);
-- Create weekly_billing_reports table for summary data
CREATE TABLE IF NOT EXISTS weekly_billing_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_week TEXT NOT NULL UNIQUE,
    total_tasks INTEGER DEFAULT 0 NOT NULL,
    total_billed_tasks INTEGER DEFAULT 0 NOT NULL,
    total_carried_over_tasks INTEGER DEFAULT 0 NOT NULL,
    report_status TEXT DEFAULT 'Generated' NOT NULL,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Create billing_status_history table for audit trail
CREATE TABLE IF NOT EXISTS billing_status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_status_id INTEGER NOT NULL,
    provider_task_id INTEGER NOT NULL,
    previous_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    change_reason TEXT,
    changed_by INTEGER,
    additional_notes TEXT,
    change_date TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_provider_id ON provider_task_billing_status(provider_id);
CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billing_week ON provider_task_billing_status(billing_week);
CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_task_date ON provider_task_billing_status(task_date);
CREATE INDEX IF NOT EXISTS idx_weekly_billing_reports_billing_week ON weekly_billing_reports(billing_week);