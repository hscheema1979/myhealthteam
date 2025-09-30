-- Populate provider weekly summary for week 35 (Sept 1-7, 2025)
-- This creates the weekly tasks summary per provider
DELETE FROM provider_weekly_summary_2025_35;
INSERT INTO provider_weekly_summary_2025_35 (
        provider_id,
        provider_name,
        week_start_date,
        week_end_date,
        year,
        week_number,
        total_tasks_completed,
        billing_code,
        billing_code_description
    )
SELECT pt.provider_id,
    COALESCE(pt.provider_name, 'Unknown') as provider_name,
    '2025-09-01' as week_start_date,
    '2025-09-07' as week_end_date,
    2025 as year,
    35 as week_number,
    COUNT(pt.provider_task_id) as total_tasks_completed,
    CASE
        WHEN COUNT(pt.provider_task_id) <= 5 THEN '99201'
        WHEN COUNT(pt.provider_task_id) <= 10 THEN '99202'
        WHEN COUNT(pt.provider_task_id) <= 15 THEN '99203'
        ELSE '99204'
    END as billing_code,
    CASE
        WHEN COUNT(pt.provider_task_id) <= 5 THEN 'Office visit, minimal'
        WHEN COUNT(pt.provider_task_id) <= 10 THEN 'Office visit, straightforward'
        WHEN COUNT(pt.provider_task_id) <= 15 THEN 'Office visit, low complexity'
        ELSE 'Office visit, moderate complexity'
    END as billing_code_description
FROM provider_tasks_2025_09 pt
WHERE pt.task_date BETWEEN '2025-09-01' AND '2025-09-07'
GROUP BY pt.provider_id,
    pt.provider_name
ORDER BY pt.provider_id;