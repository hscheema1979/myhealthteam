-- Populate patient_panel with denormalized patient, provider, coordinator, and onboarding fields
INSERT
    OR REPLACE INTO patient_panel (
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
        emergency_contact_phone,
        insurance_primary,
        insurance_policy_number,
        status,
        enrollment_date,
        discharge_date,
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
        source_table,
        source_column
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
    p.emergency_contact_phone,
    p.insurance_primary,
    p.insurance_policy_number,
    p.status,
    p.enrollment_date,
    p.discharge_date,
    p.notes,
    p.created_date,
    p.updated_date,
    p.current_facility_id,
    p.hypertension,
    p.mental_health_concerns,
    p.dementia,
    p.last_annual_wellness_visit,
    prov.provider_id,
    prov.provider_name,
    coord.coordinator_id,
    coord.coordinator_name,
    p.stage1_complete,
    p.stage2_complete,
    p.initial_tv_completed,
    p.initial_tv_completed_date,
    p.initial_tv_notes,
    'patients' as source_table,
    'various' as source_column
FROM patients p
    LEFT JOIN (
        SELECT upa.patient_id,
            pr.provider_id,
            u.full_name as provider_name
        FROM user_patient_assignments upa
            JOIN user_roles ur ON upa.user_id = ur.user_id
            JOIN users u ON upa.user_id = u.user_id
            JOIN providers pr ON pr.user_id = u.user_id
        WHERE ur.role_id = 33
    ) prov ON p.patient_id = prov.patient_id
    LEFT JOIN (
        SELECT upa.patient_id,
            upa.user_id as coordinator_id,
            u.full_name as coordinator_name
        FROM user_patient_assignments upa
            JOIN user_roles ur ON upa.user_id = ur.user_id
            JOIN users u ON upa.user_id = u.user_id
        WHERE ur.role_id = 36
    ) coord ON p.patient_id = coord.patient_id;