-- Transform provider data from SOURCE_PROVIDER_TASKS_HISTORY to provider_tasks
DROP TABLE IF EXISTS provider_tasks;
CREATE TABLE IF NOT EXISTS provider_tasks (
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
DELETE FROM provider_tasks;
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
SELECT t."1" AS provider_task_id,
    NULL AS task_id,
    scm.user_id,
    t.Prov AS provider_name,
    TRIM(REPLACE(t.[Patient Last, First DOB], 'ZEN-', '')) AS patient_name,
    scm.user_id AS user_id,
    TRIM(REPLACE(t.[Patient Last, First DOB], 'ZEN-', '')) AS patient_id,
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
    -- Date normalization: Convert MM/DD/YY and MM/DD/YYYY formats to YYYY-MM-DD
    CASE
        WHEN t.DOS GLOB '??/??/????' THEN substr(t.DOS,7,4) || '-' || printf('%02d', CAST(substr(t.DOS,1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(t.DOS,4,2) AS INTEGER))
        WHEN t.DOS GLOB '??/??/??' THEN '20' || substr(t.DOS,7,2) || '-' || printf('%02d', CAST(substr(t.DOS,1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(t.DOS,4,2) AS INTEGER))
        ELSE t.DOS
    END AS task_date,
    CASE
        WHEN t.DOS GLOB '??/??/????' THEN CAST(substr(t.DOS,1,2) AS INTEGER)
        WHEN t.DOS GLOB '??/??/??' THEN CAST(substr(t.DOS,1,2) AS INTEGER)
        ELSE strftime('%m', t.DOS)
    END AS month,
    CASE
        WHEN t.DOS GLOB '??/??/????' THEN CAST(substr(t.DOS,7,4) AS INTEGER)
        WHEN t.DOS GLOB '??/??/??' THEN CAST('20' || substr(t.DOS,7,2) AS INTEGER)
        ELSE strftime('%Y', t.DOS)
    END AS year,
    t.Coding,
    NULL AS billing_code_description,
    t.Service,
    'monthly_PSL',
    CURRENT_TIMESTAMP
FROM SOURCE_PROVIDER_TASKS_HISTORY t
    LEFT JOIN staff_code_mapping scm ON TRIM(UPPER(t.Prov)) = TRIM(UPPER(scm.staff_code))
WHERE t.[Patient Last, First DOB] IS NOT NULL
    AND TRIM(t.[Patient Last, First DOB]) != ''
    AND scm.mapping_type = 'PROVIDER'
    AND scm.confidence_level != 'UNMATCHED';