-- Patient Region and Facility Mapping Script
-- Update patients table with region_id and current_facility_id based on SOURCE_PATIENT_DATA
-- First, create any missing facilities before mapping
-- (This should be run after create_missing_facilities.sql)
-- Show current mapping status before updates
SELECT 'Before Update - Patients with Regions:' as info,
    COUNT(region_id) || ' / ' || COUNT(*) || ' patients have region_id' as status
FROM patients;
SELECT 'Before Update - Patients with Facilities:' as info,
    COUNT(current_facility_id) || ' / ' || COUNT(*) || ' patients have facility_id' as status
FROM patients;
-- Show what regions we need to map
SELECT DISTINCT LOWER(TRIM(spd."Region")) as region_name,
    COUNT(*) as patient_count
FROM SOURCE_PATIENT_DATA spd
WHERE spd."Region" IS NOT NULL
    AND spd."Region" != ''
    AND spd."Region" != 'zRegion'
GROUP BY LOWER(TRIM(spd."Region"))
ORDER BY patient_count DESC;
-- Show what facilities we need to map
SELECT DISTINCT LOWER(TRIM(spd."Fac")) as facility_name,
    COUNT(*) as patient_count
FROM SOURCE_PATIENT_DATA spd
WHERE spd."Fac" IS NOT NULL
    AND spd."Fac" != ''
    AND spd."Fac" != 'zFac'
GROUP BY LOWER(TRIM(spd."Fac"))
ORDER BY patient_count DESC;
-- Update patients with region_id based on region name matching
UPDATE patients
SET region_id = (
        SELECT r.region_id
        FROM regions r
            JOIN SOURCE_PATIENT_DATA spd ON patients.last_first_dob = spd."LAST FIRST DOB"
        WHERE LOWER(TRIM(r.region_name)) = LOWER(TRIM(spd."Region"))
        LIMIT 1
    )
WHERE EXISTS (
        SELECT 1
        FROM SOURCE_PATIENT_DATA spd
        WHERE patients.last_first_dob = spd."LAST FIRST DOB"
            AND spd."Region" IS NOT NULL
            AND spd."Region" != ''
            AND spd."Region" != 'zRegion'
    );
-- Update patients with facility_id based on facility name matching
-- Note: This assumes facilities table exists and has facility_name field
UPDATE patients
SET current_facility_id = (
        SELECT f.facility_id
        FROM facilities f
            JOIN SOURCE_PATIENT_DATA spd ON patients.last_first_dob = spd."LAST FIRST DOB"
        WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac"))
        LIMIT 1
    )
WHERE EXISTS (
        SELECT 1
        FROM SOURCE_PATIENT_DATA spd
        WHERE patients.last_first_dob = spd."LAST FIRST DOB"
            AND spd."Fac" IS NOT NULL
            AND spd."Fac" != ''
            AND spd."Fac" != 'zFac'
    );
-- Show mapping results
SELECT COUNT(*) as total_patients,
    COUNT(region_id) as patients_with_region,
    COUNT(current_facility_id) as patients_with_facility,
    ROUND(COUNT(region_id) * 100.0 / COUNT(*), 2) as region_mapping_percentage,
    ROUND(COUNT(current_facility_id) * 100.0 / COUNT(*), 2) as facility_mapping_percentage
FROM patients;
-- Show unmapped regions
SELECT 'Unmapped Regions' as category,
    DISTINCT TRIM(spd."Region") as name
FROM SOURCE_PATIENT_DATA spd
WHERE spd."Region" IS NOT NULL
    AND spd."Region" != ''
    AND spd."Region" != 'zRegion'
    AND NOT EXISTS (
        SELECT 1
        FROM regions r
        WHERE LOWER(TRIM(r.region_name)) = LOWER(TRIM(spd."Region"))
    )
UNION ALL
-- Show unmapped facilities
SELECT 'Unmapped Facilities' as category,
    DISTINCT TRIM(spd."Fac") as name
FROM SOURCE_PATIENT_DATA spd
WHERE spd."Fac" IS NOT NULL
    AND spd."Fac" != ''
    AND spd."Fac" != 'zFac'
    AND NOT EXISTS (
        SELECT 1
        FROM facilities f
        WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac"))
    );