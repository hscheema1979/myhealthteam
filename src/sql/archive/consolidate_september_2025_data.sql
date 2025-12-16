-- Consolidate September 2025 data from provider_tasks_2025_09 into main provider_tasks table
-- This script addresses the missing September data in the weekly billing dashboard

BEGIN TRANSACTION;

-- First, check if September data already exists in main table to avoid duplicates
SELECT 'Checking existing September data in main provider_tasks table...' as status;

SELECT 
    COUNT(*) as existing_september_records,
    COUNT(DISTINCT provider_name) as existing_september_providers
FROM provider_tasks 
WHERE strftime('%Y-%m', task_date) = '2025-09';

-- Insert September 2025 data from monthly table into main provider_tasks table
INSERT INTO provider_tasks (
    provider_task_id,
    task_id,
    provider_id,
    provider_name,
    patient_name,
    user_id,
    patient_id,
    status,
    notes,
    minutes_of_service,
    billing_code_id,
    created_date,
    updated_date,
    task_date,
    month,
    year,
    billing_code,
    billing_code_description,
    task_description,
    source_system,
    imported_at
)
SELECT 
    provider_task_id,
    task_id,
    provider_id,
    provider_name,
    patient_name,
    user_id,
    patient_id,
    status,
    notes,
    minutes_of_service,
    billing_code_id,
    created_date,
    updated_date,
    task_date,
    month,
    year,
    billing_code,
    billing_code_description,
    task_description,
    source_system,
    imported_at
FROM provider_tasks_2025_09
WHERE provider_task_id NOT IN (
    SELECT provider_task_id 
    FROM provider_tasks 
    WHERE provider_task_id IS NOT NULL
);

-- Verify the consolidation
SELECT 'Consolidation completed. Verification:' as status;

SELECT 
    COUNT(*) as total_september_records,
    COUNT(DISTINCT provider_name) as total_september_providers,
    MIN(task_date) as earliest_date,
    MAX(task_date) as latest_date
FROM provider_tasks 
WHERE strftime('%Y-%m', task_date) = '2025-09';

-- Show provider breakdown for September
SELECT 
    provider_name,
    COUNT(*) as task_count,
    MIN(task_date) as first_task,
    MAX(task_date) as last_task
FROM provider_tasks 
WHERE strftime('%Y-%m', task_date) = '2025-09'
GROUP BY provider_name
ORDER BY task_count DESC;

-- Update the latest data summary
SELECT 'Updated data range in main provider_tasks table:' as status;

SELECT 
    MIN(task_date) as earliest_date,
    MAX(task_date) as latest_date,
    COUNT(DISTINCT strftime('%Y-%m', task_date)) as total_months,
    COUNT(DISTINCT provider_name) as total_providers
FROM provider_tasks;

COMMIT;