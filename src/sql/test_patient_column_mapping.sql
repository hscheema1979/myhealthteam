-- Test script to map SOURCE_PATIENT_DATA columns to patients table structure
-- This script shows how each column would be derived without modifying the patients table
SELECT -- Primary key - will be auto-generated
    ROW_NUMBER() OVER (
        ORDER BY spd."LAST FIRST DOB"
    ) as proposed_patient_id,
    -- Basic patient information
    spd."First" as first_name,
    spd."Last" as last_name,
    spd."DOB" as date_of_birth,
    spd."LAST FIRST DOB" as last_first_dob,
    -- Contact information
    spd."Phone" as phone_primary,
    NULL as phone_secondary,
    -- Not available in source
    NULL as email,
    -- Not available in source
    -- Address information
    spd."Street" as address_street,
    spd."City" as address_city,
    spd."State" as address_state,
    spd."Zip" as address_zip,
    -- Emergency contact
    spd."Contact Name" as emergency_contact_name,
    NULL as emergency_contact_phone,
    -- Not available in source
    NULL as emergency_contact_relationship,
    -- Not available in source
    -- Insurance information
    spd."Ins1" as insurance_primary,
    spd."Policy" as insurance_policy_number,
    NULL as insurance_secondary,
    -- Not available in source
    -- Medical/system information
    NULL as medical_record_number,
    -- Not available in source
    spd."Pt Status" as status,
    NULL as enrollment_date,
    -- Not available in source
    NULL as discharge_date,
    -- Not available in source
    -- Region mapping - regions table doesn't have region_name, will need manual mapping
    NULL as region_id,
    -- Will need to create region mapping logic separately
    spd."Region" as region_name_source,
    -- Facility mapping - need to map facility name to facility_id
    CASE
        WHEN spd."Fac" IS NOT NULL
        AND spd."Fac" != '' THEN (
            SELECT f.facility_id
            FROM facilities f
            WHERE f.facility_name = spd."Fac"
            LIMIT 1
        )
        ELSE NULL
    END as current_facility_id,
    spd."Fac" as facility_name_source,
    -- Notes and additional fields
    COALESCE(
        spd."List6 Notes",
        spd."Prescreen Call Notes",
        spd."Initial TV Notes",
        spd."TV Note",
        spd."eMed Records Routing Notes",
        spd."Schedule HV 2w Notes"
    ) as notes,
    -- Health conditions - not available in source, set to defaults
    NULL as gender,
    -- Not available in source
    0 as hypertension,
    -- Default to 0 (false)
    0 as mental_health_concerns,
    -- Default to 0 (false)  
    0 as dementia,
    -- Default to 0 (false)
    NULL as last_annual_wellness_visit,
    -- Not available in source
    -- Audit fields
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date,
    NULL as created_by,
    -- Will be set during actual insert
    NULL as updated_by,
    -- Will be set during actual insert
    -- Source data for reference
    spd."Initial TV Prov" as initial_tv_provider_source,
    spd."Recommended  Reg Prov" as recommended_provider_source,
    spd."Assigned  Reg Prov" as assigned_provider_source,
    spd."Assigned CM" as assigned_coordinator_source,
    spd."Rep(s)" as representatives_source
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB' -- Skip header row if present
ORDER BY spd."LAST FIRST DOB"
LIMIT 10;