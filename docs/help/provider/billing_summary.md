# Provider — Billing Summary

Last Updated: 2025-11-19

## Summary
Understand how provider actions feed into billing summaries and how to validate them.

## Data Sources
- Weekly/monthly provider billing tables
- staging_provider_tasks and consolidated visits

## Inputs Required
- Accurate DOS, Task Type, notes, and status

## Outputs Downstream
- Aggregated counts and billing-ready summaries

## Guardrails
- Incomplete or incorrect status will under-report
- Validate mappings and flags (e.g., provider_paid)

## Troubleshooting
- Discrepancy in billing: review monthly summary, confirm DOS and status; check CPT mappings

## Steps
1) Open Billing Summary
2) Inspect aggregates and trends
3) Cross-check with tasks and visits

## References
- Visits & DOS; provider tasks tables; monthly billing reports