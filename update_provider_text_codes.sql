-- SQL Script to Replace Text Codes with User Names in Provider Tasks Tables
-- This script updates provider_name fields that contain text codes with actual user names
-- from the staff_code_mapping and users tables

-- First, let's create a view to simplify the mapping
CREATE TEMPORARY VIEW staff_name_mapping AS
SELECT 
    scm.staff_code,
    u.full_name,
    u.first_name,
    u.last_name,
    scm.user_id,
    scm.confidence_level
FROM staff_code_mapping scm
JOIN users u ON scm.user_id = u.user_id
WHERE scm.confidence_level = 'HIGH';

-- Update main provider_tasks table
UPDATE provider_tasks 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

-- Update all monthly provider_tasks tables for 2024
UPDATE provider_tasks_2024_01 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_01.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_02 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_02.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_03 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_03.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_04 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_04.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_05 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_05.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_06 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_06.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_07 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_07.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_08 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_08.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_09 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_09.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_10 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_10.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_11 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_11.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2024_12 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2024_12.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

-- Update all monthly provider_tasks tables for 2025
UPDATE provider_tasks_2025_01 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_01.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_02 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_02.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_03 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_03.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_04 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_04.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_05 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_05.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_06 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_06.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_07 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_07.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_08 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_08.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_09 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_09.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_10 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_10.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_11 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_11.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_2025_12 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_2025_12.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

-- Update backup and other provider_tasks tables
UPDATE provider_tasks_backup 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_backup.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE provider_tasks_restored 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = provider_tasks_restored.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE staging_provider_tasks 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = staging_provider_tasks.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

-- Update source provider_tasks tables
UPDATE source_provider_tasks_2025_07 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = source_provider_tasks_2025_07.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

UPDATE source_provider_tasks_2025_08 
SET provider_name = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = source_provider_tasks_2025_08.provider_name
)
WHERE provider_name IN (SELECT staff_code FROM staff_name_mapping);

-- Note: Provider billing tables (provider_monthly_billing_*) use provider_id instead of text codes
-- so they don't need to be updated. They reference providers by ID, not by text code.

-- Display summary of changes
SELECT 'Update Summary:' as message;
SELECT 
    'Staff Code: ' || staff_code || ' -> User Name: ' || full_name as mapping
FROM staff_name_mapping 
ORDER BY staff_code;