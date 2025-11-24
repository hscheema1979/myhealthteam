# Coordinator — Generic Task Form

Last Updated: 2025-11-19

## Summary
How to use the generic task form to record actions consistently across workflows.

## Data Sources
- Coordinator tasks tables (staging and monthly partitions)

## Inputs Required
- Task Type (select the precise action)
- Status (In Progress/Completed)
- Notes (clear, specific)
- Due Date (for follow-ups)

## Outputs Downstream
- Aggregates into summaries; may impact patient visits over transforms

## Guardrails
- Avoid vague notes; they reduce report clarity
- Ensure status is set; incomplete tasks skew summaries

## Troubleshooting
- Task not visible: check filters and date ranges; verify saves

## Steps
1) Open Generic Task Form
2) Select Task Type
3) Enter notes and set status
4) Set due date as needed
5) Save and confirm entry

## References
- Monthly summary; staging tasks verification scripts