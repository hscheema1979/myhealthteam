-- Query task_billing_codes for specific billing codes using explicit OR conditions
-- WHERE service_type = 'Primary Care Visit' AND explicit billing code matches
SELECT billing_code,
    task_description,
    service_type,
    min_minutes,
    max_minutes,
    rate,
    description
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
        OR -- NEW TELEVISIT/OFFICE VISIT - 45min (not found)
        billing_code = '99215'
        OR -- FOLLOW UP TELE/OFFICE VISIT - 45min
        billing_code = '99214'
        OR -- FOLLOW UP TELE/OFFICE VISIT - 30min
        billing_code = '99213' -- ACUTE TELEVISIT - 15min
    )
ORDER BY billing_code,
    task_description;
-- Count by billing code
SELECT billing_code,
    COUNT(*) as record_count
FROM task_billing_codes
WHERE service_type = 'Primary Care Visit'
    AND (
        billing_code = '99345'
        OR billing_code = '99350'
        OR billing_code = '99205'
        OR billing_code = '99024'
        OR billing_code = '99215'
        OR billing_code = '99214'
        OR billing_code = '99213'
    )
GROUP BY billing_code
ORDER BY billing_code;