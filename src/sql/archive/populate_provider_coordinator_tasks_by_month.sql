-- Repeatable: Transform provider and coordinator data for any month
-- Usage: Replace {YYYY_MM} with the desired year and month (e.g., 2025_09)
-- Provider transformation uses SOURCE_PSL_TASKS_{YYYY_MM} as source
-- Provider transformation uses SOURCE_PSL_TASKS_{YYYY_MM} as source
DROP TABLE IF EXISTS provider_tasks_ { YYYY_MM };
CREATE TABLE IF NOT EXISTS provider_tasks_ { YYYY_MM } (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
DELETE FROM provider_tasks_ { YYYY_MM };
INSERT INTO provider_tasks_ { YYYY_MM } (
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
SELECT t."1" AS provider_task_id,
    NULL AS task_id,
    scm.user_id AS provider_id,
    t.Prov AS provider_name,
    TRIM(REPLACE(t.[Patient Last, First DOB], 'ZEN-', '')) AS patient_name,
    scm.user_id AS user_id,
    REPLACE(
        TRIM(REPLACE(t.[Patient Last, First DOB], 'ZEN-', '')),
        ',',
        ''
    ) AS patient_id,
    t.Hospice AS status,
    t.Notes,
    CASE
        WHEN t.Minutes LIKE '%-%' THEN CAST(
            substr(t.Minutes, 1, instr(t.Minutes, '-') -1) AS INTEGER
        )
        WHEN t.Minutes IS NULL
        OR TRIM(t.Minutes) = '' THEN NULL
        ELSE CAST(t.Minutes AS INTEGER)
    END AS minutes_of_service,
    NULL AS billing_code_id,
    CURRENT_TIMESTAMP AS created_date,
    NULL AS updated_date,
    t.DOS,
    strftime('%m', t.DOS) AS month,
    strftime('%Y', t.DOS) AS year,
    t.Coding,
    NULL AS billing_code_description,
    t.Service,
    'monthly_PSL',
    CURRENT_TIMESTAMP
FROM SOURCE_PSL_TASKS_ { YYYY_MM } t
    LEFT JOIN staff_code_mapping scm ON TRIM(UPPER(t.Prov)) = TRIM(UPPER(scm.staff_code))
WHERE t.[Patient Last, First DOB] IS NOT NULL
    AND TRIM(t.[Patient Last, First DOB]) != ''
    AND scm.mapping_type = 'PROVIDER'
    AND scm.confidence_level != 'UNMATCHED';
-- Coordinator transformation uses SOURCE_CM_TASKS_{YYYY_MM} as source
-- Coordinator transformation uses SOURCE_CM_TASKS_{YYYY_MM} as source
DROP TABLE IF EXISTS coordinator_tasks_ { YYYY_MM };
CREATE TABLE IF NOT EXISTS coordinator_tasks_ { YYYY_MM } (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
DELETE FROM coordinator_tasks_ { YYYY_MM };
INSERT INTO coordinator_tasks_ { YYYY_MM } (
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
    REPLACE(TRIM(REPLACE(t.[Pt Name], 'ZEN-', '')), ',', '') AS patient_id,
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
FROM SOURCE_CM_TASKS_ { YYYY_MM } t
    LEFT JOIN staff_code_mapping scm ON TRIM(UPPER(t.Staff)) = TRIM(UPPER(scm.staff_code))
WHERE t.[Pt Name] IS NOT NULL
    AND TRIM(t.[Pt Name]) != ''
    AND scm.user_id IS NOT NULL;