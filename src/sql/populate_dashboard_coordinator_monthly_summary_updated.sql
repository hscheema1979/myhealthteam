-- Updated dashboard coordinator monthly summary using new monthly tables
-- This creates aggregated metrics for the dashboard performance components
-- Clear existing data
DELETE FROM dashboard_coordinator_monthly_summary;
-- Insert aggregated data from monthly tables
INSERT INTO dashboard_coordinator_monthly_summary (
        coordinator_id,
        month,
        year,
        total_minutes,
        total_minutes_per_patient,
        total_tasks_completed,
        average_daily_tasks
    )
SELECT COALESCE(
        scm.user_id,
        CAST(coordinator_summary.coordinator_id AS INTEGER)
    ) as coordinator_id,
    coordinator_summary.month,
    coordinator_summary.year,
    coordinator_summary.total_minutes,
    CASE
        WHEN coordinator_summary.unique_patients > 0 THEN coordinator_summary.total_minutes * 1.0 / coordinator_summary.unique_patients
        ELSE 0
    END as total_minutes_per_patient,
    coordinator_summary.total_tasks as total_tasks_completed,
    coordinator_summary.total_tasks * 1.0 / 30.0 as average_daily_tasks
FROM (
        -- April 2025 aggregated data
        SELECT coordinator_id,
            4 as month,
            2025 as year,
            SUM(duration_minutes) as total_minutes,
            COUNT(DISTINCT patient_id) as unique_patients,
            COUNT(*) as total_tasks
        FROM coordinator_tasks_2025_04
        WHERE coordinator_id IS NOT NULL
            AND patient_id IS NOT NULL
            AND duration_minutes IS NOT NULL
            AND duration_minutes > 0
        GROUP BY coordinator_id
        UNION ALL
        -- May 2025 aggregated data
        SELECT coordinator_id,
            5 as month,
            2025 as year,
            SUM(duration_minutes) as total_minutes,
            COUNT(DISTINCT patient_id) as unique_patients,
            COUNT(*) as total_tasks
        FROM coordinator_tasks_2025_05
        WHERE coordinator_id IS NOT NULL
            AND patient_id IS NOT NULL
            AND duration_minutes IS NOT NULL
            AND duration_minutes > 0
        GROUP BY coordinator_id
        UNION ALL
        -- June 2025 aggregated data
        SELECT coordinator_id,
            6 as month,
            2025 as year,
            SUM(duration_minutes) as total_minutes,
            COUNT(DISTINCT patient_id) as unique_patients,
            COUNT(*) as total_tasks
        FROM coordinator_tasks_2025_06
        WHERE coordinator_id IS NOT NULL
            AND patient_id IS NOT NULL
            AND duration_minutes IS NOT NULL
            AND duration_minutes > 0
        GROUP BY coordinator_id
        UNION ALL
        -- July 2025 aggregated data
        SELECT coordinator_id,
            7 as month,
            2025 as year,
            SUM(duration_minutes) as total_minutes,
            COUNT(DISTINCT patient_id) as unique_patients,
            COUNT(*) as total_tasks
        FROM coordinator_tasks_2025_07
        WHERE coordinator_id IS NOT NULL
            AND patient_id IS NOT NULL
            AND duration_minutes IS NOT NULL
            AND duration_minutes > 0
        GROUP BY coordinator_id
    ) coordinator_summary
    LEFT JOIN staff_code_mapping scm ON coordinator_summary.coordinator_id = scm.staff_code
WHERE COALESCE(
        scm.user_id,
        CAST(coordinator_summary.coordinator_id AS INTEGER)
    ) IS NOT NULL
ORDER BY coordinator_summary.year DESC,
    coordinator_summary.month DESC,
    COALESCE(
        scm.user_id,
        CAST(coordinator_summary.coordinator_id AS INTEGER)
    );
-- Show results
SELECT 'Dashboard summary populated' as status,
    COUNT(*) as records_inserted
FROM dashboard_coordinator_monthly_summary;