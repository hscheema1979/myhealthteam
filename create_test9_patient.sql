-- Create TEST 9 patient in all required tables (corrected version)
-- Based on onboarding_patients data for onboarding_id = 13

-- 1. Insert into patients table (with correct column names)
INSERT INTO patients (
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    phone_primary,
    email,
    address_street,
    address_city,
    address_state,
    address_zip,
    insurance_primary,
    insurance_policy_number,
    enrollment_date,
    status,
    facility,
    chronic_conditions_onboarding,
    tv_date,
    tv_time,
    tv_scheduled,
    patient_notified,
    assigned_coordinator_id,
    created_date,
    updated_date
) VALUES (
    'TEST9 TEST9 10/02/2025',
    'Test9',
    'Test9',
    '2025-10-02',
    'Male',
    '9999',
    'Test9',
    'Test9',
    'Test9',
    'CA',
    '99999',
    'MCR',
    '9999',
    '2025-10-02',
    'Active-Geri',
    'Angelicare',
    'htn, copd, dm',
    '2025-10-01',
    '14:45:00',
    1,
    1,
    13,
    datetime('now'),
    datetime('now')
);

-- 2. Insert into patient_panel table (with correct column names)
INSERT INTO patient_panel (
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    phone_primary,
    email,
    address_street,
    address_city,
    address_state,
    address_zip,
    insurance_primary,
    enrollment_date,
    status,
    facility,
    chronic_conditions_provider,
    last_visit_date,
    assigned_coordinator_id,
    provider_id,
    coordinator_id,
    initial_tv_completed,
    created_date,
    updated_date
) VALUES (
    'TEST9 TEST9 10/02/2025',
    'Test9',
    'Test9',
    '2025-10-02',
    'Male',
    '9999',
    'Test9',
    'Test9',
    'Test9',
    'CA',
    '99999',
    'MCR',
    '2025-10-02',
    'Active-Geri',
    'Angelicare',
    'htn, copd, dm',
    '2025-10-01',
    13,
    4,
    13,
    1,
    datetime('now'),
    datetime('now')
);

-- Verify the insertions
SELECT 'patients table:' as table_name;
SELECT patient_id, first_name, last_name, status FROM patients WHERE patient_id = 'TEST9 TEST9 10/02/2025';

SELECT 'patient_panel table:' as table_name;
SELECT patient_id, first_name, last_name, status FROM patient_panel WHERE patient_id = 'TEST9 TEST9 10/02/2025';

SELECT 'patient_assignments table:' as table_name;
SELECT patient_id, provider_id, coordinator_id, status FROM patient_assignments WHERE patient_id = 'TEST9 TEST9 10/02/2025';

SELECT 'onboarding_patients table:' as table_name;
SELECT onboarding_id, patient_id, first_name, last_name, stage5_complete FROM onboarding_patients WHERE onboarding_id = 13;