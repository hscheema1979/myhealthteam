# Provider — Patient Panel

Last Updated: 2025-11-19

## Summary
How providers view patient context, recent visits, and coordinate with team actions.

## Data Sources
- Patient Panel (staging/promotion to production)
- Visits/DOS via staging_patient_visits

## Inputs Required
- None typically; use for review prior to tasks/visits

## Outputs Downstream
- Context informs correct DOS/task documentation

## Guardrails
- Ensure IDs align with normalized prefixes when cross-referencing tasks

## Troubleshooting
- Missing last visit: verify transforms ran and DOS is properly recorded in tasks

## Steps
1) Open Provider Patient Panel
2) Review recent visits and planned actions
3) Proceed to Provider Tasks or Visits & DOS section

## References
- Visits & DOS guide; billing summary guide