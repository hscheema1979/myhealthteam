-- Supplementary SQL Script to Update Remaining Provider Tables
-- This script handles tables with different column structures

-- Create the temporary view for mapping
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

-- Update staging_provider_tasks (uses provider_code instead of provider_name)
UPDATE staging_provider_tasks 
SET provider_code = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = staging_provider_tasks.provider_code
)
WHERE provider_code IN (SELECT staff_code FROM staff_name_mapping);

-- Update source_provider_tasks_2025_07 (uses Prov column)
UPDATE source_provider_tasks_2025_07 
SET Prov = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = source_provider_tasks_2025_07.Prov
)
WHERE Prov IN (SELECT staff_code FROM staff_name_mapping);

-- Update source_provider_tasks_2025_08 (uses Prov column)
UPDATE source_provider_tasks_2025_08 
SET Prov = (
    SELECT snm.full_name 
    FROM staff_name_mapping snm 
    WHERE snm.staff_code = source_provider_tasks_2025_08.Prov
)
WHERE Prov IN (SELECT staff_code FROM staff_name_mapping);

-- Display summary of changes for these tables
SELECT 'Supplementary Update Summary:' as message;
SELECT 
    'Updated staging_provider_tasks provider_code field' as update_info
UNION ALL
SELECT 
    'Updated source_provider_tasks_2025_07 Prov field' as update_info
UNION ALL
SELECT 
    'Updated source_provider_tasks_2025_08 Prov field' as update_info;