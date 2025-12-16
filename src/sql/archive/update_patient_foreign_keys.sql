-- Master Patient Foreign Key Update Script
-- Updates all tables that have patient_id foreign keys after patient population
-- Step 1: Update user_patient_assignments based on coordinator assignments
INSERT INTO user_patient_assignments (user_id, patient_id, role_id)
SELECT DISTINCT u.user_id,
    p.patient_id,
    ur.role_id
FROM SOURCE_PATIENT_DATA spd
    JOIN patients p ON p.last_first_dob = spd."LAST FIRST DOB"
    JOIN staff_code_mapping scm ON LOWER(TRIM(spd."Assigned CM")) = LOWER(TRIM(scm.staff_name))
    JOIN users u ON scm.user_id = u.user_id
    JOIN user_roles ur ON ur.role_name = 'Care Coordinator' -- Assuming this role exists
WHERE spd."Assigned CM" IS NOT NULL
    AND spd."Assigned CM" != ''
    AND scm.confidence_level = 'HIGH'
    AND NOT EXISTS (
        SELECT 1
        FROM user_patient_assignments upa
        WHERE upa.user_id = u.user_id
            AND upa.patient_id = p.patient_id
            AND upa.role_id = ur.role_id
    );
-- Step 2: Update dashboard_patient_assignment_summary
-- This table tracks patient assignment metrics
INSERT INTO dashboard_patient_assignment_summary (
        patient_id,
        region_id,
        coordinator_id,
        provider_id,
        assignment_date,
        status
    )
SELECT DISTINCT p.patient_id,
    p.region_id,
    pa.coordinator_id,
    pa.provider_id,
    pa.assignment_date,
    pa.status
FROM patients p
    LEFT JOIN patient_assignments pa ON pa.patient_id = p.patient_id
WHERE NOT EXISTS (
        SELECT 1
        FROM dashboard_patient_assignment_summary dpas
        WHERE dpas.patient_id = p.patient_id
    );
-- Step 3: Update dashboard_region_patient_assignment_summary
-- This tracks patient assignments by region
INSERT INTO dashboard_region_patient_assignment_summary (
        region_id,
        patient_id,
        coordinator_id,
        assignment_date,
        status
    )
SELECT DISTINCT p.region_id,
    p.patient_id,
    pa.coordinator_id,
    pa.assignment_date,
    pa.status
FROM patients p
    LEFT JOIN patient_assignments pa ON pa.patient_id = p.patient_id
WHERE p.region_id IS NOT NULL
    AND NOT EXISTS (
        SELECT 1
        FROM dashboard_region_patient_assignment_summary drpas
        WHERE drpas.patient_id = p.patient_id
            AND drpas.region_id = p.region_id
    );
-- Step 4: Update dashboard_patient_county_map and dashboard_patient_zip_map
-- These tables map patients to geographic areas
-- County mapping (extract county from address or use region mapping)
INSERT INTO dashboard_patient_county_map (patient_id, county_name, region_id)
SELECT DISTINCT p.patient_id,
    COALESCE(
        -- Try to extract county from address_city
        CASE
            WHEN LOWER(p.address_city) LIKE '%los angeles%' THEN 'Los Angeles'
            WHEN LOWER(p.address_city) LIKE '%orange%' THEN 'Orange'
            WHEN LOWER(p.address_city) LIKE '%riverside%' THEN 'Riverside'
            WHEN LOWER(p.address_city) LIKE '%san bernardino%' THEN 'San Bernardino'
            WHEN LOWER(p.address_city) LIKE '%ventura%' THEN 'Ventura'
            ELSE 'Unknown'
        END,
        'Unknown'
    ) as county_name,
    p.region_id
FROM patients p
WHERE NOT EXISTS (
        SELECT 1
        FROM dashboard_patient_county_map dpcm
        WHERE dpcm.patient_id = p.patient_id
    );
-- ZIP code mapping
INSERT INTO dashboard_patient_zip_map (patient_id, zip_code, region_id)
SELECT DISTINCT p.patient_id,
    p.address_zip,
    p.region_id
FROM patients p
WHERE p.address_zip IS NOT NULL
    AND p.address_zip != ''
    AND NOT EXISTS (
        SELECT 1
        FROM dashboard_patient_zip_map dpzm
        WHERE dpzm.patient_id = p.patient_id
    );
-- Step 5: Create initial care plans for new patients
INSERT INTO care_plans (
        patient_id,
        plan_name,
        status,
        start_date,
        created_date,
        updated_date
    )
SELECT DISTINCT p.patient_id,
    'Standard Care Plan' as plan_name,
    CASE
        WHEN p.status = 'Active' THEN 'active'
        ELSE 'inactive'
    END as status,
    CURRENT_TIMESTAMP as start_date,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date
FROM patients p
WHERE NOT EXISTS (
        SELECT 1
        FROM care_plans cp
        WHERE cp.patient_id = p.patient_id
    );
-- Step 6: Update patient_region_mapping table if it exists and is separate
-- (Some systems have a separate mapping table)
INSERT
    OR IGNORE INTO patient_region_mapping (patient_id, region_id)
SELECT p.patient_id,
    p.region_id
FROM patients p
WHERE p.region_id IS NOT NULL;
-- Show summary of all updates
SELECT 'Summary of Foreign Key Updates:' as section,
    '' as details
UNION ALL
SELECT 'User Patient Assignments:',
    COUNT(*) || ' assignments created'
FROM user_patient_assignments
WHERE EXISTS (
        SELECT 1
        FROM patients p
        WHERE p.patient_id = user_patient_assignments.patient_id
    )
UNION ALL
SELECT 'Patient Assignment Summary:',
    COUNT(*) || ' records created'
FROM dashboard_patient_assignment_summary
UNION ALL
SELECT 'Region Assignment Summary:',
    COUNT(*) || ' records created'
FROM dashboard_region_patient_assignment_summary
UNION ALL
SELECT 'Patient County Mappings:',
    COUNT(*) || ' mappings created'
FROM dashboard_patient_county_map
UNION ALL
SELECT 'Patient ZIP Mappings:',
    COUNT(*) || ' mappings created'
FROM dashboard_patient_zip_map
UNION ALL
SELECT 'Care Plans Created:',
    COUNT(*) || ' care plans initialized'
FROM care_plans
WHERE EXISTS (
        SELECT 1
        FROM patients p
        WHERE p.patient_id = care_plans.patient_id
    )
UNION ALL
SELECT 'Patient Region Mappings:',
    COUNT(*) || ' region mappings created'
FROM patient_region_mapping;