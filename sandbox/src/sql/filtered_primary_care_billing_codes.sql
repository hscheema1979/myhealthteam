-- Query task_billing_codes for specific billing codes where service_type = 'Primary Care Visit'
-- Organized by the categories you specified
-- NEW HOME VISIT - 75min (99345)
SELECT 'NEW HOME VISIT - 75min (99345)' as category,
    billing_code,
    task_description,
    min_minutes,
    max_minutes,
    rate
FROM task_billing_codes
WHERE service_type = 'Primary Care Visit'
    AND billing_code = '99345'
UNION ALL
-- FOLLOW UP HOME VISIT - 60min (99350)  
SELECT 'FOLLOW UP HOME VISIT - 60min (99350)' as category,
    billing_code,
    task_description,
    min_minutes,
    max_minutes,
    rate
FROM task_billing_codes
WHERE service_type = 'Primary Care Visit'
    AND billing_code = '99350'
UNION ALL
-- NEW TELEVISIT/OFFICE VISIT - 60min (99205)
SELECT 'NEW TELEVISIT/OFFICE VISIT - 60min (99205)' as category,
    billing_code,
    task_description,
    min_minutes,
    max_minutes,
    rate
FROM task_billing_codes
WHERE service_type = 'Primary Care Visit'
    AND billing_code = '99205'
UNION ALL
-- NEW TELEVISIT/OFFICE VISIT - 45min (99024) - Not found in database
SELECT 'NEW TELEVISIT/OFFICE VISIT - 45min (99024) - NOT FOUND' as category,
    '99024' as billing_code,
    'NOT IN DATABASE' as task_description,
    0 as min_minutes,
    0 as max_minutes,
    0 as rate
UNION ALL
-- FOLLOW UP TELE/OFFICE VISIT - 45min (99215)
SELECT 'FOLLOW UP TELE/OFFICE VISIT - 45min (99215)' as category,
    billing_code,
    task_description,
    min_minutes,
    max_minutes,
    rate
FROM task_billing_codes
WHERE service_type = 'Primary Care Visit'
    AND billing_code = '99215'
UNION ALL
-- FOLLOW UP TELE/OFFICE VISIT - 30min (99214)
SELECT 'FOLLOW UP TELE/OFFICE VISIT - 30min (99214)' as category,
    billing_code,
    task_description,
    min_minutes,
    max_minutes,
    rate
FROM task_billing_codes
WHERE service_type = 'Primary Care Visit'
    AND billing_code = '99214'
UNION ALL
-- ACUTE TELEVISIT - 15min (99213)
SELECT 'ACUTE TELEVISIT - 15min (99213)' as category,
    billing_code,
    task_description,
    min_minutes,
    max_minutes,
    rate
FROM task_billing_codes
WHERE service_type = 'Primary Care Visit'
    AND billing_code = '99213'
ORDER BY category,
    task_description,
    min_minutes;