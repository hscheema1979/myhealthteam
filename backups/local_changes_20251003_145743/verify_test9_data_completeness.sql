-- Comprehensive data verification for TEST9 patient
-- Compare onboarding data with patients and patient_panel tables

-- 1. Basic demographic data comparison
SELECT 'DEMOGRAPHIC COMPARISON:' as section;
SELECT 
    'ONBOARDING' as source,
    first_name, last_name, date_of_birth, gender, 
    address, city, state, zip_code, phone, insurance_type
FROM onboarding_patients WHERE onboarding_id = 13

UNION ALL

SELECT 
    'PATIENTS' as source,
    first_name, last_name, date_of_birth, gender,
    address, city, state, zip_code, phone, insurance_type
FROM patients WHERE patient_id = 'TEST9 TEST9 10/02/2025';

-- 2. Medical conditions comparison
SELECT 'MEDICAL CONDITIONS COMPARISON:' as section;
SELECT 
    'ONBOARDING' as source,
    hypertension, mental_health_concerns, dementia,
    chronic_conditions_onboarding as chronic_conditions
FROM onboarding_patients WHERE onboarding_id = 13

UNION ALL

SELECT 
    'PATIENT_PANEL' as source,
    hypertension, mental_health_concerns, dementia,
    chronic_conditions_provider as chronic_conditions
FROM patient_panel WHERE patient_id = 'TEST9 TEST9 10/02/2025';

-- 3. Assignment and workflow status comparison
SELECT 'ASSIGNMENT STATUS COMPARISON:' as section;
SELECT 
    'ONBOARDING' as source,
    assigned_provider_user_id, assigned_coordinator_user_id,
    tv_scheduled, initial_tv_completed, stage5_complete
FROM onboarding_patients WHERE onboarding_id = 13

UNION ALL

SELECT 
    'PATIENTS' as source,
    assigned_provider_user_id, assigned_coordinator_user_id,
    tv_scheduled, initial_tv_completed, NULL as stage5_complete
FROM patients WHERE patient_id = 'TEST9 TEST9 10/02/2025';

-- 4. Verify patient_assignments table
SELECT 'PATIENT ASSIGNMENTS:' as section;
SELECT patient_id, provider_id, coordinator_id, status, created_date
FROM patient_assignments WHERE patient_id = 'TEST9 TEST9 10/02/2025';

-- 5. Check for any missing critical fields
SELECT 'CRITICAL FIELDS CHECK:' as section;
SELECT 
    CASE WHEN patient_id IS NULL THEN 'MISSING patient_id' ELSE 'OK patient_id' END as patient_id_status,
    CASE WHEN assigned_provider_user_id IS NULL THEN 'MISSING provider' ELSE 'OK provider' END as provider_status,
    CASE WHEN assigned_coordinator_user_id IS NULL THEN 'MISSING coordinator' ELSE 'OK coordinator' END as coordinator_status,
    CASE WHEN tv_scheduled = 0 THEN 'NOT SCHEDULED' ELSE 'SCHEDULED' END as tv_status,
    CASE WHEN initial_tv_completed = 0 THEN 'NOT COMPLETED' ELSE 'COMPLETED' END as initial_tv_status,
    CASE WHEN stage5_complete = 0 THEN 'NOT COMPLETE' ELSE 'COMPLETE' END as stage5_status
FROM onboarding_patients WHERE onboarding_id = 13;