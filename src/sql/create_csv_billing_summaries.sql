-- =============================================================================
-- Create CSV Billing Summary Tables (Monthly Partitioned)
-- Similar structure to operational tables
-- =============================================================================

BEGIN;

-- =============================================================================
-- CSV Provider Weekly Billing Summary (Partitioned by Month)
-- One table per month: csv_weekly_billing_summary_YYYY_MM
-- =============================================================================

-- Example for 2025-12 (create others as needed)
DROP TABLE IF EXISTS csv_weekly_billing_summary_2025_12;

CREATE TABLE csv_weekly_billing_summary_2025_12 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    billing_code TEXT,
    billing_code_description TEXT,
    task_type TEXT,
    total_tasks INTEGER DEFAULT 0,
    total_minutes INTEGER DEFAULT 0,
    total_hours REAL DEFAULT 0.0,
    unique_patients INTEGER DEFAULT 0,
    source_file TEXT,
    source_system TEXT DEFAULT 'CSV_IMPORT',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, week_start_date, billing_code)
);

CREATE INDEX idx_csv_weekly_2025_12_provider ON csv_weekly_billing_summary_2025_12(provider_id);
CREATE INDEX idx_csv_weekly_2025_12_date ON csv_weekly_billing_summary_2025_12(week_start_date);

-- =============================================================================
-- CSV Monthly Billing Summary (Partitioned by Month)
-- For BOTH Coordinator and Provider (RZV) tasks
-- One table per month: csv_monthly_billing_summary_YYYY_MM
-- =============================================================================

DROP TABLE IF EXISTS csv_monthly_billing_summary_2025_12;

CREATE TABLE csv_monthly_billing_summary_2025_12 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL,
    staff_name TEXT NOT NULL,
    staff_type TEXT NOT NULL,  -- 'coordinator' or 'provider'
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    billing_code TEXT,
    billing_code_description TEXT,
    task_type TEXT,
    total_tasks INTEGER DEFAULT 0,
    total_minutes INTEGER DEFAULT 0,
    total_hours REAL DEFAULT 0.0,
    unique_patients INTEGER DEFAULT 0,
    source_file TEXT,
    source_system TEXT DEFAULT 'CSV_IMPORT',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(staff_id, staff_type, year, month, billing_code, task_type)
);

CREATE INDEX idx_csv_monthly_2025_12_staff ON csv_monthly_billing_summary_2025_12(staff_id, staff_type);
CREATE INDEX idx_csv_monthly_2025_12_date ON csv_monthly_billing_summary_2025_12(year, month);

COMMIT;

-- =============================================================================
-- To create tables for other months, use the same schema:
-- - csv_weekly_billing_summary_2025_01 through csv_weekly_billing_summary_2025_11
-- - csv_weekly_billing_summary_2026_01
-- - csv_monthly_billing_summary_2025_01 through csv_monthly_billing_summary_2025_11
-- - csv_monthly_billing_summary_2026_01
-- =============================================================================
