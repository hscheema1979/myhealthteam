-- Enhanced Provider Tasks Population with Differential Import
-- This script only imports NEW or CHANGED records instead of overwriting all data

-- Create temporary staging table for comparison
DROP TABLE IF EXISTS temp_new_provider_tasks;
CREATE TEMPORARY TABLE temp_new_provider_tasks (
    provider_id TEXT,
    provider_name TEXT,
    patient_id TEXT,
    patient_name TEXT,
    user_id INTEGER,
    task_date TEXT,
    minutes_of_service INTEGER,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_hash TEXT -- Hash of key fields to detect changes
);

-- Populate staging table with transformed source data
INSERT INTO temp_new_provider_tasks (
        provider_id,
        provider_name,
        patient_id,
        patient_name,
        user_id,
        task_date,
        minutes_of_service,
        billing_code,
        billing_code_description,
        task_description,
        source_hash
    )
SELECT COALESCE(p.provider_id, sph."Prov") as provider_id,
    u.full_name as provider_name,
    COALESCE(pat.patient_id, sph."Patient Last, First DOB") as patient_id,
    sph."Patient Last, First DOB" as patient_name,
    scm.user_id,
    -- Standardize date format during import
    CASE
        WHEN sph."DOS" LIKE '__/__/____' THEN substr(sph."DOS", 7, 4) || '-' || printf(
            '%02d',
            CAST(substr(sph."DOS", 1, 2) AS INTEGER)
        ) || '-' || printf(
            '%02d',
            CAST(substr(sph."DOS", 4, 2) AS INTEGER)
        )
        WHEN sph."DOS" LIKE '__/__/__' THEN '20' || substr(sph."DOS", 7, 2) || '-' || printf(
            '%02d',
            CAST(substr(sph."DOS", 1, 2) AS INTEGER)
        ) || '-' || printf(
            '%02d',
            CAST(substr(sph."DOS", 4, 2) AS INTEGER)
        )
        ELSE sph."DOS"
    END as task_date,
    CAST(
        CASE
            WHEN sph."Minutes" LIKE '%-%' THEN substr(sph."Minutes", 1, instr(sph."Minutes", '-') - 1)
            ELSE sph."Minutes"
        END AS INTEGER
    ) as minutes_of_service,
    sph."Coding" as billing_code,
    bc.billing_code_description,
    COALESCE(bc.service, sph."Service", 'Unknown') as task_description,
    -- Create hash for change detection
    hex(
        sph."Prov" || '|' || sph."Patient Last, First DOB" || '|' || sph."DOS" || '|' || COALESCE(sph."Minutes", '') || '|' || COALESCE(sph."Coding", '') || '|' || COALESCE(sph."Service", '')
    ) as source_hash
FROM SOURCE_PROVIDER_TASKS_HISTORY sph
    LEFT JOIN staff_code_mapping scm ON LOWER(TRIM(sph."Prov")) = LOWER(TRIM(scm.staff_code))
    LEFT JOIN providers p ON scm.user_id = p.user_id
    LEFT JOIN users u ON scm.user_id = u.user_id
    LEFT JOIN billing_codes bc ON sph."Coding" = bc.billing_code
    LEFT JOIN patients pat ON TRIM(UPPER(sph."Patient Last, First DOB")) = TRIM(UPPER(pat.last_first_dob))
WHERE sph."Prov" IS NOT NULL
    AND sph."Prov" != ''
    AND sph."Patient Last, First DOB" IS NOT NULL
    AND sph."Patient Last, First DOB" != ''
    AND sph."DOS" IS NOT NULL
    AND sph."DOS" != '';

-- Create provider_tasks_archive table if it doesn't exist
CREATE TABLE IF NOT EXISTS provider_tasks_archive (
    provider_task_id INTEGER PRIMARY KEY,
    task_id INTEGER,
    provider_id INTEGER,
    provider_name TEXT,
    patient_name TEXT,
    user_id INTEGER,
    patient_id INTEGER,
    status TEXT,
    notes TEXT,
    minutes_of_service INTEGER,
    billing_code_id INTEGER,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INTEGER,
    year INTEGER,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_hash TEXT,
    archived_date TEXT DEFAULT CURRENT_TIMESTAMP,
    archive_reason TEXT
);

-- Archive records that are being updated (moved to different patient, provider, etc.)
INSERT INTO provider_tasks_archive (
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
        source_hash,
        archive_reason
    )
