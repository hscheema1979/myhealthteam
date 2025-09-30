-- Enhanced Coordinator Tasks Population with Differential Import
-- This script only imports NEW or CHANGED records instead of overwriting all data
-- Create temporary staging table for comparison
DROP TABLE IF EXISTS temp_new_coordinator_tasks;
CREATE TEMPORARY TABLE temp_new_coordinator_tasks (
    patient_id TEXT,
    patient_name TEXT,
    coordinator_id TEXT,
    user_id INTEGER,
    coordinator_name TEXT,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    source_hash TEXT -- Hash of key fields to detect changes
);
-- Populate staging table with transformed source data
INSERT INTO temp_new_coordinator_tasks (
        patient_id,
        patient_name,
        coordinator_id,
        user_id,
        coordinator_name,
        task_date,
        duration_minutes,
        task_type,
        notes,
        source_hash
    )
SELECT COALESCE(p.patient_id, sch."Pt Name") as patient_id,
    sch."Pt Name" as patient_name,
    COALESCE(c.coordinator_id, sch."Staff") as coordinator_id,
    scm.user_id,
    u.full_name as coordinator_name,
    -- Standardize date format during import
    CASE
        WHEN sch."Date Only" LIKE '__/__/____' THEN substr(sch."Date Only", 7, 4) || '-' || printf(
            '%02d',
            CAST(substr(sch."Date Only", 1, 2) AS INTEGER)
        ) || '-' || printf(
            '%02d',
            CAST(substr(sch."Date Only", 4, 2) AS INTEGER)
        )
        WHEN sch."Date Only" LIKE '__/__/__' THEN '20' || substr(sch."Date Only", 7, 2) || '-' || printf(
            '%02d',
            CAST(substr(sch."Date Only", 1, 2) AS INTEGER)
        ) || '-' || printf(
            '%02d',
            CAST(substr(sch."Date Only", 4, 2) AS INTEGER)
        )
        ELSE sch."Date Only"
    END as task_date,
    CAST(COALESCE(sch."Mins B", 0) AS INTEGER) as duration_minutes,
    sch."Type" as task_type,
    sch."Notes" as notes,
    -- Create hash for change detection
    hex(
        sch."Pt Name" || '|' || sch."Staff" || '|' || sch."Date Only" || '|' || COALESCE(sch."Mins B", 0) || '|' || COALESCE(sch."Type", '') || '|' || COALESCE(sch."Notes", '')
    ) as source_hash
FROM SOURCE_COORDINATOR_TASKS_HISTORY sch
    LEFT JOIN patients p ON TRIM(UPPER(sch."Pt Name")) = TRIM(UPPER(p.last_first_dob))
    LEFT JOIN staff_code_mapping scm ON LOWER(TRIM(sch."Staff")) = LOWER(TRIM(scm.staff_code))
    LEFT JOIN users u ON scm.user_id = u.user_id
    LEFT JOIN coordinators c ON u.user_id = c.user_id
WHERE sch."Pt Name" IS NOT NULL
    AND sch."Pt Name" != ''
    AND sch."Staff" IS NOT NULL
    AND sch."Staff" != ''
    AND sch."Type" != 'Place holder.  Do not change this row data'
    AND COALESCE(sch."Mins B", 0) > 0;
-- Create coordinator_tasks_archive table if it doesn't exist
CREATE TABLE IF NOT EXISTS coordinator_tasks_archive (
    coordinator_task_id INTEGER PRIMARY KEY,
    patient_id TEXT,
    patient_name TEXT,
    coordinator_id TEXT,
    user_id INTEGER,
    coordinator_name TEXT,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    source_hash TEXT,
    archived_date TEXT DEFAULT CURRENT_TIMESTAMP,
    archive_reason TEXT
);
-- Archive records that are being updated (moved to different patient, coordinator, etc.)
INSERT INTO coordinator_tasks_archive (
        coordinator_task_id,
        patient_id,
        patient_name,
        coordinator_id,
        user_id,
        coordinator_name,
        task_date,
        duration_minutes,
        task_type,
        notes,
        source_hash,
        archive_reason
    )
SELECT ct.coordinator_task_id,
    ct.patient_id,
    ct.patient_name,
    ct.coordinator_id,
    ct.user_id,
    ct.coordinator_name,
    ct.task_date,
    ct.duration_minutes,
    ct.task_type,
    ct.notes,
    ct.source_hash,
    'Updated in new import'
FROM coordinator_tasks ct
    INNER JOIN temp_new_coordinator_tasks tnct ON ct.task_date = tnct.task_date
    AND ct.patient_name = tnct.patient_name
    AND ct.coordinator_id = tnct.coordinator_id
WHERE ct.source_hash != tnct.source_hash;
-- Only archive if data changed
-- Delete existing records that have changed
DELETE FROM coordinator_tasks
WHERE coordinator_task_id IN (
        SELECT ct.coordinator_task_id
        FROM coordinator_tasks ct
            INNER JOIN temp_new_coordinator_tasks tnct ON ct.task_date = tnct.task_date
            AND ct.patient_name = tnct.patient_name
            AND ct.coordinator_id = tnct.coordinator_id
        WHERE ct.source_hash != tnct.source_hash
    );
