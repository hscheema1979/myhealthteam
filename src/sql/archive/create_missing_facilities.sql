-- Create Missing Facilities Script
-- Add any facilities from SOURCE_PATIENT_DATA that don't exist in facilities table
-- First, show what facilities exist currently
SELECT 'Current Facilities:' as info,
    facility_name
FROM facilities;
-- Show what facilities are needed from source data
SELECT 'Facilities Needed:' as info,
    TRIM(spd."Fac") as facility_name,
    COUNT(*) as patient_count
FROM SOURCE_PATIENT_DATA spd
WHERE spd."Fac" IS NOT NULL
    AND spd."Fac" != ''
    AND spd."Fac" != 'zFac'
    AND NOT EXISTS (
        SELECT 1
        FROM facilities f
        WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac"))
    )
GROUP BY TRIM(spd."Fac")
ORDER BY patient_count DESC;
-- Insert missing facilities
INSERT INTO facilities (facility_name, address, phone, email)
SELECT DISTINCT TRIM(spd."Fac") as facility_name,
    NULL as address,
    -- No address data in source
    NULL as phone,
    -- No phone data in source  
    NULL as email -- No email data in source
FROM SOURCE_PATIENT_DATA spd
WHERE spd."Fac" IS NOT NULL
    AND spd."Fac" != ''
    AND spd."Fac" != 'zFac'
    AND NOT EXISTS (
        SELECT 1
        FROM facilities f
        WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac"))
    );
-- Show results
SELECT 'Facilities Added:' as info,
    COUNT(*) || ' new facilities created' as details
FROM facilities
WHERE facility_id > (
        SELECT COALESCE(MAX(facility_id), 0)
        FROM facilities
        WHERE facility_name NOT IN (
                SELECT DISTINCT TRIM(spd."Fac")
                FROM SOURCE_PATIENT_DATA spd
                WHERE spd."Fac" IS NOT NULL
                    AND spd."Fac" != ''
                    AND spd."Fac" != 'zFac'
            )
    );
-- Show final facility list
SELECT facility_id,
    facility_name
FROM facilities
ORDER BY facility_id;