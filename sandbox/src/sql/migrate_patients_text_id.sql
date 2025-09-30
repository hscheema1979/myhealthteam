-- MIGRATION: Fix patients table schema to use TEXT patient_id
-- 1. Backup current patients table (optional, for safety)
DROP TABLE IF EXISTS patients_backup;
CREATE TABLE patients_backup AS
SELECT *
FROM patients;
-- 2. Drop the broken patients table
DROP TABLE IF EXISTS patients;
-- 3. Recreate patients table with patient_id as TEXT (not INT, not PRIMARY KEY)
CREATE TABLE patients (
    patient_id TEXT,
    region_id INT,
    first_name TEXT,
    last_name TEXT,
    date_of_birth TEXT,
    gender TEXT,
    phone_primary TEXT,
    phone_secondary TEXT,
    email TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relationship TEXT,
    insurance_primary TEXT,
    insurance_policy_number TEXT,
    insurance_secondary TEXT,
    medical_record_number TEXT,
    enrollment_date TEXT,
    discharge_date TEXT,
    notes TEXT,
    created_date TEXT,
    updated_date TEXT,
    created_by INT,
    updated_by INT,
    current_facility_id INT,
    hypertension INT,
    mental_health_concerns INT,
    dementia INT,
    last_annual_wellness_visit TEXT,
    last_first_dob TEXT,
    status TEXT,
    medical_records_requested BOOLEAN DEFAULT FALSE,
    referral_documents_received BOOLEAN DEFAULT FALSE,
    insurance_cards_received BOOLEAN DEFAULT FALSE,
    emed_signature_received BOOLEAN DEFAULT FALSE,
    last_visit_date DATE,
    facility TEXT,
    assigned_coordinator_id INTEGER,
    er_count_1yr INTEGER,
    hospitalization_count_1yr INTEGER,
    clinical_biometric TEXT,
    chronic_conditions_provider TEXT,
    cancer_history TEXT,
    subjective_risk_level INTEGER,
    provider_mh_schizophrenia BOOLEAN DEFAULT FALSE,
    provider_mh_depression BOOLEAN DEFAULT FALSE,
    provider_mh_anxiety BOOLEAN DEFAULT FALSE,
    provider_mh_stress BOOLEAN DEFAULT FALSE,
    provider_mh_adhd BOOLEAN DEFAULT FALSE,
    provider_mh_bipolar BOOLEAN DEFAULT FALSE,
    provider_mh_suicidal BOOLEAN DEFAULT FALSE,
    active_specialists TEXT,
    code_status TEXT,
    cognitive_function TEXT,
    functional_status TEXT,
    goals_of_care TEXT,
    active_concerns TEXT,
    initial_tv_completed_date TEXT,
    initial_tv_notes TEXT,
    initial_tv_provider TEXT,
    service_type TEXT
);
-- 4. (Optional) Restore data from backup if needed, but best to re-import with 4a-transform.ps1
-- INSERT INTO patients (...) SELECT ... FROM patients_backup;
-- 5. Clean up backup if not needed
-- DROP TABLE IF EXISTS patients_backup;