-- Insert new records (including updated records)
INSERT INTO coordinator_tasks (
        patient_id,
        patient_name,
        coordinator_id,
        user_id,
        coordinator_name,
        task_date,
        duration_minutes,
        task_type,
        notes,
        source_hash
    )
SELECT DISTINCT tnct.patient_id,
    tnct.patient_name,
    tnct.coordinator_id,
    tnct.user_id,
    tnct.coordinator_name,
    tnct.task_date,
    tnct.duration_minutes,
    tnct.task_type,
    tnct.notes,
    tnct.source_hash
FROM temp_new_coordinator_tasks tnct
    LEFT JOIN coordinator_tasks ct ON ct.task_date = tnct.task_date
    AND ct.patient_name = tnct.patient_name
    AND ct.coordinator_id = tnct.coordinator_id
    AND ct.source_hash = tnct.source_hash
WHERE ct.coordinator_task_id IS NULL;
-- Only insert if doesn't already exist
-- Create missing patients for any unmatched "Last, First DOB" references
INSERT
    OR IGNORE INTO patients (
        last_name,
        first_name,
        date_of_birth,
        last_first_dob,
        status,
        created_date,
        updated_date,
        notes
    )
SELECT DISTINCT TRIM(
        substr(
            tnct.patient_id,
            1,
            instr(tnct.patient_id, ',') - 1
        )
    ) as last_name,
    TRIM(
        substr(
            tnct.patient_id,
            instr(tnct.patient_id, ',') + 1,
            instr(tnct.patient_id, ' ') - instr(tnct.patient_id, ',') - 1
        )
    ) as first_name,
    CASE
        WHEN tnct.patient_id LIKE '%/%/%' THEN substr(tnct.patient_id, -10, 4) || '-' || printf(
            '%02d',
            CAST(substr(tnct.patient_id, -10, 2) AS INTEGER)
        ) || '-' || printf(
            '%02d',
            CAST(substr(tnct.patient_id, -7, 2) AS INTEGER)
        )
        ELSE NULL
    END as date_of_birth,
    tnct.patient_id as last_first_dob,
    'Active' as status,
    datetime('now') as created_date,
    datetime('now') as updated_date,
    'Auto-created from coordinator tasks differential import' as notes
FROM temp_new_coordinator_tasks tnct
WHERE tnct.patient_id IS NOT NULL
    AND tnct.patient_id NOT IN (
        SELECT CAST(patient_id AS TEXT)
        FROM patients
        WHERE patient_id IS NOT NULL
    )
    AND tnct.patient_id NOT IN (
        SELECT last_first_dob
        FROM patients
        WHERE last_first_dob IS NOT NULL
    )
    AND tnct.patient_id LIKE '%,%'
    AND tnct.patient_id LIKE '%/%/%'
    AND length(tnct.patient_id) > 10;
-- Update coordinator_tasks with proper patient_id references
UPDATE coordinator_tasks
SET patient_id = (
        SELECT p.patient_id
        FROM patients p
        WHERE p.last_first_dob = coordinator_tasks.patient_id
            OR (p.first_name || ' ' || p.last_name) = coordinator_tasks.patient_name
        LIMIT 1
    )
WHERE patient_id IS NOT NULL
    AND patient_id NOT IN (
        SELECT CAST(patient_id AS TEXT)
        FROM patients
        WHERE patient_id IS NOT NULL
    );
-- Report differential import results
SELECT 'Import Summary' as section,
    (
        SELECT COUNT(*)
        FROM temp_new_coordinator_tasks
    ) as total_source_records,
    (
        SELECT COUNT(*)
        FROM coordinator_tasks
    ) as final_task_count,
    (
        SELECT COUNT(*)
        FROM coordinator_tasks_archive
        WHERE archived_date >= datetime('now', '-1 hour')
    ) as archived_records,
    (
        SELECT COUNT(*)
        FROM patients
        WHERE notes LIKE '%differential import%'
    ) as new_patients_created
UNION ALL
SELECT 'Data Quality Check' as section,
    (
        SELECT COUNT(*)
        FROM coordinator_tasks
        WHERE task_date LIKE '____-__-__'
    ) as standardized_dates,
    (
        SELECT COUNT(*)
        FROM coordinator_tasks
        WHERE patient_id IS NOT NULL
            AND EXISTS (
                SELECT 1
                FROM patients p
                WHERE p.patient_id = coordinator_tasks.patient_id
            )
    ) as linked_patients,
    (
        SELECT COUNT(DISTINCT coordinator_id)
        FROM coordinator_tasks
    ) as unique_coordinators,
    (
        SELECT COUNT(*)
        FROM coordinator_tasks
        WHERE duration_minutes > 0
    ) as tasks_with_valid_duration;
-- Clean up temporary table
DROP TABLE temp_new_coordinator_tasks;