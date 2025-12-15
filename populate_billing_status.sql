-- ============================================================================
-- POPULATE provider_task_billing_status
-- ============================================================================
-- This table tracks Medicare/insurance billing workflow for provider tasks
-- It's a 1:1 mirror of provider_tasks with additional billing status flags
-- ============================================================================
DELETE FROM provider_task_billing_status;
INSERT INTO provider_task_billing_status (
        provider_task_id,
        provider_id,
        provider_name,
        patient_name,
        task_date,
        billing_week,
        week_start_date,
        week_end_date,
        task_description,
        minutes_of_service,
        billing_code,
        billing_code_description,
        billing_status,
        is_billed,
        is_invoiced,
        is_claim_submitted,
        is_insurance_processed,
        is_approved_to_pay,
        is_paid,
        is_carried_over,
        created_date
    )
SELECT pt.provider_task_id,
    pt.provider_id,
    pt.provider_name,
    pt.patient_name,
    pt.task_date,
    CAST(strftime('%W', pt.task_date) AS INTEGER) as billing_week,
    DATE(pt.task_date, 'weekday 0', '-6 days') as week_start_date,
    DATE(pt.task_date, 'weekday 0') as week_end_date,
    pt.task_description,
    pt.minutes_of_service,
    pt.billing_code,
    pt.billing_code_description,
    'Pending' as billing_status,
    FALSE as is_billed,
    FALSE as is_invoiced,
    FALSE as is_claim_submitted,
    FALSE as is_insurance_processed,
    FALSE as is_approved_to_pay,
    FALSE as is_paid,
    FALSE as is_carried_over,
    CURRENT_TIMESTAMP as created_date
FROM provider_tasks pt
WHERE pt.billing_code IS NOT NULL
    AND pt.billing_code != 'Not_Billable'
ORDER BY pt.task_date DESC,
    pt.provider_id;
-- Show summary
SELECT 'Provider billing status table populated' as status,
    COUNT(*) as total_billable_tasks,
    COUNT(DISTINCT provider_id) as unique_providers,
    MIN(task_date) as earliest_task,
    MAX(task_date) as latest_task
FROM provider_task_billing_status;