SELECT pt.provider_task_id,
    pt.task_id,
    pt.provider_id,
    pt.provider_name,
    pt.patient_name,
    pt.user_id,
    pt.patient_id,
    pt.status,
    pt.notes,
    pt.minutes_of_service,
    pt.billing_code_id,
    pt.created_date,
    pt.updated_date,
    pt.task_date,
    pt.month,
    pt.year,
    pt.billing_code,
    pt.billing_code_description,
    pt.task_description,
    pt.source_hash,
    'Updated in new import'
FROM provider_tasks pt
    INNER JOIN temp_new_provider_tasks tnpt ON pt.task_date = tnpt.task_date
    AND pt.provider_id = tnpt.provider_id
    AND pt.patient_name = tnpt.patient_name
WHERE pt.source_hash != tnpt.source_hash;

-- Only archive if data changed

-- Delete existing records that have changed
DELETE FROM provider_tasks
WHERE provider_task_id IN (
        SELECT pt.provider_task_id
        FROM provider_tasks pt
            INNER JOIN temp_new_provider_tasks tnpt ON pt.task_date = tnpt.task_date
            AND pt.provider_id = tnpt.provider_id
            AND pt.patient_name = tnpt.patient_name
        WHERE pt.source_hash != tnpt.source_hash
    );

-- Insert new records (including updated records)
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
        source_hash
    )
SELECT (
        SELECT COALESCE(MAX(provider_task_id), 0) + 1
        FROM provider_tasks
    ) + ROW_NUMBER() OVER (
        ORDER BY tnpt.task_date,
        tnpt.provider_id,
        tnpt.patient_name
    ) as provider_task_id,
    NULL as task_id,
    tnpt.provider_id,
    tnpt.provider_name,
    tnpt.patient_name,
    tnpt.user_id,
    tnpt.patient_id,
    NULL as status,
    NULL as notes,
    tnpt.minutes_of_service,
    NULL as billing_code_id,
    datetime('now') as created_date,
    datetime('now') as updated_date,
    tnpt.task_date,
    CAST(strftime('%m', tnpt.task_date) AS INTEGER) as month,
    CAST(strftime('%Y', tnpt.task_date) AS INTEGER) as year,
    tnpt.billing_code,
    tnpt.billing_code_description,
    tnpt.task_description,
    tnpt.source_hash
FROM temp_new_provider_tasks tnpt
    LEFT JOIN provider_tasks pt ON pt.task_date = tnpt.task_date
    AND pt.provider_id = tnpt.provider_id
    AND pt.patient_name = tnpt.patient_name
    AND pt.source_hash = tnpt.source_hash
WHERE pt.provider_task_id IS NULL;

-- Only insert if doesn't already exist

-- Update provider_tasks with proper patient_id references
UPDATE provider_tasks
SET patient_id = (
        SELECT p.patient_id
        FROM patients p
        WHERE p.last_first_dob = provider_tasks.patient_name
        LIMIT 1
    )
WHERE patient_id IS NULL
    AND patient_name IS NOT NULL;

-- Report differential import results
SELECT 'Import Summary' as section,
    (
        SELECT COUNT(*)
        FROM temp_new_provider_tasks
    ) as total_source_records,
    (
        SELECT COUNT(*)
        FROM provider_tasks
    ) as final_task_count,
    (
        SELECT COUNT(*)
        FROM provider_tasks_archive
        WHERE archived_date >= datetime('now', '-1 hour')
    ) as archived_records
UNION ALL
SELECT 'Data Quality Check' as section,
    (
        SELECT COUNT(*)
        FROM provider_tasks
        WHERE task_date LIKE '____-__-__'
    ) as standardized_dates,
    (
        SELECT COUNT(*)
        FROM provider_tasks
        WHERE patient_id IS NOT NULL
            AND EXISTS (
                SELECT 1
                FROM patients p
                WHERE p.patient_id = provider_tasks.patient_id
            )
    ) as linked_patients,
    (
        SELECT COUNT(DISTINCT provider_id)
        FROM provider_tasks
    ) as unique_providers,
    (
        SELECT COUNT(*)
        FROM provider_tasks
        WHERE minutes_of_service > 0
    ) as tasks_with_valid_duration;

-- Clean up temporary table
DROP TABLE temp_new_provider_tasks;