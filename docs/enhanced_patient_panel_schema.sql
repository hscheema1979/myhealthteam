-- Enhanced patient_panel table schema
-- Supports My Patients views (Provider & Coordinator dashboards) and HHC admin dashboard
-- Created to provide a comprehensive superset of all required columns

CREATE TABLE IF NOT EXISTS patient_panel (
    -- Core patient identification (existing)
    patient_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    date_of_birth TEXT,
    phone_primary TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    insurance_primary TEXT,
    insurance_policy_number TEXT,
    current_facility_id INTEGER,
    facility TEXT,
    assigned_coordinator_id INTEGER,
    status TEXT,
    created_date TEXT,

    -- Provider/Coordinator assignment (existing)
    provider_id INTEGER,
    coordinator_id INTEGER,
    provider_name TEXT,
    coordinator_name TEXT,
    last_visit_date TEXT,

    -- Clinical and care management fields (enhanced for all dashboards)
    initial_tv_completed_date TEXT,
    initial_tv_notes TEXT,
    initial_tv_provider TEXT,
    goals_of_care TEXT,
    goc_value TEXT,
    code_status TEXT,
    subjective_risk_level TEXT,
    service_type TEXT,

    -- Contact information for care coordination
    appointment_contact_name TEXT,
    appointment_contact_phone TEXT,
    appointment_contact_email TEXT,
    medical_contact_name TEXT,
    medical_contact_phone TEXT,
    medical_contact_email TEXT,

    -- Additional clinical fields
    hypertension INTEGER DEFAULT 0,
    mental_health_concerns INTEGER DEFAULT 0,
    dementia INTEGER DEFAULT 0,
    clinical_biometric TEXT,
    chronic_conditions_provider TEXT,
    cancer_history TEXT,
    active_specialists TEXT,
    cognitive_function TEXT,
    functional_status TEXT,
    active_concerns TEXT,

    -- Workflow and process tracking
    enrollment_date TEXT,
    discharge_date TEXT,
    notes TEXT,
    chart_notes TEXT,
    intake_call_completed INTEGER DEFAULT 0,
    intake_notes TEXT,
    eligibility_status TEXT,
    eligibility_notes TEXT,
    eligibility_verified INTEGER DEFAULT 0,
    emed_chart_created INTEGER DEFAULT 0,
    chart_id TEXT,
    facility_confirmed INTEGER DEFAULT 0,
    medical_records_requested INTEGER DEFAULT 0,
    referral_documents_received INTEGER DEFAULT 0,
    insurance_cards_received INTEGER DEFAULT 0,
    emed_signature_received INTEGER DEFAULT 0,

    -- TV (Telehealth Visit) tracking
    tv_date TEXT,
    tv_scheduled INTEGER DEFAULT 0,
    patient_notified INTEGER DEFAULT 0,
    tv_time TEXT,

    -- Provider-specific visit tracking
    last_visit_service_type TEXT,
    last_visit_minutes INTEGER DEFAULT 0,
    er_count_1yr INTEGER,
    hospitalization_count_1yr INTEGER,

    -- Standardized patient ID format for external systems
    last_first_dob TEXT,

    -- Care team information
    primary_care_provider TEXT,
    pcp_last_seen TEXT,
    active_specialist TEXT,
    specialist_last_seen TEXT,
    chronic_conditions_onboarding TEXT,

    -- Mental health flags (both provider and onboarding versions)
    mh_schizophrenia INTEGER DEFAULT 0,
    mh_depression INTEGER DEFAULT 0,
    mh_anxiety INTEGER DEFAULT 0,
    mh_stress INTEGER DEFAULT 0,
    mh_adhd INTEGER DEFAULT 0,
    mh_bipolar INTEGER DEFAULT 0,
    mh_suicidal INTEGER DEFAULT 0,
    provider_mh_schizophrenia INTEGER DEFAULT 0,
    provider_mh_depression INTEGER DEFAULT 0,
    provider_mh_anxiety INTEGER DEFAULT 0,
    provider_mh_stress INTEGER DEFAULT 0,
    provider_mh_adhd INTEGER DEFAULT 0,
    provider_mh_bipolar INTEGER DEFAULT 0,
    provider_mh_suicidal INTEGER DEFAULT 0,

    -- Care team member names for easy display
    care_provider_name TEXT,
    care_coordinator_name TEXT,

    -- Additional contact numbers for display
    phone_medical TEXT,
    phone_appointment TEXT,
    phone_medical_number TEXT,
    phone_appointment_number TEXT,

    -- HHC-specific fields
    mins INTEGER DEFAULT 0,

    -- Metadata
    updated_date TEXT DEFAULT (datetime('now'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patient_panel_patient_id ON patient_panel(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_panel_provider_id ON patient_panel(provider_id);
CREATE INDEX IF NOT EXISTS idx_patient_panel_coordinator_id ON patient_panel(coordinator_id);
CREATE INDEX IF NOT EXISTS idx_patient_panel_status ON patient_panel(status);
CREATE INDEX IF NOT EXISTS idx_patient_panel_facility ON patient_panel(facility);
CREATE INDEX IF NOT EXISTS idx_patient_panel_last_visit ON patient_panel(last_visit_date);

-- Note: This enhanced schema supports:
--
-- My Patients - Provider Dashboard:
-- - Core patient info: first_name, last_name, phone_primary, facility
-- - Care info: status, goals_of_care/goc_value, code_status, service_type
-- - Assignment: provider_name, coordinator_name, last_visit_date
--
-- My Patients - Coordinator Dashboard:
-- - All provider fields PLUS:
-- - Risk assessment: subjective_risk_level
-- - Contact info: appointment_contact_name/phone, medical_contact_name/phone
-- - Care team: care_provider_name, care_coordinator_name
-- - Visit tracking: last_visit_service_type, last_visit_minutes, mins
--
-- HHC Admin Dashboard:
-- - All above fields PLUS:
-- - Standardized ID: last_first_dob
-- - Geographic: address_city
-- - Insurance: insurance_primary
-- - TV tracking: initial_tv_completed_date, tv_date, initial_tv_provider
-- - Clinical: code_status, subjective_risk_level, medical_contact_phone, appointment_contact_phone
--
-- This superset approach ensures the patient_panel table can serve as a single
-- source of truth for all patient-related views across the application.
