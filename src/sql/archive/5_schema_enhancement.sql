-- ZEN Medical System - Database Schema Enhancement Script
-- Implementation of P0 Enhancement Requirements
-- Date: September 22, 2025

-- Disable foreign key constraints during schema changes
PRAGMA foreign_keys = OFF;

-- ========================================
-- ONBOARDING DATA ENHANCEMENTS (Stage 1)
-- ========================================

-- Stage 1: Contact Information Fields
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_name TEXT;
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_phone TEXT;
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_email TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_name TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_phone TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_email TEXT;

-- ========================================
-- ONBOARDING DATA ENHANCEMENTS (Stage 2)
-- ========================================

-- Stage 2: Medical Provider Information
ALTER TABLE onboarding_patients ADD COLUMN primary_care_provider TEXT;
ALTER TABLE onboarding_patients ADD COLUMN pcp_last_seen DATE;
ALTER TABLE onboarding_patients ADD COLUMN active_specialist TEXT;
ALTER TABLE onboarding_patients ADD COLUMN specialist_last_seen DATE;
ALTER TABLE onboarding_patients ADD COLUMN chronic_conditions_onboarding TEXT;

-- Mental Health Checkboxes (Stage 2)
ALTER TABLE onboarding_patients ADD COLUMN mh_schizophrenia BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_depression BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_anxiety BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_stress BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_adhd BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_bipolar BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_suicidal BOOLEAN DEFAULT FALSE;

-- ========================================
-- PROVIDER CLINICAL DATA ENHANCEMENTS
-- ========================================

-- Patient Panel Updates (for Provider Dashboard)
ALTER TABLE patients ADD COLUMN last_visit_date DATE;
ALTER TABLE patients ADD COLUMN facility TEXT;
ALTER TABLE patients ADD COLUMN assigned_coordinator_id INTEGER;

-- Clinical Data Collection
ALTER TABLE patients ADD COLUMN er_count_1yr INTEGER;
ALTER TABLE patients ADD COLUMN hospitalization_count_1yr INTEGER;
ALTER TABLE patients ADD COLUMN clinical_biometric TEXT;
ALTER TABLE patients ADD COLUMN chronic_conditions_provider TEXT;
ALTER TABLE patients ADD COLUMN cancer_history TEXT;
ALTER TABLE patients ADD COLUMN subjective_risk_level INTEGER; -- 1-6 scale

-- Provider Mental Health Assessment Checkboxes
ALTER TABLE patients ADD COLUMN provider_mh_schizophrenia BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_depression BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_anxiety BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_stress BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_adhd BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_bipolar BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_suicidal BOOLEAN DEFAULT FALSE;

-- Additional Clinical Fields
ALTER TABLE patients ADD COLUMN active_specialists TEXT;
ALTER TABLE patients ADD COLUMN code_status TEXT;
ALTER TABLE patients ADD COLUMN cognitive_function TEXT;
ALTER TABLE patients ADD COLUMN functional_status TEXT;
ALTER TABLE patients ADD COLUMN goals_of_care TEXT;
ALTER TABLE patients ADD COLUMN active_concerns TEXT;

-- ========================================
-- COORDINATOR ENHANCEMENTS
-- ========================================

-- Provider Assignment Tracking (if not already exists)
ALTER TABLE onboarding_patients ADD COLUMN assigned_provider_user_id INTEGER;

-- TV Visit Scheduling Fields
ALTER TABLE onboarding_patients ADD COLUMN tv_date DATE;
ALTER TABLE onboarding_patients ADD COLUMN tv_time TIME;
ALTER TABLE onboarding_patients ADD COLUMN tv_scheduled BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN patient_notified BOOLEAN DEFAULT FALSE;

-- ========================================
-- CREATE INDEXES FOR PERFORMANCE
-- ========================================

-- Patient-related indexes
CREATE INDEX IF NOT EXISTS idx_patients_last_visit_date ON patients(last_visit_date);
CREATE INDEX IF NOT EXISTS idx_patients_risk_level ON patients(subjective_risk_level);
CREATE INDEX IF NOT EXISTS idx_patients_coordinator ON patients(assigned_coordinator_id);

-- Onboarding workflow indexes
CREATE INDEX IF NOT EXISTS idx_onboarding_stage1 ON onboarding_patients(stage1_complete);
CREATE INDEX IF NOT EXISTS idx_onboarding_stage2 ON onboarding_patients(stage2_complete);
CREATE INDEX IF NOT EXISTS idx_onboarding_provider_assignment ON onboarding_patients(assigned_provider_user_id);

-- Coordinator task performance indexes
CREATE INDEX IF NOT EXISTS idx_coordinator_tasks_date ON coordinator_tasks(task_date);
CREATE INDEX IF NOT EXISTS idx_coordinator_tasks_coordinator ON coordinator_tasks(coordinator_id);
CREATE INDEX IF NOT EXISTS idx_coordinator_tasks_patient ON coordinator_tasks(patient_id);

-- ========================================
-- RE-ENABLE CONSTRAINTS
-- ========================================

PRAGMA foreign_keys = ON;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Verify onboarding_patients table structure
-- SELECT sql FROM sqlite_master WHERE type='table' AND name='onboarding_patients';

-- Verify patients table structure  
-- SELECT sql FROM sqlite_master WHERE type='table' AND name='patients';

-- Check indexes created
-- SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';