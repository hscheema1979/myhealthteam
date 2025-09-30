-- Update patient_panel from patient_visits
UPDATE patient_panel
SET last_visit_date = (
                SELECT v.last_visit_date
                FROM patient_visits v
                WHERE v.patient_id = REPLACE(
                                patient_panel.last_name || ' ' || patient_panel.first_name || ' ' || patient_panel.date_of_birth,
                                ',',
                                ''
                        )
        ),
        last_visit_service_type = (
                SELECT v.service_type
                FROM patient_visits v
                WHERE v.patient_id = REPLACE(
                                patient_panel.last_name || ' ' || patient_panel.first_name || ' ' || patient_panel.date_of_birth,
                                ',',
                                ''
                        )
        )
WHERE EXISTS (
                SELECT 1
                FROM patient_visits v
                WHERE v.patient_id = REPLACE(
                                patient_panel.last_name || ' ' || patient_panel.first_name || ' ' || patient_panel.date_of_birth,
                                ',',
                                ''
                        )
        );
-- Update patients from patient_visits
UPDATE patients
SET last_visit_date = (
                SELECT v.last_visit_date
                FROM patient_visits v
                WHERE v.patient_id = REPLACE(
                                patients.last_name || ' ' || patients.first_name || ' ' || patients.date_of_birth,
                                ',',
                                ''
                        )
        ),
        service_type = (
                SELECT v.service_type
                FROM patient_visits v
                WHERE v.patient_id = REPLACE(
                                patients.last_name || ' ' || patients.first_name || ' ' || patients.date_of_birth,
                                ',',
                                ''
                        )
        )
WHERE EXISTS (
                SELECT 1
                FROM patient_visits v
                WHERE v.patient_id = REPLACE(
                                patients.last_name || ' ' || patients.first_name || ' ' || patients.date_of_birth,
                                ',',
                                ''
                        )
        );