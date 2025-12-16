.mode csv
.headers on

-- Check patient_panel for non-numeric provider_id/coordinator_id
.output scripts/outputs/reports/patient_panel_non_numeric_ids.csv
SELECT patient_id,
       provider_id,
       coordinator_id,
       provider_name,
       coordinator_name
FROM patient_panel
WHERE (CAST(provider_id AS TEXT) NOT GLOB '[0-9]*' AND provider_id IS NOT NULL)
   OR (CAST(coordinator_id AS TEXT) NOT GLOB '[0-9]*' AND coordinator_id IS NOT NULL);
.output stdout

-- Check user_patient_assignments for non-numeric IDs
.output scripts/outputs/reports/user_patient_assignments_non_numeric_ids.csv
SELECT patient_id,
       user_id,
       role_id
FROM user_patient_assignments
WHERE CAST(user_id AS TEXT) NOT GLOB '[0-9]*' AND user_id IS NOT NULL;
.output stdout

-- Optional: panel rows missing names for mapped IDs (diagnostic)
.output scripts/outputs/reports/patient_panel_missing_names_for_ids.csv
SELECT pp.patient_id,
       pp.provider_id,
       pp.coordinator_id
FROM patient_panel pp
LEFT JOIN users u1 ON pp.provider_id = u1.user_id
LEFT JOIN users u2 ON pp.coordinator_id = u2.user_id
WHERE (pp.provider_id IS NOT NULL AND (pp.provider_name IS NULL OR TRIM(pp.provider_name) = '') AND u1.user_id IS NOT NULL)
   OR (pp.coordinator_id IS NOT NULL AND (pp.coordinator_name IS NULL OR TRIM(pp.coordinator_name) = '') AND u2.user_id IS NOT NULL);
.output stdout