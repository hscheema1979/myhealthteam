# Coordinator — Ongoing Workflows

Last Updated: 2025-11-19

## Summary
Track and progress ongoing workflows for patients, ensuring follow-ups and actions are captured.

## Data Sources
- Coordinator tasks: staging_coordinator_tasks; monthly partitions for summaries
- Patient panel and last visit aggregation via transforms

## Inputs Required
- Task Type (e.g., Follow-up, Scheduling)
- Status (In Progress/Completed)
- Notes and due dates

## Outputs Downstream
- Workflow stage advances; minutes aggregate
- Monthly summaries reflect workload and outcomes

## Guardrails
- Don’t leave tasks without status; summaries degrade
- Keep IDs consistent with normalized prefixes (ZEN-, PM-, ZMN-)

## Troubleshooting
- Tasks not showing in summaries: confirm status and dates; verify transforms executed

## Steps
1) Open Ongoing Workflows
2) Select patient and task
3) Update status and notes
4) Save; verify in summaries later

## References
- Monthly summary reports; users/staff_code_mapping for name resolution