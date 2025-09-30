-- Patient Data Transformation Script
-- Transform SOURCE_PATIENT_DATA into patients table
-- This script is REPEATABLE: it will clear the patients table before re-importing.
-- Now includes Initial TV Provider (spd."Initial TV Prov") mapping.
DELETE FROM patients;
INSERT INTO patients (
        patient_id,
        region_id,
        first_name,
        last_name,
        date_of_birth,
        gender,
        phone_primary,
        phone_secondary,
        email,
        address_street,
        address_city,
        address_state,
        address_zip,
        emergency_contact_name,
        emergency_contact_phone,
        emergency_contact_relationship,
        insurance_primary,
        insurance_policy_number,
        insurance_secondary,
        medical_record_number,
        enrollment_date,
        discharge_date,
        notes,
        created_date,
        updated_date,
        created_by,
        updated_by,
        current_facility_id,
        hypertension,
        mental_health_concerns,
        dementia,
        last_annual_wellness_visit,
        last_first_dob,
        status,
        medical_records_requested,
        referral_documents_received,
        insurance_cards_received,
        emed_signature_received,
        last_visit_date,
        facility,
        assigned_coordinator_id,
        er_count_1yr,
        hospitalization_count_1yr,
        clinical_biometric,
        chronic_conditions_provider,
        cancer_history,
        subjective_risk_level,
        provider_mh_schizophrenia,
        provider_mh_depression,
        provider_mh_anxiety,
        provider_mh_stress,
        provider_mh_adhd,
        provider_mh_bipolar,
        provider_mh_suicidal,
        active_specialists,
        code_status,
        cognitive_function,
        functional_status,
        goals_of_care,
        active_concerns,
        initial_tv_completed_date,
        initial_tv_notes,
        service_type,
        appointment_contact_name,
        appointment_contact_phone,
        appointment_contact_email,
        medical_contact_name,
        medical_contact_phone,
        medical_contact_email,
        primary_care_provider,
        pcp_last_seen,
        active_specialist,
        specialist_last_seen,
        chronic_conditions_onboarding,
        mh_schizophrenia,
        mh_depression,
        mh_anxiety,
        mh_stress,
        mh_adhd,
        mh_bipolar,
        mh_suicidal,
        tv_date,
        tv_scheduled,
        patient_notified,
        initial_tv_provider
    )
SELECT DISTINCT 
    -- Standardized patient ID normalization
    TRIM(
        REPLACE(
            REPLACE(
                REPLACE(
                    TRIM(spd."Last") || ' ' || TRIM(spd."First") || ' ' || TRIM(spd."DOB"),
                    ', ',
                    ' '
                ),
                ',',
                ' '
            ),
            '  ',
            ' '
        )
    ) as patient_id,
    NULL as region_id,
    TRIM(spd."First") as first_name,
    TRIM(spd."Last") as last_name,
    spd."DOB" as date_of_birth,
    NULL as gender,
    CASE
        WHEN spd."Phone" IS NOT NULL
        AND spd."Phone" != ''
        AND spd."Phone" != 'zPhone' THEN TRIM(spd."Phone")
        ELSE NULL
    END as phone_primary,
    NULL as phone_secondary,
    NULL as email,
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
    NULL as emergency_contact_phone,
    NULL as emergency_contact_relationship,
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
    NULL as insurance_secondary,
    NULL as medical_record_number,
    NULL as enrollment_date,
    NULL as discharge_date,
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
    NULL as created_by,
    NULL as updated_by,
    CASE
        WHEN spd."Fac" IS NOT NULL
        AND TRIM(spd."Fac") != ''
        AND TRIM(spd."Fac") != 'zFac' THEN (
            SELECT f.facility_id
            FROM facilities f
            WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac"))
            LIMIT 1
        )
        ELSE NULL
    END as current_facility_id,
    0 as hypertension,
    0 as mental_health_concerns,
    0 as dementia,
    NULL as last_annual_wellness_visit,
    -- Standardized patient ID normalization for last_first_dob
    TRIM(
        REPLACE(
            REPLACE(
                REPLACE(
                    TRIM(spd."LAST FIRST DOB"),
                    ', ',
                    ' '
                ),
                ',',
                ' '
            ),
            '  ',
            ' '
        )
    ) as last_first_dob,
    CASE
        WHEN spd."Pt Status" IS NOT NULL
        AND spd."Pt Status" != '' THEN TRIM(spd."Pt Status")
        ELSE 'Active'
    END as status,
    FALSE as medical_records_requested,
    FALSE as referral_documents_received,
    FALSE as insurance_cards_received,
    FALSE as emed_signature_received,
    NULL as last_visit_date,
    NULL as facility,
    NULL as assigned_coordinator_id,
    NULL as er_count_1yr,
    NULL as hospitalization_count_1yr,
    NULL as clinical_biometric,
    NULL as chronic_conditions_provider,
    NULL as cancer_history,
    NULL as subjective_risk_level,
    FALSE as provider_mh_schizophrenia,
    FALSE as provider_mh_depression,
    FALSE as provider_mh_anxiety,
    FALSE as provider_mh_stress,
    FALSE as provider_mh_adhd,
    FALSE as provider_mh_bipolar,
    FALSE as provider_mh_suicidal,
    NULL as active_specialists,
    NULL as code_status,
    NULL as cognitive_function,
    NULL as functional_status,
    NULL as goals_of_care,
    NULL as active_concerns,
    NULLIF(spd."Initial TV Date", '') as initial_tv_completed_date,
    NULLIF(spd."Initial TV Notes", '') as initial_tv_notes,
    NULL as service_type,
    NULL as appointment_contact_name,
    NULL as appointment_contact_phone,
    NULL as appointment_contact_email,
    NULL as medical_contact_name,
    NULL as medical_contact_phone,
    NULL as medical_contact_email,
    NULL as primary_care_provider,
    NULL as pcp_last_seen,
    NULL as active_specialist,
    NULL as specialist_last_seen,
    NULL as chronic_conditions_onboarding,
    FALSE as mh_schizophrenia,
    FALSE as mh_depression,
    FALSE as mh_anxiety,
    FALSE as mh_stress,
    FALSE as mh_adhd,
    FALSE as mh_bipolar,
    FALSE as mh_suicidal,
    NULLIF(spd."Initial TV Date", '') as tv_date,
    CASE
        WHEN spd."Initial TV Date" IS NOT NULL
        AND spd."Initial TV Date" != '' THEN TRUE
        ELSE FALSE
    END as tv_scheduled,
    CASE
        WHEN spd."CM Notified" IS NOT NULL
        AND spd."CM Notified" != '' THEN TRUE
        ELSE FALSE
    END as patient_notified,
    NULLIF(spd."Initial TV Prov", '') as initial_tv_provider
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND TRIM(spd."First") IS NOT NULL
    AND TRIM(spd."Last") IS NOT NULL
    AND spd."DOB" IS NOT NULL;
-- Display summary of transformation
SELECT COUNT(*) as total_patients_transformed,
    COUNT(
        CASE
            WHEN phone_primary IS NOT NULL THEN 1
        END
    ) as patients_with_phone,
    COUNT(
        CASE
            WHEN address_city IS NOT NULL THEN 1
        END
    ) as patients_with_address,
    COUNT(
        CASE
            WHEN insurance_primary IS NOT NULL THEN 1
        END
    ) as patients_with_insurance,
    COUNT(
        CASE
            WHEN notes IS NOT NULL
            AND notes != '' THEN 1
        END
    ) as patients_with_notes
FROM patients;