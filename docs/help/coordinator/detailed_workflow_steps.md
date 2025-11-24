# Coordinator — Detailed Workflow Steps

Last Updated: 2025-11-19

## Summary
Standardized step-by-step actions for common coordinator workflows to ensure consistency.

## Data Sources
- Coordinator tasks history and monthly partitions
- Patient panel (last visit, assignments)

## Inputs Required
- Task Type per step; precise notes
- Dates (activity and due) when applicable

## Outputs Downstream
- Step completion reflects in summaries and visits after transforms

## Guardrails
- Ensure DOS/activity_date captured when needed; else provider-facing alignment breaks

## Troubleshooting
- Missing steps: confirm the workflow definition and that tasks were saved

## Steps (Example: Phone Review)
1) Open patient record
2) Review recent visit and notes
3) Call patient; document outcomes
4) Set follow-up due date if needed
5) Mark task completed

## References
- Workflow definitions in docs/workflow (if available); Admin dashboard validation