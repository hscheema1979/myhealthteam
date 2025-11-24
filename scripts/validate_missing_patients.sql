-- Check what records were filtered out during normalization
SELECT 
    ROWID as original_rowid,
    "Last",
    "First",
    "DOB",
    "LAST FIRST DOB"
FROM SOURCE_PATIENT_DATA
WHERE "Last" IS NULL OR "Last" = '' 
   OR "First" IS NULL OR "First" = '' 
   OR "DOB" IS NULL OR "DOB" = '' 
   OR "LAST FIRST DOB" IS NULL 
   OR "LAST FIRST DOB" = '' 
   OR "LAST FIRST DOB" = 'LAST FIRST DOB';

-- Also check for duplicates that might be causing issues
SELECT 
    "LAST FIRST DOB",
    COUNT(*) as count
FROM SOURCE_PATIENT_DATA
WHERE "LAST FIRST DOB" IS NOT NULL AND "LAST FIRST DOB" != '' AND "LAST FIRST DOB" != 'LAST FIRST DOB'
GROUP BY "LAST FIRST DOB"
HAVING COUNT(*) > 1;