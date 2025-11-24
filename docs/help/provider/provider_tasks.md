# Provider — Provider Tasks

Last Updated: 2025-11-19

## Summary
Document provider actions and ensure DOS is captured correctly for downstream billing and visit consolidation.

## Data Sources
- staging_provider_tasks; SOURCE_PROVIDER_TASKS_HISTORY

## Inputs Required
- DOS (Date of Service)
- Task Type
- Notes
- Status

## Outputs Downstream
- Visits consolidated in staging_patient_visits
- Billing summaries in weekly/monthly tables

## Guardrails
- Missing DOS breaks visit alignment and billing accuracy
- Normalize IDs (ZEN-, PM-, ZMN-) when cross-referencing

## Troubleshooting
- Task missing from summary: verify DOS and status; ensure transforms ran

## Steps
1) Open Provider Tasks
2) Enter DOS accurately
3) Select Task Type and add notes
4) Set status to Completed when done

## References
- Visits & DOS; Billing Summary