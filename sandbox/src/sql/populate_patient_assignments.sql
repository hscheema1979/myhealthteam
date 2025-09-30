DELETE FROM patient_assignments;
-- Insert one row per patient with both provider and coordinator assignments if available
INSERT INTO patient_assignments (
        patient_id,
        provider_id,
        coordinator_id,
        assignment_date,
        assignment_type,
        status,
        priority_level,
        notes,
        created_date,
        updated_date,
        initial_tv_provider_id
    )
SELECT p.patient_id,
    -- Provider assignment
    (
        SELECT u.user_id
        FROM SOURCE_PATIENT_DATA spd2
            JOIN users u ON TRIM(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(spd2."Assigned  Reg Prov", 'MD', ''),
                                        'NP',
                                        ''
                                    ),
                                    'PA',
                                    ''
                                ),
                                'ZZ',
                                ''
                            ),
                            ' ,',
                            ','
                        ),
                        ', ',
                        ','
                    ),
                    '  ',
                    ' '
                )
            ) = TRIM(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(REPLACE(u.full_name, 'MD', ''), 'NP', ''),
                                    'PA',
                                    ''
                                ),
                                'ZZ',
                                ''
                            ),
                            ' ,',
                            ','
                        ),
                        ', ',
                        ','
                    ),
                    '  ',
                    ' '
                )
            )
        WHERE spd2."Assigned  Reg Prov" IS NOT NULL
            AND spd2."Assigned  Reg Prov" != ''
            AND TRIM(spd2."Last") || ' ' || TRIM(spd2."First") || ' ' || TRIM(spd2."DOB") = p.patient_id
        LIMIT 1
    ) AS provider_id,
    -- Coordinator assignment
    (
        SELECT u.user_id
        FROM SOURCE_PATIENT_DATA spd2
            JOIN users u ON LOWER(TRIM(u.first_name)) = LOWER(
                TRIM(
                    CASE
                        WHEN INSTR(spd2."Assigned CM", ',') > 0 THEN SUBSTR(
                            spd2."Assigned CM",
                            INSTR(spd2."Assigned CM", ',') + 1
                        )
                        ELSE spd2."Assigned CM"
                    END
                )
            )
        WHERE spd2."Assigned CM" IS NOT NULL
            AND spd2."Assigned CM" != ''
            AND TRIM(spd2."Last") || ' ' || TRIM(spd2."First") || ' ' || TRIM(spd2."DOB") = p.patient_id
        LIMIT 1
    ) AS coordinator_id,
    CURRENT_TIMESTAMP as assignment_date,
    'both' as assignment_type,
    CASE
        WHEN p.status LIKE '%Active%' THEN 'active'
        ELSE 'inactive'
    END as status,
    'standard' as priority_level,
    'Imported from SOURCE_PATIENT_DATA' as notes,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date,
    NULL as initial_tv_provider_id
FROM patients p;