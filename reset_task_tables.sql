-- RESET TASK TABLES WITH PROPER UNIQUE CONSTRAINTS
-- This script drops all coordinator_tasks_* and provider_tasks_* tables
-- and recreates them with UNIQUE constraints to prevent duplicates
-- WARNING: This will DELETE ALL TASK DATA
-- Make sure you have backups before running!
-- Drop all coordinator task tables
DROP TABLE IF EXISTS coordinator_tasks_1999_12;
DROP TABLE IF EXISTS coordinator_tasks_2022_01;
DROP TABLE IF EXISTS coordinator_tasks_2025_01;
DROP TABLE IF EXISTS coordinator_tasks_2025_02;
DROP TABLE IF EXISTS coordinator_tasks_2025_03;
DROP TABLE IF EXISTS coordinator_tasks_2025_04;
DROP TABLE IF EXISTS coordinator_tasks_2025_05;
DROP TABLE IF EXISTS coordinator_tasks_2025_06;
DROP TABLE IF EXISTS coordinator_tasks_2025_07;
DROP TABLE IF EXISTS coordinator_tasks_2025_08;
DROP TABLE IF EXISTS coordinator_tasks_2025_09;
DROP TABLE IF EXISTS coordinator_tasks_2025_10;
DROP TABLE IF EXISTS coordinator_tasks_2025_11;
DROP TABLE IF EXISTS coordinator_tasks_2025_12;
-- Drop all provider task tables
DROP TABLE IF EXISTS provider_tasks_2001_01;
DROP TABLE IF EXISTS provider_tasks_2023_05;
DROP TABLE IF EXISTS provider_tasks_2023_06;
DROP TABLE IF EXISTS provider_tasks_2023_07;
DROP TABLE IF EXISTS provider_tasks_2023_10;
DROP TABLE IF EXISTS provider_tasks_2023_11;
DROP TABLE IF EXISTS provider_tasks_2023_12;
DROP TABLE IF EXISTS provider_tasks_2024_01;
DROP TABLE IF EXISTS provider_tasks_2024_02;
DROP TABLE IF EXISTS provider_tasks_2024_03;
DROP TABLE IF EXISTS provider_tasks_2024_04;
DROP TABLE IF EXISTS provider_tasks_2024_05;
DROP TABLE IF EXISTS provider_tasks_2024_06;
DROP TABLE IF EXISTS provider_tasks_2024_07;
DROP TABLE IF EXISTS provider_tasks_2024_08;
DROP TABLE IF EXISTS provider_tasks_2024_09;
DROP TABLE IF EXISTS provider_tasks_2024_10;
DROP TABLE IF EXISTS provider_tasks_2024_11;
DROP TABLE IF EXISTS provider_tasks_2024_12;
DROP TABLE IF EXISTS provider_tasks_2025_01;
DROP TABLE IF EXISTS provider_tasks_2025_02;
DROP TABLE IF EXISTS provider_tasks_2025_03;
DROP TABLE IF EXISTS provider_tasks_2025_04;
DROP TABLE IF EXISTS provider_tasks_2025_05;
DROP TABLE IF EXISTS provider_tasks_2025_06;
DROP TABLE IF EXISTS provider_tasks_2025_07;
DROP TABLE IF EXISTS provider_tasks_2025_08;
DROP TABLE IF EXISTS provider_tasks_2025_09;
DROP TABLE IF EXISTS provider_tasks_2025_10;
DROP TABLE IF EXISTS provider_tasks_2025_11;
DROP TABLE IF EXISTS provider_tasks_2025_12;
-- Also drop dependent tables that will be recreated
DROP TABLE IF EXISTS coordinator_monthly_summary;
DROP TABLE IF EXISTS provider_task_billing_status;
DROP TABLE IF EXISTS provider_weekly_payroll_status;
-- Recreate summary tables with proper schemas
CREATE TABLE coordinator_monthly_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id INTEGER,
    coordinator_name TEXT,
    patient_id TEXT,
    patient_name TEXT,
    year INTEGER,
    month INTEGER,
    month_start_date DATE,
    month_end_date DATE,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    billing_status TEXT DEFAULT 'Pending',
    is_billed BOOLEAN DEFAULT FALSE,
    billed_date DATE,
    billed_by INTEGER,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE provider_task_billing_status (
    billing_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_task_id INTEGER,
    provider_id INTEGER,
    provider_name TEXT,
    patient_name TEXT,
    task_date DATE,
    billing_week INTEGER,
    week_start_date DATE,
    week_end_date DATE,
    task_description TEXT,
    minutes_of_service INTEGER,
    billing_code TEXT,
    billing_code_description TEXT,
    billing_status TEXT DEFAULT 'Pending',
    is_billed BOOLEAN DEFAULT FALSE,
    is_invoiced BOOLEAN DEFAULT FALSE,
    is_claim_submitted BOOLEAN DEFAULT FALSE,
    is_insurance_processed BOOLEAN DEFAULT FALSE,
    is_approved_to_pay BOOLEAN DEFAULT FALSE,
    is_paid BOOLEAN DEFAULT FALSE,
    is_carried_over BOOLEAN DEFAULT FALSE,
    original_billing_week INTEGER,
    carryover_reason TEXT,
    billing_notes TEXT,
    billed_date DATE,
    invoiced_date DATE,
    claim_submitted_date DATE,
    insurance_processed_date DATE,
    approved_to_pay_date DATE,
    paid_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE provider_weekly_payroll_status (
    payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER,
    provider_name TEXT,
    pay_week_start_date DATE,
    pay_week_end_date DATE,
    pay_week_number INTEGER,
    pay_year INTEGER,
    visit_type TEXT,
    task_count INTEGER DEFAULT 0,
    total_minutes_of_service INTEGER DEFAULT 0,
    payroll_status TEXT DEFAULT 'Pending',
    is_approved BOOLEAN DEFAULT FALSE,
    approved_date DATE,
    approved_by INTEGER,
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATE,
    paid_by INTEGER,
    payment_method TEXT,
    payment_reference TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Create indexes for performance
CREATE INDEX idx_coordinator_monthly_summary_coordinator_year_month ON coordinator_monthly_summary(coordinator_id, year, month);
CREATE INDEX idx_provider_billing_status_provider_task ON provider_task_billing_status(provider_task_id);
CREATE INDEX idx_provider_payroll_provider_week ON provider_weekly_payroll_status(provider_id, pay_week_start_date);