-- ============================================================================
-- POST-IMPORT PROCESSING FOR production.db
-- ============================================================================
-- Purpose: Complete all data aggregations and table population after raw import
-- Run AFTER: transform_production_data_v3.py completes
-- Runtime: ~30 seconds
-- ============================================================================
-- ============================================================================
-- STEP 1: Create Summary Tables
-- ============================================================================
-- Provider Weekly Summary with Billing
CREATE TABLE IF NOT EXISTS provider_weekly_summary_with_billing (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER,
    provider_name TEXT,
    week_start_date DATE,
    week_end_date DATE,
    year INTEGER,
    week_number INTEGER,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    status TEXT DEFAULT 'Active',
    paid BOOLEAN DEFAULT FALSE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Coordinator Monthly Summary
CREATE TABLE IF NOT EXISTS coordinator_monthly_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id TEXT,
    coordinator_name TEXT,
    year INTEGER,
    month INTEGER,
    month_start_date DATE,
    month_end_date DATE,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Patient Monthly Billing Tables (monthly partitions for 2025)
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_01 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_02 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_03 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_04 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_05 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_06 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_07 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_08 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_09 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_10 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_11 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_monthly_billing_2025_12 (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT,
    billing_code_description TEXT,
    patient_id TEXT,
    total_minutes INTEGER DEFAULT 0,
    billing_status TEXT DEFAULT 'Pending',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ============================================================================
-- STEP 2: Create Empty Tables for Billing Workflow & Audit
-- ============================================================================
-- Provider Task Billing Status (user-editable workflow flags)
CREATE TABLE IF NOT EXISTS provider_task_billing_status (
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
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Audit Log (empty for now, future use)
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT,
    table_name TEXT,
    record_id TEXT,
    old_value TEXT,
    new_value TEXT,
    user_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
-- ============================================================================
-- STEP 2: Create Dashboard Compatibility Views
-- ============================================================================
-- These views UNION all monthly partitioned tables so dashboards can query
-- "provider_tasks" instead of "provider_tasks_YYYY_MM"
-- ============================================================================
DROP VIEW IF EXISTS provider_tasks;
DROP VIEW IF EXISTS coordinator_tasks;
-- Provider Tasks View (all months)
CREATE VIEW provider_tasks AS
SELECT *
FROM provider_tasks_2001_01
UNION ALL
SELECT *
FROM provider_tasks_2023_05
UNION ALL
SELECT *
FROM provider_tasks_2023_06
UNION ALL
SELECT *
FROM provider_tasks_2023_07
UNION ALL
SELECT *
FROM provider_tasks_2023_10
UNION ALL
SELECT *
FROM provider_tasks_2023_11
UNION ALL
SELECT *
FROM provider_tasks_2023_12
UNION ALL
SELECT *
FROM provider_tasks_2024_01
UNION ALL
SELECT *
FROM provider_tasks_2024_02
UNION ALL
SELECT *
FROM provider_tasks_2024_03
UNION ALL
SELECT *
FROM provider_tasks_2024_04
UNION ALL
SELECT *
FROM provider_tasks_2024_05
UNION ALL
SELECT *
FROM provider_tasks_2024_06
UNION ALL
SELECT *
FROM provider_tasks_2024_07
UNION ALL
SELECT *
FROM provider_tasks_2024_08
UNION ALL
SELECT *
FROM provider_tasks_2024_09
UNION ALL
SELECT *
FROM provider_tasks_2024_10
UNION ALL
SELECT *
FROM provider_tasks_2024_11
UNION ALL
SELECT *
FROM provider_tasks_2024_12
UNION ALL
SELECT *
FROM provider_tasks_2025_01
UNION ALL
SELECT *
FROM provider_tasks_2025_02
UNION ALL
SELECT *
FROM provider_tasks_2025_03
UNION ALL
SELECT *
FROM provider_tasks_2025_04
UNION ALL
SELECT *
FROM provider_tasks_2025_05
UNION ALL
SELECT *
FROM provider_tasks_2025_06
UNION ALL
SELECT *
FROM provider_tasks_2025_07
UNION ALL
SELECT *
FROM provider_tasks_2025_08
UNION ALL
SELECT *
FROM provider_tasks_2025_09
UNION ALL
SELECT *
FROM provider_tasks_2025_10
UNION ALL
SELECT *
FROM provider_tasks_2025_11;
-- Coordinator Tasks View (all months)
CREATE VIEW coordinator_tasks AS
SELECT *
FROM coordinator_tasks_2025_01
UNION ALL
SELECT *
FROM coordinator_tasks_2025_02
UNION ALL
SELECT *
FROM coordinator_tasks_2025_03
UNION ALL
SELECT *
FROM coordinator_tasks_2025_04
UNION ALL
SELECT *
FROM coordinator_tasks_2025_05
UNION ALL
SELECT *
FROM coordinator_tasks_2025_06
UNION ALL
SELECT *
FROM coordinator_tasks_2025_07
UNION ALL
SELECT *
FROM coordinator_tasks_2025_08
UNION ALL
SELECT *
FROM coordinator_tasks_2025_09
UNION ALL
SELECT *
FROM coordinator_tasks_2025_10
UNION ALL
SELECT *
FROM coordinator_tasks_2025_11;
-- ============================================================================
-- STEP 3: Update Patient Panel Last Visit Data
-- ============================================================================
-- Only if patient_panel table exists (created by ZMO import)
-- ============================================================================
UPDATE patient_panel
SET last_visit_date = (
        SELECT MAX(task_date)
        FROM provider_tasks pt
        WHERE pt.patient_id = patient_panel.patient_id
    )
WHERE EXISTS (
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
            AND name = 'patient_panel'
    );
-- ============================================================================
-- STEP 4: Populate Provider Weekly Summary with Billing
-- ============================================================================
-- Clear existing data
DELETE FROM provider_weekly_summary_with_billing;
-- Populate weekly summaries
INSERT INTO provider_weekly_summary_with_billing (
        provider_id,
        provider_name,
        week_start_date,
        week_end_date,
        year,
        week_number,
        total_tasks_completed,
        total_time_spent_minutes,
        billing_code,
        billing_code_description,
        status,
        created_date
    )
SELECT pt.provider_id,
    u.full_name as provider_name,
    DATE(pt.task_date, 'weekday 0', '-6 days') as week_start_date,
    DATE(pt.task_date, 'weekday 0') as week_end_date,
    CAST(strftime('%Y', pt.task_date) AS INTEGER) as year,
    CAST(strftime('%W', pt.task_date) AS INTEGER) as week_number,
    COUNT(*) as total_tasks_completed,
    SUM(pt.minutes_of_service) as total_time_spent_minutes,
    CASE
        WHEN SUM(pt.minutes_of_service) >= 60 THEN '99349'
        WHEN SUM(pt.minutes_of_service) >= 40 THEN '99348'
        WHEN SUM(pt.minutes_of_service) >= 30 THEN '99347'
        WHEN SUM(pt.minutes_of_service) >= 20 THEN '99346'
        ELSE '99345'
    END as billing_code,
    CASE
        WHEN SUM(pt.minutes_of_service) >= 60 THEN 'Home Visit 60+ min'
        WHEN SUM(pt.minutes_of_service) >= 40 THEN 'Home Visit 40-59 min'
        WHEN SUM(pt.minutes_of_service) >= 30 THEN 'Home Visit 30-39 min'
        WHEN SUM(pt.minutes_of_service) >= 20 THEN 'Home Visit 20-29 min'
        ELSE 'Home Visit <20 min'
    END as billing_code_description,
    'Active' as status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks pt
    LEFT JOIN users u ON pt.provider_id = u.user_id
GROUP BY pt.provider_id,
    year,
    week_number
ORDER BY year DESC,
    week_number DESC,
    pt.provider_id;
-- ============================================================================
-- STEP 5: Populate Coordinator Monthly Summary
-- ============================================================================
-- Clear existing data
DELETE FROM coordinator_monthly_summary;
-- Populate monthly summaries
INSERT INTO coordinator_monthly_summary (
        coordinator_id,
        coordinator_name,
        year,
        month,
        month_start_date,
        month_end_date,
        total_tasks_completed,
        total_time_spent_minutes,
        created_date
    )
SELECT ct.coordinator_id,
    u.full_name as coordinator_name,
    CAST(strftime('%Y', ct.task_date) AS INTEGER) as year,
    CAST(strftime('%m', ct.task_date) AS INTEGER) as month,
    DATE(ct.task_date, 'start of month') as month_start_date,
    DATE(
        ct.task_date,
        'start of month',
        '+1 month',
        '-1 day'
    ) as month_end_date,
    COUNT(*) as total_tasks_completed,
    SUM(ct.duration_minutes) as total_time_spent_minutes,
    CURRENT_TIMESTAMP as created_date
FROM coordinator_tasks ct
    LEFT JOIN users u ON ct.coordinator_id = u.user_id
GROUP BY ct.coordinator_id,
    year,
    month
ORDER BY year DESC,
    month DESC,
    ct.coordinator_id;
-- ============================================================================
-- STEP 6: Populate Patient Monthly Billing (per month)
-- ============================================================================
-- Clear existing monthly billing tables
DELETE FROM patient_monthly_billing_2025_01;
DELETE FROM patient_monthly_billing_2025_02;
DELETE FROM patient_monthly_billing_2025_03;
DELETE FROM patient_monthly_billing_2025_04;
DELETE FROM patient_monthly_billing_2025_05;
DELETE FROM patient_monthly_billing_2025_06;
DELETE FROM patient_monthly_billing_2025_07;
DELETE FROM patient_monthly_billing_2025_08;
DELETE FROM patient_monthly_billing_2025_09;
DELETE FROM patient_monthly_billing_2025_10;
DELETE FROM patient_monthly_billing_2025_11;
-- Populate 2025_01
INSERT INTO patient_monthly_billing_2025_01 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_01 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_02
INSERT INTO patient_monthly_billing_2025_02 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_02 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_03
INSERT INTO patient_monthly_billing_2025_03 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_03 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_04
INSERT INTO patient_monthly_billing_2025_04 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_04 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_05
INSERT INTO patient_monthly_billing_2025_05 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_05 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_06
INSERT INTO patient_monthly_billing_2025_06 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_06 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_07
INSERT INTO patient_monthly_billing_2025_07 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_07 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_08
INSERT INTO patient_monthly_billing_2025_08 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_08 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_09
INSERT INTO patient_monthly_billing_2025_09 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_09 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_10
INSERT INTO patient_monthly_billing_2025_10 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_10 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- Populate 2025_11
INSERT INTO patient_monthly_billing_2025_11 (
        billing_code,
        billing_code_description,
        patient_id,
        total_minutes,
        billing_status,
        created_date
    )
SELECT pt.billing_code,
    tbc.description as billing_code_description,
    pt.patient_id,
    SUM(pt.minutes_of_service) as total_minutes,
    'Pending' as billing_status,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks_2025_11 pt
    LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
GROUP BY pt.billing_code,
    pt.patient_id;
-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
-- ============================================================================
-- STEP 8: Rebuild patient_panel from patients (with correct schema)
-- ============================================================================
-- CRITICAL: Schema must match what get_all_patient_panel() expects in database.py
-- Required columns: patient_id, first_name, last_name, date_of_birth, phone_primary,
--   current_facility_id, facility, status, created_date, provider_id, coordinator_id,
--   provider_name, coordinator_name, last_visit_date, last_visit_service_type,
--   goals_of_care, goc_value, code_status, subjective_risk_level, service_type,
--   er_count_1yr, hospitalization_count_1yr, mental_health_concerns, provider_mh_*,
--   cognitive_function, functional_status, active_specialists, active_concerns,
--   chronic_conditions_provider, appointment_contact_*, medical_contact_*,
--   care_provider_name, care_coordinator_name, updated_date
DROP TABLE IF EXISTS patient_panel;
CREATE TABLE patient_panel AS
SELECT DISTINCT
    p.patient_id,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.phone_primary,
    p.current_facility_id,
    p.facility,
    p.status,
    p.created_date,
    CAST(COALESCE(pa.provider_id, 0) AS INTEGER) as provider_id,
    CAST(COALESCE(pa.coordinator_id, 0) AS TEXT) as coordinator_id,
    CASE WHEN pa.provider_id > 0 THEN u_prov.full_name ELSE NULL END as provider_name,
    CASE WHEN pa.coordinator_id > 0 THEN u_coord.full_name ELSE NULL END as coordinator_name,
    p.last_visit_date,
    p.service_type as last_visit_service_type,
    p.goals_of_care,
    p.goc_value,
    p.code_status,
    p.subjective_risk_level,
    p.service_type,
    COALESCE(p.er_count_1yr, 0) as er_count_1yr,
    COALESCE(p.hospitalization_count_1yr, 0) as hospitalization_count_1yr,
    COALESCE(p.mental_health_concerns, 0) as mental_health_concerns,
    COALESCE(p.provider_mh_schizophrenia, 0) as provider_mh_schizophrenia,
    COALESCE(p.provider_mh_depression, 0) as provider_mh_depression,
    COALESCE(p.provider_mh_anxiety, 0) as provider_mh_anxiety,
    COALESCE(p.provider_mh_stress, 0) as provider_mh_stress,
    COALESCE(p.provider_mh_adhd, 0) as provider_mh_adhd,
    COALESCE(p.provider_mh_bipolar, 0) as provider_mh_bipolar,
    COALESCE(p.provider_mh_suicidal, 0) as provider_mh_suicidal,
    p.cognitive_function,
    p.functional_status,
    p.active_specialists,
    p.active_concerns,
    p.chronic_conditions_provider,
    p.appointment_contact_name,
    p.appointment_contact_phone,
    p.medical_contact_name,
    p.medical_contact_phone,
    CASE WHEN pa.provider_id > 0 THEN u_prov.full_name ELSE NULL END as care_provider_name,
    CASE WHEN pa.coordinator_id > 0 THEN u_coord.full_name ELSE NULL END as care_coordinator_name,
    datetime('now') as updated_date
FROM patients p
LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id AND pa.status = 'active'
LEFT JOIN users u_prov ON pa.provider_id = u_prov.user_id
LEFT JOIN users u_coord ON pa.coordinator_id = u_coord.user_id;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patient_panel_patient_id ON patient_panel(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_panel_provider_id ON patient_panel(provider_id);
CREATE INDEX IF NOT EXISTS idx_patient_panel_coordinator_id ON patient_panel(coordinator_id);
CREATE INDEX IF NOT EXISTS idx_patient_panel_status ON patient_panel(status);
CREATE INDEX IF NOT EXISTS idx_patient_panel_facility ON patient_panel(facility);
CREATE INDEX IF NOT EXISTS idx_patient_panel_last_visit ON patient_panel(last_visit_date);
SELECT 'Post-import processing complete' as status,
    (
        SELECT COUNT(*)
        FROM provider_weekly_summary_with_billing
    ) as provider_weekly_summary_count,
    (
        SELECT COUNT(*)
        FROM coordinator_monthly_summary
    ) as coordinator_monthly_summary_count,
    (
        SELECT COUNT(*)
        FROM patient_monthly_billing_2025_11
    ) as patient_monthly_billing_count,
    (
        SELECT COUNT(*)
        FROM provider_task_billing_status
    ) as provider_task_billing_status_count,
    (
        SELECT COUNT(*)
        FROM patient_panel
    ) as patient_panel_count,
    (
        SELECT COUNT(DISTINCT status)
        FROM patient_panel
    ) as patient_panel_status_types;
-- ============================================================================
-- STEP 7: Populate Provider Task Billing Status (Medicare/Insurance Workflow)
-- ============================================================================
DELETE FROM provider_task_billing_status;
INSERT INTO provider_task_billing_status (
        provider_task_id,
        provider_id,
        provider_name,
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
        is_carried_over,
        created_date
    )
SELECT pt.provider_task_id,
    pt.provider_id,
    pt.provider_name,
    pt.patient_name,
    pt.task_date,
    CAST(strftime('%W', pt.task_date) AS INTEGER) as billing_week,
    DATE(pt.task_date, 'weekday 0', '-6 days') as week_start_date,
    DATE(pt.task_date, 'weekday 0') as week_end_date,
    pt.task_description,
    pt.minutes_of_service,
    pt.billing_code,
    pt.billing_code_description,
    'Pending' as billing_status,
    FALSE as is_billed,
    FALSE as is_invoiced,
    FALSE as is_claim_submitted,
    FALSE as is_insurance_processed,
    FALSE as is_approved_to_pay,
    FALSE as is_paid,
    FALSE as is_carried_over,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks pt
WHERE pt.billing_code IS NOT NULL
    AND pt.billing_code != 'Not_Billable'
ORDER BY pt.task_date DESC,
    pt.provider_id;