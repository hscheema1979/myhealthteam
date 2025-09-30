-- Create coordinator monthly summary tables for billing and monitoring
-- This script creates the required summary tables for coordinators
-- Drop existing tables if they exist
DROP TABLE IF EXISTS coordinator_monthly_summary_2025_09;
DROP TABLE IF EXISTS coordinator_minutes_2025_09;
DROP TABLE IF EXISTS provider_weekly_summary_2025_35;
-- 1. Coordinator Monthly Summary (patient minutes per coordinator)
CREATE TABLE coordinator_monthly_summary_2025_09 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id INTEGER NOT NULL,
    coordinator_name TEXT,
    patient_id TEXT NOT NULL,
    patient_name TEXT,
    year INTEGER NOT NULL DEFAULT 2025,
    month INTEGER NOT NULL DEFAULT 9,
    total_minutes INTEGER NOT NULL,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP
);
-- 2. Coordinator Minutes Summary (total minutes per coordinator)
CREATE TABLE coordinator_minutes_2025_09 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id INTEGER NOT NULL,
    coordinator_name TEXT,
    year INTEGER NOT NULL DEFAULT 2025,
    month INTEGER NOT NULL DEFAULT 9,
    total_minutes INTEGER NOT NULL,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP
);
-- 3. Provider Weekly Summary
CREATE TABLE provider_weekly_summary_2025_35 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL DEFAULT 2025,
    week_number INTEGER NOT NULL DEFAULT 35,
    total_tasks_completed INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP
);
-- Note: last_visit columns already exist in patient_panel