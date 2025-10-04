.headers on
.mode table

-- Check onboarding_patients table for TEST 9
SELECT 'ONBOARDING_PATIENTS TABLE:' as table_name;
SELECT onboarding_id, patient_id, first_name, last_name, date_of_birth, stage5_complete 
FROM onboarding_patients 
WHERE (first_name LIKE '%TEST%' AND last_name LIKE '%9%') 
   OR (first_name = 'TEST' AND last_name = '9');

-- Check patients table for TEST 9
SELECT 'PATIENTS TABLE:' as table_name;
SELECT patient_id, first_name, last_name, date_of_birth 
FROM patients 
WHERE (first_name LIKE '%TEST%' AND last_name LIKE '%9%') 
   OR (first_name = 'TEST' AND last_name = '9');

-- Check patient_panel table for TEST 9
SELECT 'PATIENT_PANEL TABLE:' as table_name;
SELECT patient_id, first_name, last_name, date_of_birth 
FROM patient_panel 
WHERE (first_name LIKE '%TEST%' AND last_name LIKE '%9%') 
   OR (first_name = 'TEST' AND last_name = '9');

-- Check patient_assignments table for TEST 9
SELECT 'PATIENT_ASSIGNMENTS TABLE:' as table_name;
SELECT assignment_id, patient_id, provider_id, coordinator_id, assignment_type, status 
FROM patient_assignments 
WHERE patient_id IN (
    SELECT patient_id FROM patients 
    WHERE (first_name LIKE '%TEST%' AND last_name LIKE '%9%') 
       OR (first_name = 'TEST' AND last_name = '9')
);