-- Create daily_provider_tasks table with all columns from task_billing_codes
-- Populate with the 5 specific records (one per billing code with lowest min_minutes)
DROP TABLE IF EXISTS daily_provider_tasks;
CREATE TABLE daily_provider_tasks AS WITH min_duration_per_code AS (
    SELECT billing_code,
        MIN(min_minutes) as min_duration
    FROM task_billing_codes
    WHERE service_type = 'Primary Care Visit'
        AND (
            billing_code = '99345'
            OR -- NEW HOME VISIT - 75min
            billing_code = '99350'
            OR -- FOLLOW UP HOME VISIT - 60min  
            billing_code = '99205'
            OR -- NEW TELEVISIT/OFFICE VISIT - 60min
            billing_code = '99024'
            OR -- NEW TELEVISIT/OFFICE VISIT - 45min
            billing_code = '99215'
            OR -- FOLLOW UP TELE/OFFICE VISIT - 45min
            billing_code = '99214'
            OR -- FOLLOW UP TELE/OFFICE VISIT - 30min
            billing_code = '99213' -- ACUTE TELEVISIT - 15min
        )
    GROUP BY billing_code
),
ranked_records AS (
    SELECT tbc.*,
        ROW_NUMBER() OVER (
            PARTITION BY tbc.billing_code
            ORDER BY tbc.task_description
        ) as rn
    FROM task_billing_codes tbc
        INNER JOIN min_duration_per_code mdpc ON tbc.billing_code = mdpc.billing_code
        AND tbc.min_minutes = mdpc.min_duration
    WHERE tbc.service_type = 'Primary Care Visit'
)
SELECT code_id,
    task_description,
    service_type,
    location_type,
    patient_type,
    min_minutes,
    max_minutes,
    billing_code,
    description,
    rate,
    effective_date,
    expiration_date,
    datetime('now') as created_date
FROM ranked_records
WHERE rn = 1
ORDER BY billing_code;
-- Add an enabled column for future use
ALTER TABLE daily_provider_tasks
ADD COLUMN enabled BOOLEAN DEFAULT 1;
-- Show the results
SELECT *
FROM daily_provider_tasks
ORDER BY billing_code;
-- Show count
SELECT 'Total daily provider tasks created' as description,
    COUNT(*) as count
FROM daily_provider_tasks;