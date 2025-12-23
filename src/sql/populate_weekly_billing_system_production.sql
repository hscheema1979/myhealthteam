-- Populate provider_task_billing_status table from existing provider_tasks data
-- This script migrates existing provider task data into the new billing system
-- This version works with the production database that has monthly provider task tables
-- First, create the billing tables if they don't exist
-- Run create_weekly_billing_system.sql first if needed
-- Insert billing records for all existing provider tasks from all monthly tables
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
        billed_date,
        billed_by,
        is_invoiced,
        invoiced_date,
        is_claim_submitted,
        claim_submitted_date,
        is_insurance_processed,
        insurance_processed_date,
        is_approved_to_pay,
        approved_to_pay_date,
        is_paid,
        paid_date,
        is_carried_over,
        original_billing_week,
        carryover_reason,
        billing_notes,
        created_date,
        updated_date
    )
SELECT pt.provider_task_id,
    pt.provider_id,
    u.full_name as provider_name,
    COALESCE(pt.patient_name, pt.patient_id) as patient_name,
    pt.task_date,
    pt.task_description,
    pt.minutes_of_service,
    COALESCE(pt.billing_code, 'Not_Billable') as billing_code,
    COALESCE(
        pt.billing_code_description,
        pt.task_description || ' - Default'
    ) as billing_code_description,
    -- Calculate billing week from task date
    strftime('%Y-%W', pt.task_date) as billing_week,
    strftime('%Y-%m-%d', pt.task_date, '-6 days', 'weekday 1') as week_start_date,
    strftime('%Y-%m-%d', pt.task_date, '+0 days', 'weekday 0') as week_end_date,
    'Pending' as billing_status,
    0 as is_billed,
    NULL as billed_date,
    NULL as billed_by,
    0 as is_invoiced,
    NULL as invoiced_date,
    0 as is_claim_submitted,
    NULL as claim_submitted_date,
    0 as is_insurance_processed,
    NULL as insurance_processed_date,
    0 as is_approved_to_pay,
    NULL as approved_to_pay_date,
    0 as is_paid,
    NULL as paid_date,
    0 as is_carried_over,
    NULL as original_billing_week,
    NULL as carryover_reason,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date
FROM provider_tasks_2025_12 pt
    LEFT JOIN users u ON pt.provider_id = u.user_id
WHERE pt.billing_code IS NOT NULL
    AND pt.billing_code != 'Not_Billable'
    AND pt.task_date IS NOT NULL
    AND pt.provider_id IS NOT NULL;
-- Create weekly summary report
INSERT INTO weekly_billing_reports (
        billing_week,
        total_tasks,
        total_billed_tasks,
        total_carried_over_tasks,
        report_status
    )
SELECT strftime('%Y-%W', pt.task_date) as billing_week,
    COUNT(*) as total_tasks,
    COUNT(
        CASE
            WHEN pt.billing_code IS NOT NULL
            AND pt.billing_code != 'Not_Billable' THEN 1
        END
    ) as total_billed_tasks,
    0 as total_carried_over_tasks,
    'Migrated' as report_status
FROM provider_tasks_2025_12 pt
WHERE pt.billing_code IS NOT NULL
    AND pt.billing_code != 'Not_Billable'
    AND pt.task_date IS NOT NULL
    AND pt.provider_id IS NOT NULL
GROUP BY strftime('%Y-%W', pt.task_date);