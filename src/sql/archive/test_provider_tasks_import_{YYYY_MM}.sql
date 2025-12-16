-- Test provider_tasks_{YYYY_MM} import mapping
SELECT patient_id,
    provider_id,
    task_date,
    minutes_of_service,
    task_description,
    notes
FROM provider_tasks_ { YYYY_MM }
ORDER BY task_date DESC
LIMIT 20;
-- Check for fallback patient_id usage
SELECT patient_id,
    COUNT(*) AS count
FROM provider_tasks_ { YYYY_MM }
WHERE patient_id LIKE '%,%'
GROUP BY patient_id
ORDER BY count DESC;
-- Check for missing provider_id
SELECT *
FROM provider_tasks_ { YYYY_MM }
WHERE provider_id IS NULL
    OR provider_id = '';
-- Check for duplicate fallback patient_id
SELECT patient_id,
    COUNT(*) AS count
FROM provider_tasks_ { YYYY_MM }
WHERE patient_id LIKE '%,%'
GROUP BY patient_id
HAVING count > 1;