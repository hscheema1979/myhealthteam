-- Repeatable nightly refresh of patient_panel with all key columns
DELETE FROM patient_panel;
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
        last_visit_date,
        facility,
        goals_of_care,
        code_status
    )
SELECT p.patient_id,
    p.first_name,
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
    TRIM(COALESCE(p.notes, '')) AS notes,
    p.created_date,
    p.updated_date,
    p.current_facility_id,
    p.hypertension,
    p.mental_health_concerns,
    p.dementia,
    p.last_annual_wellness_visit,
    pa.provider_id,
    up.full_name AS provider_name,
    pa.coordinator_id,
    uc.full_name AS coordinator_name,
    pv.last_visit_date,
    spd.[Fac] AS facility,
    p.goals_of_care,
    p.code_status
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
    LEFT JOIN users uc ON pa.coordinator_id = uc.user_id
    LEFT JOIN patient_visits pv ON p.patient_id = pv.patient_id
    LEFT JOIN SOURCE_PATIENT_DATA spd ON p.patient_id = spd.[LAST FIRST DOB];