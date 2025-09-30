-- Repeatable: clear patients before insert
DELETE FROM patients;
INSERT INTO patients (
        patient_id,
        region_id,
        first_name,
        last_name,
        date_of_birth,
        phone_primary,
        address_street,
        address_city,
        address_state,
        address_zip,
        status,
        notes
    )
SELECT spd."LAST FIRST DOB",
    CAST(spd."Region" AS INT),
    spd."First",
    spd."Last",
    spd."DOB",
    spd."Phone",
    spd."Street",
    spd."City",
    spd."State",
    spd."Zip",
    spd."Pt Status",
    spd."Initial TV Notes"
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND TRIM(spd."LAST FIRST DOB") != '';
-- Repeatable: clear patient_assignments before insert
DELETE FROM patient_assignments;
INSERT INTO patient_assignments (
        patient_id,
        provider_id,
        coordinator_id,
        assignment_type,
        initial_tv_provider_id,
        assignment_date,
        status
    )
SELECT spd."LAST FIRST DOB",
    CAST(spd."Assigned  Reg Prov" AS INT),
    CAST(spd."Assigned CM" AS INT),
    'provider',
    CAST(spd."Initial TV Prov" AS INT),
    spd."Initial TV Date",
    spd."Pt Status"
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND TRIM(spd."LAST FIRST DOB") != ''
    AND spd."Assigned  Reg Prov" IS NOT NULL
    AND TRIM(spd."Assigned  Reg Prov") != ''
    AND spd."Assigned CM" IS NOT NULL
    AND TRIM(spd."Assigned CM") != '';
-- Ensure Initial TV Provider role exists in roles
INSERT INTO roles (role_id, role_name, description)
SELECT 41,
    'INITIAL_TV_PROVIDER',
    'Initial TV Provider role'
WHERE NOT EXISTS (
        SELECT 1
        FROM roles
        WHERE role_id = 41
    );
-- Repeatable: remove only Andrews' Initial TV Provider role before re-adding
DELETE FROM user_roles
WHERE user_id = 105
    AND role_id = 41;
INSERT INTO user_roles (user_id, role_id, is_primary)
SELECT 105,
    41,
    1;
DELETE FROM patient_region_mapping;
INSERT INTO patient_region_mapping (
        patient_id,
        region_id,
        zip_code,
        city,
        state,
        created_date
    )
SELECT spd."LAST FIRST DOB",
    CAST(spd."Region" AS INT),
    spd."Zip",
    spd."City",
    spd."State",
    CURRENT_TIMESTAMP
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND TRIM(spd."LAST FIRST DOB") != ''
    AND spd."Region" IS NOT NULL
    AND TRIM(spd."Region") != '';
-- Repeatable: clear patient_panel before insert
DELETE FROM patient_panel;
INSERT INTO patient_panel (
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
        emergency_contact_name,
        insurance_primary,
        insurance_policy_number,
        status,
        notes,
        created_date,
        updated_date,
        current_facility_id,
        hypertension,
        mental_health_concerns,
        dementia,
        last_annual_wellness_visit,
        provider_id,
        provider_name,
        coordinator_id,
        coordinator_name,
        stage1_complete,
        stage2_complete,
        initial_tv_completed,
        initial_tv_completed_date,
        initial_tv_notes,
        source_table
    )
SELECT p.first_name,
    p.last_name,
    p.date_of_birth,
    p.gender,
    p.phone_primary,
    p.email,
    p.address_street,
    p.address_city,
    p.address_state,
    p.address_zip,
    p.emergency_contact_name,
    p.insurance_primary,
    p.insurance_policy_number,
    p.status,
    TRIM(
        COALESCE(p.notes, '') || CASE
            WHEN p.initial_tv_notes IS NOT NULL
            AND p.initial_tv_notes != '' THEN '\nInitial TV: ' || p.initial_tv_notes
            ELSE ''
        END
    ) as notes,
    p.created_date,
    p.updated_date,
    p.current_facility_id,
    p.hypertension,
    p.mental_health_concerns,
    p.dementia,
    p.last_annual_wellness_visit,
    pa.provider_id,
    up.full_name as provider_name,
    pa.coordinator_id,
    uc.full_name as coordinator_name,
    NULL,
    -- stage1_complete
    NULL,
    -- stage2_complete
    NULL,
    -- initial_tv_completed
    p.initial_tv_completed_date,
    p.initial_tv_notes,
    'patients'
FROM patients p
    LEFT JOIN (
        SELECT patient_id,
            MAX(
                CASE
                    WHEN assignment_type = 'provider' THEN provider_id
                END
            ) AS provider_id,
            MAX(
                CASE
                    WHEN assignment_type = 'coordinator' THEN coordinator_id
                END
            ) AS coordinator_id
        FROM patient_assignments
        GROUP BY patient_id
    ) pa ON pa.patient_id = p.patient_id
    LEFT JOIN users up ON pa.provider_id = up.user_id
    LEFT JOIN users uc ON pa.coordinator_id = uc.user_id;