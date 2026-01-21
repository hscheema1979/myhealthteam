-- =============================================================================
-- CSV Billing Tables - Source of Truth for Billing
-- These tables are populated ONLY by ETL from CSV files
-- They are READ-ONLY after import (no web UI updates)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: csv_coordinator_tasks_YYYY_MM
-- Source: CMLog_*.csv (coordinator work) + RVZ_ZEN-*.csv (provider phone reviews)
-- Contains: All coordinator work + provider phone reviews for billing
--
-- Raw CSV columns preserved for audit/reconciliation
-- -----------------------------------------------------------------------------
-- Example table for December 2025 (this template will be used by ETL)
CREATE TABLE IF NOT EXISTS csv_coordinator_tasks_2025_12 (
    csv_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Staff identification
    staff_code TEXT NOT NULL,              -- Original staff code from CSV (e.g., "SumLa000", "ZEN-SZA")
    staff_id INTEGER,                      -- Mapped staff_id from users table (via staff_code_mapping)
    staff_name TEXT,                       -- Staff full name from users table
    -- Patient identification
    patient_id TEXT NOT NULL,              -- Patient name/ID from CSV
    patient_dob TEXT,                      -- Patient DOB from "Last, First DOB" column
    -- Task details
    task_date DATE NOT NULL,               -- Date of service from "Date Only" column
    duration_minutes REAL NOT NULL,        -- Final duration in minutes (max of Mins B, ZEN, Total Mins)
    mins_b_value REAL DEFAULT 0,           -- Raw "Mins B" column value (for audit)
    zen_value REAL DEFAULT 0,              -- Raw "ZEN" column value (for audit)
    total_mins_value REAL DEFAULT 0,       -- Raw "Total Mins" column value (for audit)
    task_type TEXT,                        -- Type of task from "Type" column
    notes TEXT,                            -- Notes from "Notes" column
    current_status TEXT,                   -- Status from "Current" column
    -- Time tracking (optional, for audit)
    start_time_b TEXT,                     -- Start time from "Start Time B" column
    stop_time_b TEXT,                      -- Stop time from "Stop Time B" column
    start_time_a TEXT,                     -- Start time from "Start Time A" column (RVZ files)
    stop_time_a TEXT,                      -- Stop time from "Stop Time A" column (RVZ files)
    -- Source tracking
    source_file TEXT NOT NULL,             -- Original CSV filename (e.g., "CMLog_SumLa000.csv")
    source_system TEXT DEFAULT 'CSV_IMPORT', -- Source system identifier
    source_type TEXT NOT NULL,             -- 'CMLOG' or 'RVZ' - indicates file type
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Billing workflow fields
    billing_status TEXT DEFAULT 'Pending',  -- Pending, Billed, Invoiced, Paid, etc.
    is_billed INTEGER DEFAULT 0,
    billed_date DATE,
    billed_by INTEGER,
    invoice_id TEXT,
    is_paid INTEGER DEFAULT 0,
    paid_date DATE,
    billing_notes TEXT
);
CREATE INDEX idx_csv_coord_staff_date ON csv_coordinator_tasks_2025_12(staff_id, task_date);
CREATE INDEX idx_csv_coord_status ON csv_coordinator_tasks_2025_12(billing_status);

