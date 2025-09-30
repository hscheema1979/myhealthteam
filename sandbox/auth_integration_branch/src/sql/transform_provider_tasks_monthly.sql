-- transform_provider_tasks_monthly.sql
-- Usage: replace {YYYY} and {MM} with actual year and month, then .read this file in sqlite3
-- Example: to populate 2025_09 partition, run after replacing placeholders or use a small shell wrapper

INSERT INTO provider_tasks_{YYYY}_{MM} (
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
    task_description
)
SELECT
    NULL,  -- provider_task_id will be auto-generated
    s.src_rowid,  -- Using src_rowid as task_id
    s.provider_code,  -- provider_id from provider_code
    NULL,  -- provider_name (not available in staging table)
    s.patient_name_raw,  -- patient_name from patient_name_raw
    NULL,  -- user_id (not available in staging table)
    p.patient_id,  -- patient_id from patients table
    NULL,  -- status (not available in staging table)
    NULL,  -- notes (not available in staging table)
    CASE
        WHEN trim(s.minutes_raw) = '' THEN NULL
        ELSE CAST(s.minutes_raw AS INTEGER)
    END,  -- minutes_of_service from minutes_raw
    NULL,  -- billing_code_id (not available in staging table)
    NULL,  -- created_date (not available in staging table)
    NULL,  -- updated_date (not available in staging table)
    s.activity_date,  -- task_date from activity_date
    CAST(strftime('%m', s.activity_date) AS INTEGER),  -- month from activity_date
    CAST(strftime('%Y', s.activity_date) AS INTEGER),  -- year from activity_date
    s.billing_code,  -- billing_code
    NULL,  -- billing_code_description (not available in staging table)
    s.service  -- task_description from service
FROM staging_provider_tasks s
    LEFT JOIN patients p ON p.last_first_dob = s.patient_name_raw
WHERE s.activity_date >= date('{YYYY}-{MM}-01')
    AND s.activity_date < date('{YYYY}-{MM}-01', '+1 month');