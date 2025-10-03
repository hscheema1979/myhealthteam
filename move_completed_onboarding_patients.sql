-- Migration Script: Move Completed Onboarding Patients to Separate Table
-- Purpose: Create onboarding_patients_completed table and move completed patients
-- Date: 2025-01-03
-- Author: System Migration
-- Database: production.db

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Begin transaction for atomic operation
BEGIN TRANSACTION;

-- Step 1: Create onboarding_patients_completed table with same structure as onboarding_patients
CREATE TABLE IF NOT EXISTS onboarding_patients_completed (
    onboarding_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    workflow_instance_id INTEGER,
    
    -- Patient Registration Data (Stage 1)
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_primary TEXT,
    email TEXT,
    gender TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    
    -- Address Information
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    
    -- Insurance Information
    insurance_provider TEXT,
    policy_number TEXT,
    group_number TEXT,
    
    -- Referral Information
    referral_source TEXT,
    referring_provider TEXT,
    referral_date DATE,
    
    -- System Fields
    patient_status TEXT DEFAULT 'Active',
    facility_assignment TEXT,
    assigned_pot_user_id INTEGER,
    
    -- Stage Completion Tracking
    stage1_complete BOOLEAN DEFAULT FALSE,
    stage2_complete BOOLEAN DEFAULT FALSE,
    stage3_complete BOOLEAN DEFAULT FALSE,
    stage4_complete BOOLEAN DEFAULT FALSE,
    stage5_complete BOOLEAN DEFAULT TRUE,  -- Always true for completed
    
    -- Additional onboarding fields
    eligibility_status TEXT,
    eligibility_notes TEXT,
    eligibility_verified BOOLEAN DEFAULT FALSE,
    emed_chart_created BOOLEAN DEFAULT FALSE,
    chart_id TEXT,
    facility_confirmed BOOLEAN DEFAULT FALSE,
    chart_notes TEXT,
    intake_call_completed BOOLEAN DEFAULT FALSE,
    intake_notes TEXT,
    
    -- Document tracking
    medical_records_requested BOOLEAN DEFAULT FALSE,
    referral_documents_received BOOLEAN DEFAULT FALSE,
    insurance_cards_received BOOLEAN DEFAULT FALSE,
    emed_signature_received BOOLEAN DEFAULT FALSE,
    
    -- Contact information
    appointment_contact_name TEXT,
    appointment_contact_phone TEXT,
    appointment_contact_email TEXT,
    medical_contact_name TEXT,
    medical_contact_phone TEXT,
    medical_contact_email TEXT,
    
    -- Medical history
    primary_care_provider TEXT,
    pcp_last_seen DATE,
    active_specialist TEXT,
    specialist_last_seen DATE,
    chronic_conditions_onboarding TEXT,
    
    -- Mental health flags
    mh_schizophrenia BOOLEAN DEFAULT FALSE,
    mh_depression BOOLEAN DEFAULT FALSE,
    mh_anxiety BOOLEAN DEFAULT FALSE,
    mh_stress BOOLEAN DEFAULT FALSE,
    mh_adhd BOOLEAN DEFAULT FALSE,
    mh_bipolar BOOLEAN DEFAULT FALSE,
    mh_suicidal BOOLEAN DEFAULT FALSE,
    
    -- Provider assignment and TV scheduling
    assigned_provider_user_id INTEGER,
    tv_date DATE,
    tv_time TIME,
    tv_scheduled BOOLEAN DEFAULT FALSE,
    patient_notified BOOLEAN DEFAULT FALSE,
    
    -- Health conditions
    hypertension BOOLEAN DEFAULT FALSE,
    mental_health_concerns BOOLEAN DEFAULT FALSE,
    dementia BOOLEAN DEFAULT FALSE,
    annual_well_visit BOOLEAN DEFAULT FALSE,
    initial_tv_completed BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,
    moved_to_completed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Copy completed patients to the completed table
INSERT INTO onboarding_patients_completed 
SELECT 
    onboarding_id,
    patient_id,
    workflow_instance_id,
    first_name,
    last_name,
    date_of_birth,
    phone_primary,
    email,
    gender,
    emergency_contact_name,
    emergency_contact_phone,
    address_street,
    address_city,
    address_state,
    address_zip,
    insurance_provider,
    policy_number,
    group_number,
    referral_source,
    referring_provider,
    referral_date,
    patient_status,
    facility_assignment,
    assigned_pot_user_id,
    stage1_complete,
    stage2_complete,
    stage3_complete,
    stage4_complete,
    stage5_complete,
    eligibility_status,
    eligibility_notes,
    eligibility_verified,
    emed_chart_created,
    chart_id,
    facility_confirmed,
    chart_notes,
    intake_call_completed,
    intake_notes,
    medical_records_requested,
    referral_documents_received,
    insurance_cards_received,
    emed_signature_received,
    appointment_contact_name,
    appointment_contact_phone,
    appointment_contact_email,
    medical_contact_name,
    medical_contact_phone,
    medical_contact_email,
    primary_care_provider,
    pcp_last_seen,
    active_specialist,
    specialist_last_seen,
    chronic_conditions_onboarding,
    mh_schizophrenia,
    mh_depression,
    mh_anxiety,
    mh_stress,
    mh_adhd,
    mh_bipolar,
    mh_suicidal,
    assigned_provider_user_id,
    tv_date,
    tv_time,
    tv_scheduled,
    patient_notified,
    hypertension,
    mental_health_concerns,
    dementia,
    annual_well_visit,
    initial_tv_completed,
    created_date,
    updated_date,
    completed_date,
    CURRENT_TIMESTAMP as moved_to_completed_date
FROM onboarding_patients 
WHERE stage5_complete = 1;

-- 3. Show what we're about to move
SELECT 
    onboarding_id,
    first_name || ' ' || last_name as patient_name,
    stage5_complete,
    completed_date,
    created_date
FROM onboarding_patients 
WHERE stage5_complete = 1;

-- 4. Delete completed patients from main table
DELETE FROM onboarding_patients 
WHERE stage5_complete = 1;

-- 5. Create indexes for the completed table
CREATE INDEX IF NOT EXISTS idx_onboarding_completed_patient_id ON onboarding_patients_completed(patient_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_completed_name ON onboarding_patients_completed(first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_onboarding_completed_date ON onboarding_patients_completed(completed_date);

-- 6. Verify the move
SELECT 'Remaining in main table:' as status, COUNT(*) as count FROM onboarding_patients
UNION ALL
SELECT 'Moved to completed table:' as status, COUNT(*) as count FROM onboarding_patients_completed;