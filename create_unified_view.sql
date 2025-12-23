-- Create Unified Tasks View
-- This view combines coordinator_tasks and provider_tasks into a single unified view
-- with standardized column names and a type indicator

DROP VIEW IF EXISTS unified_tasks;

CREATE VIEW unified_tasks AS
-- Coordinator tasks
SELECT
    'coordinator' AS task_type,
    coordinator_task_id AS task_id,
    coordinator_id AS staff_id,
    coordinator_name AS staff_name,
    patient_id,
    NULL AS patient_name,  -- coordinator_tasks doesn't have patient_name
    task_date,
    duration_minutes AS minutes,
    task_type AS activity_type,  -- Rename to avoid confusion with task_type column
    notes,
    NULL AS task_description,  -- coordinator_tasks doesn't have task_description
    NULL AS billing_code,
    NULL AS billing_code_description,
    source_system,
    imported_at,
    NULL AS status,  -- coordinator_tasks doesn't have status
    NULL AS is_deleted,  -- coordinator_tasks doesn't have is_deleted
    NULL AS provider_paid,  -- coordinator_tasks doesn't have provider_paid
    NULL AS provider_paid_date  -- coordinator_tasks doesn't have provider_paid_date
FROM coordinator_tasks

UNION ALL

-- Provider tasks
SELECT
    'provider' AS task_type,
    provider_task_id AS task_id,
    provider_id AS staff_id,
    provider_name AS staff_name,
    patient_id,
    patient_name,
    task_date,
    minutes_of_service AS minutes,
    NULL AS activity_type,  -- provider_tasks doesn't have task_type
    notes,
    task_description,
    billing_code,
    billing_code_description,
    source_system,
    imported_at,
    status,
    is_deleted,
    provider_paid,
    provider_paid_date
FROM provider_tasks;

-- Add facility information view
DROP VIEW IF EXISTS unified_tasks_with_facilities;

CREATE VIEW unified_tasks_with_facilities AS
SELECT
    ut.*,
    p.current_facility_id,
    f.facility_name
FROM unified_tasks ut
LEFT JOIN patients p ON ut.patient_id = p.patient_id
LEFT JOIN facilities f ON p.current_facility_id = f.facility_id;

-- Create summary tables for common metrics

-- Minutes per staff per month per facility
DROP VIEW IF EXISTS minutes_per_staff_per_month_per_facility;

CREATE VIEW minutes_per_staff_per_month_per_facility AS
SELECT
    COALESCE(facility_name, 'Unknown Facility') AS facility_name,
    staff_name,
    task_type,
    strftime('%Y-%m', task_date) AS month,
    SUM(minutes) AS total_minutes,
    COUNT(*) AS task_count,
    COUNT(DISTINCT patient_id) AS unique_patients,
    ROUND(AVG(minutes), 2) AS avg_minutes_per_task
FROM unified_tasks_with_facilities
WHERE task_date >= date('now', '-24 months')  -- Last 2 years
GROUP BY facility_name, staff_name, task_type, month
ORDER BY facility_name, staff_name, month DESC;

-- Tasks per month per facility
DROP VIEW IF EXISTS tasks_per_month_per_facility;

CREATE VIEW tasks_per_month_per_facility AS
SELECT
    COALESCE(facility_name, 'Unknown Facility') AS facility_name,
    task_type,
    strftime('%Y-%m', task_date) AS month,
    COUNT(*) AS task_count,
    SUM(minutes) AS total_minutes,
    COUNT(DISTINCT staff_name) AS unique_staff,
    COUNT(DISTINCT patient_id) AS unique_patients
FROM unified_tasks_with_facilities
WHERE task_date >= date('now', '-24 months')
GROUP BY facility_name, task_type, month
ORDER BY facility_name, month DESC, task_type;

-- Staff performance summary
DROP VIEW IF EXISTS staff_performance_summary;

