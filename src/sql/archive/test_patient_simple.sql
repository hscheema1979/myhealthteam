-- Simple Patient Transformation Test - First 10 Records
-- Test basic patient data transformation
SELECT ROW_NUMBER() OVER (
        ORDER BY spd."LAST FIRST DOB"
    ) as row_num,
    TRIM(spd."First") as first_name,
    TRIM(spd."Last") as last_name,
    spd."DOB" as date_of_birth,
    CASE
        WHEN spd."Phone" IS NOT NULL
        AND spd."Phone" != ''
        AND spd."Phone" != 'zPhone' THEN TRIM(spd."Phone")
        ELSE 'N/A'
    END as phone,
    CASE
        WHEN spd."Pt Status" IS NOT NULL
        AND spd."Pt Status" != '' THEN TRIM(spd."Pt Status")
        ELSE 'Active'
    END as status
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL
    AND spd."LAST FIRST DOB" != ''
    AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    AND TRIM(spd."First") IS NOT NULL
    AND TRIM(spd."Last") IS NOT NULL
    AND spd."DOB" IS NOT NULL
ORDER BY spd."LAST FIRST DOB"
LIMIT 10;