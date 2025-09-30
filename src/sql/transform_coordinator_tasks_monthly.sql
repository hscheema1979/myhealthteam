-- transform_coordinator_tasks_monthly.sql
-- Usage: replace {YYYY} and {MM} with actual year and month, then .read this file in sqlite3
-- Example: to populate 2025_09 partition, run after replacing placeholders or use a small shell wrapper
INSERT INTO coordinator_tasks_{YYYY}_{MM} (
        coordinator_task_id,
        task_id,
        patient_id,
        coordinator_id,
        task_date,
        duration_minutes,
        task_type,
        notes
    )
SELECT NULL,  -- coordinator_task_id will be auto-generated
    s.src_rowid,  -- Using src_rowid as task_id
    p.patient_id,  -- patient_id from patients table
    s.staff_code,  -- coordinator_id from staff_code
    s.activity_date,  -- task_date from activity_date
    CASE
        WHEN trim(s.minutes_raw) = '' THEN NULL
        ELSE CAST(s.minutes_raw AS INTEGER)
    END,  -- duration_minutes from minutes_raw
    s.task_type,  -- task_type from task_type
    s.notes   -- notes from notes
FROM staging_coordinator_tasks s
    LEFT JOIN patients p ON p.last_first_dob = s.patient_name_raw
WHERE s.activity_date >= date('{YYYY}-{MM}-01')
    AND s.activity_date < date('{YYYY}-{MM}-01', '+1 month');