CREATE VIEW staff_performance_summary AS
SELECT
    staff_name,
    task_type,
    COUNT(*) AS total_tasks,
    SUM(minutes) AS total_minutes,
    ROUND(AVG(minutes), 2) AS avg_minutes_per_task,
    COUNT(DISTINCT patient_id) AS unique_patients,
    COUNT(DISTINCT strftime('%Y-%m', task_date)) AS active_months,
    MIN(task_date) AS first_task_date,
    MAX(task_date) AS last_task_date,
    -- For coordinators: most common activity_type
    CASE
        WHEN task_type = 'coordinator' THEN (
            SELECT activity_type
            FROM unified_tasks ut2
            WHERE ut2.staff_name = ut.staff_name
              AND ut2.task_type = ut.task_type
              AND ut2.activity_type IS NOT NULL
            GROUP BY activity_type
            ORDER BY COUNT(*) DESC
            LIMIT 1
        )
        ELSE NULL
    END AS most_common_activity_type,
    -- For providers: most common billing_code
    CASE
        WHEN task_type = 'provider' THEN (
            SELECT billing_code
            FROM unified_tasks ut2
            WHERE ut2.staff_name = ut.staff_name
              AND ut2.task_type = ut.task_type
              AND ut2.billing_code IS NOT NULL
            GROUP BY billing_code
            ORDER BY COUNT(*) DESC
            LIMIT 1
        )
        ELSE NULL
    END AS most_common_billing_code
FROM unified_tasks ut
WHERE task_date >= date('now', '-24 months')
GROUP BY staff_name, task_type
ORDER BY total_minutes DESC;

-- Facility summary
DROP VIEW IF EXISTS facility_summary;

CREATE VIEW facility_summary AS
SELECT
    COALESCE(facility_name, 'Unknown Facility') AS facility_name,
    COUNT(*) AS total_tasks,
    SUM(minutes) AS total_minutes,
    ROUND(AVG(minutes), 2) AS avg_minutes_per_task,
    COUNT(DISTINCT patient_id) AS unique_patients,
    COUNT(DISTINCT CASE WHEN task_type = 'coordinator' THEN staff_name END) AS coordinator_count,
    COUNT(DISTINCT CASE WHEN task_type = 'provider' THEN staff_name END) AS provider_count,
    SUM(CASE WHEN task_type = 'coordinator' THEN minutes ELSE 0 END) AS coordinator_minutes,
    SUM(CASE WHEN task_type = 'provider' THEN minutes ELSE 0 END) AS provider_minutes,
    COUNT(CASE WHEN task_type = 'coordinator' THEN 1 END) AS coordinator_tasks,
    COUNT(CASE WHEN task_type = 'provider' THEN 1 END) AS provider_tasks
FROM unified_tasks_with_facilities
WHERE task_date >= date('now', '-24 months')
GROUP BY facility_name
ORDER BY total_minutes DESC;

-- Monthly trends
DROP VIEW IF EXISTS monthly_trends;

CREATE VIEW monthly_trends AS
SELECT
    strftime('%Y-%m', task_date) AS month,
    task_type,
    COUNT(*) AS task_count,
    SUM(minutes) AS total_minutes,
    COUNT(DISTINCT staff_name) AS unique_staff,
    COUNT(DISTINCT patient_id) AS unique_patients
FROM unified_tasks
WHERE task_date >= date('now', '-24 months')
GROUP BY month, task_type
ORDER BY month DESC, task_type;

-- Print confirmation
SELECT 'Created unified_tasks view with ' || COUNT(*) || ' total tasks' AS message
FROM unified_tasks;

SELECT 'Created unified_tasks_with_facilities view' AS message;

SELECT 'Created 5 summary views:' AS message;
SELECT '1. minutes_per_staff_per_month_per_facility' AS view_name;
SELECT '2. tasks_per_month_per_facility' AS view_name;
SELECT '3. staff_performance_summary' AS view_name;
SELECT '4. facility_summary' AS view_name;
SELECT '5. monthly_trends' AS view_name;

-- Example queries for common use cases:
/*
-- 1. All tasks for a specific coordinator
SELECT * FROM unified_tasks_with_facilities
WHERE task_type = 'coordinator'
  AND staff_name = 'Szalas NP, Andrew'
ORDER BY task_date DESC;

-- 2. Minutes per coordinator per month, per facility (your original request)
SELECT * FROM minutes_per_staff_per_month_per_facility
WHERE task_type = 'coordinator'
ORDER BY facility_name, staff_name, month DESC;

-- 3. Tasks per provider per month, per facility (your original request)
SELECT * FROM minutes_per_staff_per_month_per_facility
WHERE task_type = 'provider'
ORDER BY facility_name, staff_name, month DESC;

-- 4. General minutes per month per facility
SELECT
    facility_name,
    month,
    SUM(total_minutes) AS total_minutes,
    SUM(task_count) AS total_tasks
FROM tasks_per_month_per_facility
GROUP BY facility_name, month
ORDER BY facility_name, month DESC;

-- 5. Tasks per month per facility
SELECT * FROM tasks_per_month_per_facility
ORDER BY facility_name, month DESC;
*/
