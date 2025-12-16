-- Complete Patient Transformation - CORRECTED VERSION
-- This script handles the complete patient transformation process including all foreign key relationships
-- STEP 1: Create missing facilities first
INSERT
    OR IGNORE INTO facilities (facility_name)
SELECT DISTINCT TRIM(spd."Fac") as facility_name
FROM SOURCE_PATIENT_DATA spd
WHERE spd."Fac" IS NOT NULL
    AND spd."Fac" != ''
    AND spd."Fac" != 'zFac';
-- STEP 2: Insert patients with all available data (avoiding duplicates)
INSERT
    OR IGNORE INTO patients (
        first_name,
        last_name,
        date_of_birth,
        last_first_dob,
        phone_primary,
        address_street,
        address_city,
        address_state,
        address_zip,
        emergency_contact_name,
        insurance_primary,
        insurance_policy_number,
        status,
        notes,
        created_date,
        updated_date,
        region_id,
        current_facility_id,
        gender,
        hypertension,
        mental_health_concerns,
        dementia
    )
SELECT DISTINCT TRIM(spd."First") as first_name,
    TRIM(spd."Last") as last_name,
    spd."DOB" as date_of_birth,
    TRIM(spd."LAST FIRST DOB") as last_first_dob,
    CASE
        WHEN spd."Phone" IS NOT NULL
        AND spd."Phone" != ''
        AND spd."Phone" != 'zPhone' THEN TRIM(spd."Phone")
        ELSE NULL
    END as phone_primary,
    CASE
        WHEN spd."Street" IS NOT NULL
        AND spd."Street" != ''
        AND spd."Street" != 'zStreet' THEN TRIM(spd."Street")
        ELSE NULL
    END as address_street,
    CASE
        WHEN spd."City" IS NOT NULL
        AND spd."City" != ''
        AND spd."City" != 'zCity' THEN TRIM(spd."City")
        ELSE NULL
    END as address_city,
    CASE
        WHEN spd."State" IS NOT NULL
        AND spd."State" != ''
        AND spd."State" != 'zState' THEN TRIM(spd."State")
        ELSE NULL
    END as address_state,
    CASE
        WHEN spd."Zip" IS NOT NULL
        AND spd."Zip" != ''
        AND spd."Zip" != 'zZip' THEN TRIM(spd."Zip")
        ELSE NULL
    END as address_zip,
    CASE
        WHEN spd."Contact Name" IS NOT NULL
        AND spd."Contact Name" != ''
        AND spd."Contact Name" != 'zContact' THEN TRIM(spd."Contact Name")
        ELSE NULL
    END as emergency_contact_name,
    CASE
        WHEN spd."Ins1" IS NOT NULL
        AND spd."Ins1" != ''
        AND spd."Ins1" != 'zIns' THEN TRIM(spd."Ins1")
        ELSE NULL
    END as insurance_primary,
    CASE
        WHEN spd."Policy" IS NOT NULL
        AND spd."Policy" != ''
        AND spd."Policy" != 'zPolicy' THEN TRIM(spd."Policy")
        ELSE NULL
    END as insurance_policy_number,
    CASE
        WHEN spd."Pt Status" IS NOT NULL
        AND spd."Pt Status" != '' THEN TRIM(spd."Pt Status")
        ELSE 'Active'
    END as status,
    TRIM(
        COALESCE(
            NULLIF(spd."List6 Notes", ''),
            NULLIF(spd."Prescreen Call Notes", ''),
            NULLIF(spd."Initial TV Notes", ''),
            NULLIF(spd."TV Note", ''),
            NULLIF(spd."eMed Records Routing Notes", ''),
            NULLIF(spd."Schedule HV 2w Notes", ''),
            ''
        )
    ) as notes,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date,
    -- Map region_id by looking up regions table
    (
        SELECT r.region_id
        FROM regions r
        WHERE LOWER(TRIM(r.region_name)) = LOWER(TRIM(spd."Region"))
        LIMIT 1
    ) as region_id,
    -- Map facility_id by looking up facilities table  
    (
        SELECT f.facility_id
        FROM facilities f
        WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac"))
        LIMIT 1
    ) as current_facility_id,
    NULL as gender,
    0 as hypertension,
    0 as mental_health_concerns,
    0 as dementia
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND TRIM(spd."First") IS NOT NULL
    AND TRIM(spd."Last") IS NOT NULL
    AND spd."DOB" IS NOT NULL;
