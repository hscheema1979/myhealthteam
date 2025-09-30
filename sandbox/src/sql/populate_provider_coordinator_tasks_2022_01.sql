-- Repeatable: Transform provider and coordinator data for 2022_01
-- Usage: Replace {YYYY_MM} with the desired year and month (e.g., 2022_01)
-- Coordinator transformation uses SOURCE_CM_TASKS_2022_01 as source
CREATE TABLE IF NOT EXISTS coordinator_tasks_2022_01 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
DELETE FROM coordinator_tasks_2022_01;
INSERT INTO coordinator_tasks_2022_01 (
        coordinator_id,
        patient_id,
        task_date,
        duration_minutes,
        task_type,
        notes,
        source_system,
        imported_at
    )
SELECT scm.user_id AS coordinator_id,
    TRIM(REPLACE(t.[Pt Name], 'ZEN-', '')) AS patient_id,
    t.[Date Only],
    CASE
        WHEN t.[Total Mins] LIKE '%-%' THEN CAST(
            substr(t.[Total Mins], 1, instr(t.[Total Mins], '-') -1) AS INTEGER
        )
        WHEN t.[Total Mins] IS NULL
        OR TRIM(t.[Total Mins]) = '' THEN NULL
        ELSE CAST(t.[Total Mins] AS INTEGER)
    END AS duration_minutes,
    t.Type,
    t.Notes,
    'monthly_CM',
    CURRENT_TIMESTAMP
FROM SOURCE_CM_TASKS_2022_01 t
    LEFT JOIN staff_code_mapping scm ON TRIM(UPPER(t.Staff)) = TRIM(UPPER(scm.staff_code))
WHERE t.[Pt Name] IS NOT NULL
    AND TRIM(t.[Pt Name]) != ''
    AND scm.user_id IS NOT NULL;