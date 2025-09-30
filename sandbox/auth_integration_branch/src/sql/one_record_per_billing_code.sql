-- Select one record per billing code - the one with the lowest minimum duration
-- If there are ties, pick the first one alphabetically by task_description
WITH min_duration_per_code AS (
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
    SELECT tbc.billing_code,
        tbc.task_description,
        tbc.service_type,
        tbc.min_minutes,
        tbc.max_minutes,
        tbc.rate,
        tbc.description,
        ROW_NUMBER() OVER (
            PARTITION BY tbc.billing_code
            ORDER BY tbc.task_description
        ) as rn
    FROM task_billing_codes tbc
        INNER JOIN min_duration_per_code mdpc ON tbc.billing_code = mdpc.billing_code
        AND tbc.min_minutes = mdpc.min_duration
    WHERE tbc.service_type = 'Primary Care Visit'
)
SELECT billing_code,
    task_description,
    service_type,
    min_minutes,
    max_minutes,
    rate,
    description
FROM ranked_records
WHERE rn = 1
ORDER BY billing_code;