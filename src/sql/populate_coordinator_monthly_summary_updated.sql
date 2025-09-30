-- Updated coordinator monthly summary population using new monthly tables
-- This script aggregates data from coordinator_tasks_2025_XX tables
-- Clear existing data
DELETE FROM coordinator_monthly_summary;
-- Insert data from all monthly tables (UNION ALL to combine all months)
INSERT INTO coordinator_monthly_summary (
        coordinator_id,
        coordinator_name,
        patient_id,
        patient_name,
        year,
        month,
        total_minutes,
        billing_code_id,
        billing_code,
        billing_code_description
    )
SELECT COALESCE(
        scm.user_id,
        CAST(monthly_summary.coordinator_id AS INTEGER)
    ) as coordinator_id,
    COALESCE(
        u.first_name || ' ' || u.last_name,
        monthly_summary.coordinator_id
    ) as coordinator_name,
    COALESCE(p.patient_id, monthly_summary.patient_id) as patient_id,
    COALESCE(
        p.first_name || ' ' || p.last_name,
        p.last_first_dob,
        monthly_summary.patient_id
    ) as patient_name,
    monthly_summary.year,
    monthly_summary.month,
    monthly_summary.total_minutes,
    bc.code_id as billing_code_id,
    bc.billing_code,
    bc.description as billing_code_description
FROM (
        -- April 2025 data
        SELECT monthly_tasks.coordinator_id,
            monthly_tasks.patient_id,
            2025 as year,
            4 as month,
            SUM(monthly_tasks.duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_04 monthly_tasks
        WHERE monthly_tasks.coordinator_id IS NOT NULL
            AND monthly_tasks.patient_id IS NOT NULL
            AND monthly_tasks.duration_minutes IS NOT NULL
            AND monthly_tasks.duration_minutes > 0
        GROUP BY monthly_tasks.coordinator_id,
            monthly_tasks.patient_id
        UNION ALL
        -- May 2025 data  
        SELECT monthly_tasks.coordinator_id,
            monthly_tasks.patient_id,
            2025 as year,
            5 as month,
            SUM(monthly_tasks.duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_05 monthly_tasks
        WHERE monthly_tasks.coordinator_id IS NOT NULL
            AND monthly_tasks.patient_id IS NOT NULL
            AND monthly_tasks.duration_minutes IS NOT NULL
            AND monthly_tasks.duration_minutes > 0
        GROUP BY monthly_tasks.coordinator_id,
            monthly_tasks.patient_id
        UNION ALL
        -- June 2025 data
        SELECT monthly_tasks.coordinator_id,
            monthly_tasks.patient_id,
            2025 as year,
            6 as month,
            SUM(monthly_tasks.duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_06 monthly_tasks
        WHERE monthly_tasks.coordinator_id IS NOT NULL
            AND monthly_tasks.patient_id IS NOT NULL
            AND monthly_tasks.duration_minutes IS NOT NULL
            AND monthly_tasks.duration_minutes > 0
        GROUP BY monthly_tasks.coordinator_id,
            monthly_tasks.patient_id
        UNION ALL
        -- July 2025 data
        SELECT monthly_tasks.coordinator_id,
            monthly_tasks.patient_id,
            2025 as year,
            7 as month,
            SUM(monthly_tasks.duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_07 monthly_tasks
        WHERE monthly_tasks.coordinator_id IS NOT NULL
            AND monthly_tasks.patient_id IS NOT NULL
            AND monthly_tasks.duration_minutes IS NOT NULL
            AND monthly_tasks.duration_minutes > 0
        GROUP BY monthly_tasks.coordinator_id,
            monthly_tasks.patient_id
    ) monthly_summary -- Join to get user_id from staff codes
    LEFT JOIN staff_code_mapping scm ON monthly_summary.coordinator_id = scm.staff_code
    LEFT JOIN users u ON COALESCE(
        scm.user_id,
        CAST(monthly_summary.coordinator_id AS INTEGER)
    ) = u.user_id
    LEFT JOIN patients p ON (
        CAST(monthly_summary.patient_id AS INTEGER) = p.patient_id
        OR p.last_first_dob = monthly_summary.patient_id
    )
    LEFT JOIN coordinator_billing_codes bc ON monthly_summary.total_minutes >= bc.min_minutes
    AND monthly_summary.total_minutes <= bc.max_minutes
WHERE COALESCE(
        scm.user_id,
        CAST(monthly_summary.coordinator_id AS INTEGER)
    ) IS NOT NULL
ORDER BY monthly_summary.year DESC,
    monthly_summary.month DESC,
    COALESCE(
        scm.user_id,
        CAST(monthly_summary.coordinator_id AS INTEGER)
    );
-- Show results
SELECT 'Summary populated' as status,
    COUNT(*) as records_inserted
FROM coordinator_monthly_summary;