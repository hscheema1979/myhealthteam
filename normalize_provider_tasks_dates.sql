-- Normalize task_date column in provider_tasks table from MM/DD/YY to YYYY-MM-DD format
-- This script converts dates like "06/01/25" to "2025-06-01"

BEGIN TRANSACTION;

-- Create a backup of the original data before transformation
CREATE TEMP TABLE provider_tasks_backup AS 
SELECT provider_task_id, task_date as original_task_date 
FROM provider_tasks 
WHERE task_date IS NOT NULL;

-- Update task_date column to YYYY-MM-DD format
-- Assuming YY values 00-30 are 20XX and 31-99 are 19XX
UPDATE provider_tasks 
SET task_date = 
    CASE 
        -- Handle MM/DD/YY format where YY is 2-digit year
        WHEN task_date LIKE '__/__/__' THEN
            CASE 
                -- Years 00-30 are assumed to be 2000-2030
                WHEN CAST(substr(task_date, 7, 2) AS INTEGER) <= 30 THEN
                    '20' || substr(task_date, 7, 2) || '-' || 
                    printf('%02d', CAST(substr(task_date, 1, 2) AS INTEGER)) || '-' || 
                    printf('%02d', CAST(substr(task_date, 4, 2) AS INTEGER))
                -- Years 31-99 are assumed to be 1931-1999
                ELSE
                    '19' || substr(task_date, 7, 2) || '-' || 
                    printf('%02d', CAST(substr(task_date, 1, 2) AS INTEGER)) || '-' || 
                    printf('%02d', CAST(substr(task_date, 4, 2) AS INTEGER))
            END
        ELSE task_date  -- Keep unchanged if not MM/DD/YY format
    END
WHERE task_date IS NOT NULL AND task_date LIKE '__/__/__';

-- Verification: Show conversion summary
SELECT 'CONVERSION SUMMARY' as info;

SELECT 'Records updated:' as info, COUNT(*) as count
FROM provider_tasks 
WHERE task_date LIKE '____-__-__';

SELECT 'Sample conversions:' as info;
SELECT 
    b.original_task_date,
    p.task_date as new_task_date
FROM provider_tasks p
JOIN provider_tasks_backup b ON p.provider_task_id = b.provider_task_id
WHERE b.original_task_date != p.task_date
LIMIT 10;

-- Verify no MM/DD/YY format remains
SELECT 'Remaining MM/DD/YY format:' as info, COUNT(*) as count
FROM provider_tasks 
WHERE task_date LIKE '__/__/__';

COMMIT;

-- Final verification
SELECT 'FINAL VERIFICATION' as info;
SELECT 'Total YYYY-MM-DD format:' as info, COUNT(*) as count
FROM provider_tasks 
WHERE task_date LIKE '____-__-__';

SELECT 'Sample normalized dates:' as info;
SELECT DISTINCT task_date 
FROM provider_tasks 
WHERE task_date LIKE '____-__-__'
ORDER BY task_date 
LIMIT 10;