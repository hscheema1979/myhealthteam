# Provider — Visits & DOS

Last Updated: 2025-11-19

## Summary
How dates of service (DOS) drive visit records and summaries.

## Data Sources
- staging_patient_visits (consolidated visits)
- staging_provider_tasks (input tasks with DOS)

## Inputs Required
- DOS and task details

## Outputs Downstream
- Patient visit consolidation and billing summaries

## Guardrails
- DOS must be present and correctly formatted (YYYY-MM-DD)

## Troubleshooting
- Visit missing: confirm DOS on the task; check transforms executed

## Steps
1) Open Visits & DOS
2) Review tasks and their DOS
3) Confirm visit consolidation in reports

## References
- Billing Summary; alignment checks