-- -----------------------------------------------------------------------------
-- Table: csv_provider_tasks_YYYY_MM
-- Source: PSL_ZEN-*.csv (PCP visits only)
-- Contains: Provider PCP visits (Home, Office, Telehealth) for billing
--
-- Raw CSV columns preserved for audit/reconciliation
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS csv_provider_tasks_2025_12 (
    csv_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Staff identification
    staff_code TEXT NOT NULL,              -- Original staff code from CSV (e.g., "ZEN-SZA")
    staff_id INTEGER,                      -- Mapped staff_id from users table (via staff_code_mapping)
    staff_name TEXT,                       -- Staff full name from users table
    -- Patient identification
    patient_id TEXT NOT NULL,              -- Patient name/ID from "Patient Last, First DOB" column
    patient_dob TEXT,                      -- Patient DOB extracted from patient_id
    -- Task details
    task_date DATE NOT NULL,               -- Date of service from "DOS" column
    duration_minutes REAL NOT NULL,        -- Duration in minutes (from "Minutes" column, parsed from range)
    raw_minutes TEXT,                      -- Raw "Minutes" value (may be range like "40-49")
    task_type TEXT,                        -- Service description from "Service" column
    billing_code TEXT,                     -- CPT/billing code from "Coding" column
    -- Billing status from CSV
    billed_date_notes TEXT,                -- "Billed Date Notes" column value
    hospice TEXT DEFAULT 'No',             -- Hospice flag from "Hospice" column
    paid_by_patient TEXT,                  -- "Paid by Patient" column value
    -- Notes
    notes TEXT,                            -- General notes from "Notes" column
    -- Wound care fields (optional, from PSL files)
    wc_size TEXT,                          -- "WC Size (sqcm)" - wound care size
    wc_diagnosis TEXT,                     -- "WC Diagnosis" - wound care diagnosis
    graft_info TEXT,                       -- "Graft Info" - graft information
    wound_number TEXT,                     -- "Wound#" - wound number
    session_number TEXT,                   -- "Session#" - session number
    multiple_grafts TEXT,                  -- "Multiple Grafts" flag
    -- Source tracking
    source_file TEXT NOT NULL,             -- Original CSV filename (e.g., "PSL_ZEN-SZA.csv")
    source_system TEXT DEFAULT 'CSV_IMPORT',
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Billing workflow fields
    billing_status TEXT DEFAULT 'Pending',  -- Pending, Billed, Invoiced, Paid, etc.
    is_billed INTEGER DEFAULT 0,
    billed_date DATE,                      -- System billed date (separate from CSV billed_date_notes)
    billed_by INTEGER,
    invoice_id TEXT,
    is_paid INTEGER DEFAULT 0,
    paid_date DATE,                        -- System paid date (separate from CSV paid_by_patient)
    billing_notes TEXT
);
CREATE INDEX idx_csv_prov_staff_date ON csv_provider_tasks_2025_12(staff_id, task_date);
CREATE INDEX idx_csv_prov_status ON csv_provider_tasks_2025_12(billing_status);
CREATE INDEX idx_csv_prov_billing_code ON csv_provider_tasks_2025_12(billing_code);