-- STEP 3: Create patient assignments for coordinators (using staff codes, not names)
-- First, let's see if we can match coordinator names to existing staff codes
-- This will need to be done based on the actual data mapping
-- For now, create placeholder assignments for patients with coordinator info
INSERT
    OR IGNORE INTO patient_assignments (
        patient_id,
        assignment_date,
        assignment_type,
        status,
        priority_level,
        notes,
        created_date,
        updated_date
    )
SELECT DISTINCT p.patient_id,
    CURRENT_TIMESTAMP as assignment_date,
    'coordinator' as assignment_type,
    CASE
        WHEN p.status LIKE '%Active%' THEN 'active'
        ELSE 'inactive'
    END as status,
    'standard' as priority_level,
    'Imported from SOURCE_PATIENT_DATA - Assigned CM: ' || spd."Assigned CM" as notes,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date
FROM SOURCE_PATIENT_DATA spd
    JOIN patients p ON p.last_first_dob = spd."LAST FIRST DOB"
WHERE spd."Assigned CM" IS NOT NULL
    AND spd."Assigned CM" != '';
-- STEP 4: Create care plans for all patients
INSERT
    OR IGNORE INTO care_plans (
        patient_id,
        plan_name,
        status,
        start_date,
        created_date,
        updated_date
    )
SELECT p.patient_id,
    'Standard Care Plan' as plan_name,
    CASE
        WHEN p.status LIKE '%Active%' THEN 'active'
        ELSE 'inactive'
    END as status,
    CURRENT_TIMESTAMP as start_date,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date
FROM patients p;
-- STEP 5: Update dashboard summaries
INSERT
    OR IGNORE INTO dashboard_patient_assignment_summary (
        patient_id,
        region_id,
        assignment_date,
        status
    )
SELECT p.patient_id,
    p.region_id,
    pa.assignment_date,
    pa.status
FROM patients p
    LEFT JOIN patient_assignments pa ON pa.patient_id = p.patient_id
    AND pa.assignment_type = 'coordinator';
-- STEP 6: Create geographic mappings
INSERT
    OR IGNORE INTO dashboard_patient_county_map (patient_id, county_name, region_id)
SELECT p.patient_id,
    CASE
        WHEN LOWER(p.address_city) LIKE '%los angeles%' THEN 'Los Angeles'
        WHEN LOWER(p.address_city) LIKE '%orange%' THEN 'Orange'
        WHEN LOWER(p.address_city) LIKE '%riverside%' THEN 'Riverside'
        WHEN LOWER(p.address_city) LIKE '%san bernardino%' THEN 'San Bernardino'
        WHEN LOWER(p.address_city) LIKE '%ventura%' THEN 'Ventura'
        ELSE 'Unknown'
    END as county_name,
    p.region_id
FROM patients p;
INSERT
    OR IGNORE INTO dashboard_patient_zip_map (patient_id, zip_code, region_id)
SELECT p.patient_id,
    p.address_zip,
    p.region_id
FROM patients p
WHERE p.address_zip IS NOT NULL
    AND p.address_zip != '';
-- STEP 7: Final summary report
SELECT 'PATIENT TRANSFORMATION COMPLETE' as summary,
    '' as details
UNION ALL
SELECT 'Total Patients in Database:',
    COUNT(*)
FROM patients
UNION ALL
SELECT 'Patients with Regions:',
    COUNT(region_id)
FROM patients
UNION ALL
SELECT 'Patients with Facilities:',
    COUNT(current_facility_id)
FROM patients
UNION ALL
SELECT 'Patient Assignments Created:',
    COUNT(*)
FROM patient_assignments
WHERE assignment_type = 'coordinator'
UNION ALL
SELECT 'Care Plans Created:',
    COUNT(*)
FROM care_plans
UNION ALL
SELECT 'Dashboard Assignment Records:',
    COUNT(*)
FROM dashboard_patient_assignment_summary
UNION ALL
SELECT 'Geographic County Mappings:',
    COUNT(*)
FROM dashboard_patient_county_map
UNION ALL
SELECT 'Geographic ZIP Mappings:',
    COUNT(*)
FROM dashboard_patient_zip_map
UNION ALL
SELECT 'Facilities Available:',
    COUNT(*)
FROM facilities;