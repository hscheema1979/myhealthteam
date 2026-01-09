-- ============================================================================
-- Migration: Contact Fields + created_at_pst
-- ============================================================================
-- Purpose: Add contact columns for Stage 4 onboarding and created_at_pst for coordinator tasks
-- Date: 2025-01-08
-- ============================================================================

-- ============================================================================
-- PART 1: Appointment Contact & Facility Nurse columns
-- ============================================================================
-- These columns are required by the Stage 4 intake processing form
-- They will persist through data imports since:
-- - onboarding_patients: uses INSERT OR REPLACE (unlisted columns preserved)
-- - patients: columns added here will be preserved via restore logic in transform script
-- - patient_panel: rebuilt from patients in post_import_processing.sql
-- ============================================================================

-- Add columns to onboarding_patients table (Stage 4 data)
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_name TEXT;
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_phone TEXT;
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_email TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_name TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_phone TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_email TEXT;
ALTER TABLE onboarding_patients ADD COLUMN facility_nurse_name TEXT;
ALTER TABLE onboarding_patients ADD COLUMN facility_nurse_phone TEXT;
ALTER TABLE onboarding_patients ADD COLUMN facility_nurse_email TEXT;
ALTER TABLE onboarding_patients ADD COLUMN active_specialist TEXT;
ALTER TABLE onboarding_patients ADD COLUMN specialist_last_seen TEXT;
ALTER TABLE onboarding_patients ADD COLUMN chronic_conditions_onboarding TEXT;
ALTER TABLE onboarding_patients ADD COLUMN primary_care_provider TEXT;
ALTER TABLE onboarding_patients ADD COLUMN pcp_last_seen TEXT;

-- Add columns to patients table (for completed onboarding transfers)
ALTER TABLE patients ADD COLUMN facility_nurse_name TEXT;
ALTER TABLE patients ADD COLUMN facility_nurse_phone TEXT;
ALTER TABLE patients ADD COLUMN facility_nurse_email TEXT;
-- Note: appointment_contact_* and medical_contact_* columns already exist in patients table

-- Add columns to patient_panel table (for dashboard display)
ALTER TABLE patient_panel ADD COLUMN facility_nurse_name TEXT;
ALTER TABLE patient_panel ADD COLUMN facility_nurse_phone TEXT;
ALTER TABLE patient_panel ADD COLUMN facility_nurse_email TEXT;
-- Note: appointment_contact_* and medical_contact_* columns already exist in patient_panel table

-- ============================================================================
-- PART 2: created_at_pst column for coordinator_tasks tables
-- ============================================================================
-- This column is needed for task review functionality
-- Since SQLite doesn't support IF NOT EXISTS for ALTER TABLE, we use a try/catch approach
-- Each ALTER TABLE will fail silently if column already exists
-- ============================================================================

-- Helper script notes: If any ALTER TABLE fails due to duplicate column,
-- continue with remaining statements. The application handles missing columns.

-- 2024 tables
ALTER TABLE coordinator_tasks_2024_01 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_02 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_03 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_04 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_05 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_06 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_07 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_08 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_09 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_10 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_11 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_12 ADD COLUMN created_at_pst TEXT;

-- 2025 tables
ALTER TABLE coordinator_tasks_2025_01 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_02 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_03 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_04 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_05 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_06 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_07 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_08 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_09 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_10 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_11 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_12 ADD COLUMN created_at_pst TEXT;

-- 2026 tables
ALTER TABLE coordinator_tasks_2026_01 ADD COLUMN created_at_pst TEXT;
