-- Update facility in patient_panel from SOURCE_PATIENT_DATA
UPDATE patient_panel
SET facility = (
        SELECT spd."Fac"
        FROM SOURCE_PATIENT_DATA spd
        WHERE spd."LAST FIRST DOB" = patient_panel.patient_id
    )
WHERE patient_panel.patient_id IN (
        SELECT "LAST FIRST DOB"
        FROM SOURCE_PATIENT_DATA
        WHERE "Fac" IS NOT NULL
            AND TRIM("Fac") != ''
    );