-- -----------------------------------------------------------------------------
-- Table: csv_provider_rvzs_YYYY_MM
-- Source: RVZ_ZEN-*.csv (raw data preserved for audit/reconciliation)
-- Contains: Raw RVZ file data - provider phone reviews + care coordination
-- This table preserves ALL raw RVZ data for reconciliation purposes
-- Note: RVZ data is also imported into csv_coordinator_tasks for billing
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS csv_provider_rvzs_2025_12 (
    csv_rvz_id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Staff identification
    staff_code TEXT NOT NULL,              -- Original provider code from CSV (e.g., "ZEN-SZA")
    staff_id INTEGER,                      -- Mapped staff_id from users table
    staff_name TEXT,                       -- Staff full name from users table
    -- Patient identification
    patient_id TEXT NOT NULL,              -- Patient name/ID from "Pt Name" column
    patient_dob TEXT,                      -- Patient DOB from "Last, First DOB" column
    -- Task details
    task_date DATE NOT NULL,               -- Date of service from "Date Only" column
    duration_minutes REAL,                 -- Final duration (uses ZEN column primarily)
    mins_b_value REAL DEFAULT 0,           -- Raw "Mins B" column value (usually empty in RVZ)
    zen_value REAL DEFAULT 0,              -- Raw "ZEN" column value (primary source)
    total_mins_value REAL DEFAULT 0,       -- Raw "Total Mins" column value
    task_type TEXT,                        -- Type from "Type" column
    notes TEXT,                            -- Notes from "Notes" column
    current_status TEXT,                   -- Status from "Current" column
    notzen_flag TEXT,                      -- "NotZEN" column value
    -- Time tracking (all columns from RVZ)
    start_time_a TEXT,                     -- "Start Time A" column
    stop_time_a TEXT,                      -- "Stop Time A" column
    start_time_b TEXT,                     -- "Start Time B" column
    stop_time_b TEXT,                      -- "Stop Time B" column
    -- Source tracking
    source_file TEXT NOT NULL,             -- Original CSV filename (e.g., "RVZ_ZEN-SZA.csv")
    source_system TEXT DEFAULT 'CSV_IMPORT',
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_csv_rvz_staff_date ON csv_provider_rvzs_2025_12(staff_id, task_date);

-- -----------------------------------------------------------------------------
-- View: csv_billing_summary_YYYY_MM
-- Aggregates all CSV billing data for monthly billing reports
-- Combines coordinator tasks (CMLog + RVZ) and provider tasks (PSL)
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS csv_billing_summary_2025_12 AS
WITH coordinator_summary AS (
    -- Coordinator work from CMLog files + provider phone reviews from RVZ files
    SELECT
        staff_id,
        staff_name,
        task_date,
        source_type,
        SUM(duration_minutes) as coordinator_minutes,
        COUNT(*) as coordinator_tasks,
        GROUP_CONCAT(DISTINCT source_file) as sources
    FROM csv_coordinator_tasks_2025_12
    WHERE duration_minutes > 0
    GROUP BY staff_id, staff_name, task_date, source_type
),
provider_summary AS (
    -- Provider PCP visits from PSL files
    SELECT
        staff_id,
        staff_name,
        task_date,
        billing_code,
        task_type,
        SUM(duration_minutes) as provider_minutes,
        SUM(duration_minutes) / 60.0 as provider_hours,
        COUNT(*) as provider_tasks
    FROM csv_provider_tasks_2025_12
    WHERE duration_minutes > 0
    GROUP BY staff_id, staff_name, task_date, billing_code, task_type
)
SELECT
    COALESCE(c.staff_id, p.staff_id) as staff_id,
    COALESCE(c.staff_name, p.staff_name) as staff_name,
    COALESCE(c.task_date, p.task_date) as task_date,
    -- Coordinator minutes (split by source_type)
    SUM(CASE WHEN c.source_type = 'CMLOG' THEN c.coordinator_minutes ELSE 0 END) as cmlog_minutes,
    SUM(CASE WHEN c.source_type = 'RVZ' THEN c.coordinator_minutes ELSE 0 END) as rvz_phone_review_minutes,
    COALESCE(c.coordinator_minutes, 0) as total_coordinator_minutes,
    COALESCE(p.provider_minutes, 0) as provider_minutes,
    COALESCE(c.coordinator_minutes, 0) + COALESCE(p.provider_minutes, 0) as total_minutes,
    ROUND((COALESCE(c.coordinator_minutes, 0) + COALESCE(p.provider_minutes, 0)) / 60.0, 2) as total_hours,
    -- Provider details
    p.billing_code,
    p.task_type as provider_task_type,
    -- Counts
    COALESCE(SUM(c.coordinator_tasks), 0) as coordinator_task_count,
    COALESCE(p.provider_tasks, 0) as provider_task_count,
    COALESCE(SUM(c.coordinator_tasks), 0) + COALESCE(p.provider_tasks, 0) as total_task_count,
    -- Sources for audit
    GROUP_CONCAT(DISTINCT c.sources) as coordinator_sources
FROM coordinator_summary c
FULL OUTER JOIN provider_summary p ON c.staff_id = p.staff_id AND c.task_date = p.task_date
GROUP BY COALESCE(c.staff_id, p.staff_id), COALESCE(c.staff_name, p.staff_name), COALESCE(c.task_date, p.task_date)
;

-- -----------------------------------------------------------------------------
-- View: csv_billing_monthly_summary_YYYY_MM
-- Monthly aggregated totals by staff for billing reports
-- Provides high-level summary for monthly billing reconciliation
-- -----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS csv_billing_monthly_summary_2025_12 AS
SELECT
    staff_id,
    staff_name,
    -- Coordinator minutes by source
    SUM(cmlog_minutes) as total_cmlog_minutes,
    SUM(rvz_phone_review_minutes) as total_rvz_phone_review_minutes,
    SUM(total_coordinator_minutes) as total_coordinator_minutes,
    -- Provider minutes
    SUM(provider_minutes) as total_provider_minutes,
    -- Totals
    SUM(total_minutes) as total_all_minutes,
    SUM(total_hours) as total_all_hours,
    COUNT(DISTINCT task_date) as working_days,
    SUM(total_task_count) as total_tasks
FROM csv_billing_summary_2025_12
GROUP BY staff_id, staff_name;
