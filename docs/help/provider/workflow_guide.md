# Provider Workflow Guide

Last Updated: 2025-11-19

## Summary — What & Why
This guide explains the provider-side workflow: managing provider tasks, documenting visits, ensuring DOS is recorded correctly, and understanding how these entries drive billing summaries and patient visit updates.

## Data Sources — Where the Data Comes From
- Provider Tasks: staging_provider_tasks (history), SOURCE_PROVIDER_TASKS_HISTORY for imported raw tasks.
- Visits & DOS: activity_date is often derived from DOS; transforms consolidate into staging_patient_visits.
- Billing Summaries: staging_provider_weekly_summary and staging_provider_monthly_billing.
- Patient Panel: staging_patient_panel reflects last visit and assignments after transforms.

## Inputs — What You Must Provide
- DOS (Date of Service) — critical for accurate visit records and billing.
- Task Type — specify the clinical or administrative action.
- Notes — capture clinical details and outcomes.
- Status — mark progress accurately; completed actions feed summaries.

## Outputs — What Happens Downstream
- Visits are consolidated with canonical dates and IDs.
- Weekly/monthly billing summary aggregates counts and CPT mappings.
- Patient panel last_visit can update after transforms.

## Guardrails — Common Mistakes to Avoid
- Missing or malformed DOS: leads to incorrect activity_date and broken alignment checks.
- Patient ID prefixes (ZEN-, PM-, ZMN-): normalization applies in comparisons; ensure consistent IDs.
- Task Type/Status mismatch: incomplete or incorrect status results in under-reporting.

## Troubleshooting — How to Fix Issues
- Visit missing from summaries: verify DOS exists and transforms executed; check staging_provider_tasks for the record.
- Panel mismatch: compare IDs in staging vs raw sources; run alignment checks to see differences.
- Billing discrepancies: review monthly summary and provider_paid flags; validate CPT mappings.

## Examples — Step-by-Step
1) Open Provider Tasks and select a patient task.
2) Enter DOS accurately (YYYY-MM-DD).
3) Choose correct Task Type, add notes, set Status to “Completed”.
4) Save — transforms will aggregate into visits and billing summaries.

## Role Responsibilities
- Provider: Completes task documentation with DOS and clinical details.
- Billing Review: Consumes provider outputs for accurate billing summaries.

## References
- Staging Alignment Checks Section C (provider_name alignment refactor pending).
- Weekly/Monthly billing tables in staging for verification.