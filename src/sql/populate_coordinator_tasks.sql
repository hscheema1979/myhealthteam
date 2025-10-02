-- Fast coordinator tasks import - recreate table approach
-- Step 1: Backup existing table
DROP TABLE IF EXISTS old_coordinator_tasks;
ALTER TABLE coordinator_tasks
    RENAME TO old_coordinator_tasks;
-- Step 2: Create new coordinator_tasks table with same structure
CREATE TABLE coordinator_tasks (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    patient_id TEXT,
    coordinator_id TEXT,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT
);
-- Step 3: Fast bulk insert - no duplicate checking needed
INSERT INTO coordinator_tasks (
        patient_id,
        coordinator_id,
        task_date,
        duration_minutes,
        task_type,
        notes
    )
-- Regular coordinator tasks from SOURCE_COORDINATOR_TASKS_HISTORY
SELECT -- Standardized patient ID normalization
    TRIM(
        REPLACE(
            REPLACE(
                REPLACE(
                    TRIM(REPLACE(sch."Pt Name", 'ZEN-', '')),
                    ', ',
                    ' '
                ),
                ',',
                ' '
            ),
            '  ',
            ' '
        )
    ) as patient_id,
    sch."Staff" as coordinator_id,
    -- Keep raw for now
    -- Standardize date format
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
    CAST(sch."Mins B" AS INTEGER) as duration_minutes,
    sch."Type" as task_type,
    sch."Notes" as notes
FROM "SOURCE_COORDINATOR_TASKS_HISTORY" sch
WHERE sch."Pt Name" IS NOT NULL
    AND sch."Pt Name" != ''
    AND sch."Staff" IS NOT NULL
    AND sch."Staff" != ''
    AND sch."Mins B" IS NOT NULL
    AND CAST(sch."Mins B" AS REAL) > 0
    AND sch."Type" != 'Place holder.  Do not change this row data'

UNION ALL

-- RVZ care management tasks from SOURCE_PROVIDER_TASKS_HISTORY
SELECT -- Standardized patient ID normalization for RVZ data
    TRIM(
        REPLACE(
            REPLACE(
                REPLACE(
                    TRIM(REPLACE(sph."Patient Last, First DOB", 'ZEN-', '')),
                    ', ',
                    ' '
                ),
                ',',
                ' '
            ),
            '  ',
            ' '
        )
    ) as patient_id,
    sph."Prov" as coordinator_id,
    -- Standardize date format for RVZ data
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
    COALESCE(CAST(sph."Minutes" AS INTEGER), 0) as duration_minutes,
    sph."Service" as task_type,
    sph."Notes" as notes
FROM "SOURCE_PROVIDER_TASKS_HISTORY" sph
WHERE sph."Prov" LIKE '%ZEN-MAL%'
    AND sph."Patient Last, First DOB" IS NOT NULL
    AND sph."Patient Last, First DOB" != ''
    AND sph."Patient Last, First DOB" != 'Aaa, Aaa'
    AND sph."Patient Last, First DOB" != 'MOUSE, MICKEY'
    AND sph."Service" IS NOT NULL
    AND sph."Service" != ''
    AND (
        sph."Service" LIKE '%CM%PHONE%REVIEW%' 
        OR sph."Service" LIKE '%cm%phone%review%'
        OR sph."Service" LIKE '%Care%Coordination%'
        OR sph."Service" LIKE '%TCM%'
    );
-- Step 4: Show results
SELECT 'Import Complete' as status,
    (
        SELECT COUNT(*)
        FROM coordinator_tasks
    ) as new_total,
    (
        SELECT COUNT(*)
        FROM old_coordinator_tasks
    ) as old_total,
    (
        SELECT COUNT(*)
        FROM SOURCE_COORDINATOR_TASKS_HISTORY
    ) as source_total;
-- ...existing code...