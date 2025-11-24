# Coordinator Workflow Guide

Last Updated: 2025-11-19

## Summary — What & Why
This guide explains the end-to-end coordinator workflow in the Zen Medicine dashboards: how to manage the patient panel, start and track workflows, and record tasks consistently so downstream reports (visits, summaries, billing) remain accurate.

## Data Sources — Where the Data Comes From
- Panel & Assignments: staging_patient_panel (staging-only in recent runs), curated patient_panel (production) when promoted.
- Coordinator Tasks: staging_coordinator_tasks (history), monthly partitions (coordinator_tasks_YYYY_MM) for summaries.
- Visits & Latest Visit: staging_patient_visits built from tasks; last_visit updated in staging_patient_panel via transform.
- Users & Roles: users, user_roles; coordinator roles typically role_id 36 (CC) and 37 (LC).

## Inputs — What You Must Provide
- Task Type (e.g., Phone Review, Follow-up, Scheduling) — choose the action performed.
- Notes — capture details, decisions, outcomes; avoid vague notes.
- Due Date — to set reminders and future follow-ups.
- Status — mark “In Progress” or “Completed” appropriately.
- Assignment changes — use panel assignment tools when assigning or reassigning coordinators.

## Outputs — What Happens Downstream
- Workflow Stage may advance based on Task Type/Status.
- Patient’s last_visit can update after transforms (staging-only unless promoted).
- Monthly/weekly summaries aggregate minutes and counts by coordinator.
- Data appears in Admin dashboard with coordinator name resolution via users/staff_code_mapping.

## Guardrails — Common Mistakes to Avoid
- ID Namespace Confusion: coordinator_id can be users.user_id or staff codes (e.g., CHAZU000). Display layers resolve names but unmapped codes show “Unknown”.
- Prefix Normalization: Patient IDs with prefixes (ZEN-, PM-, ZMN-) are normalized in comparisons; ensure consistent IDs in tasks vs panel.
- DOS vs activity_date: Provider DOS derives activity_date; if missing, checks can break. Coordinators should ensure dates are captured correctly in tasks.
- Don’t leave tasks without Status; incomplete states degrade summary accuracy.

## Troubleshooting — How to Fix Issues
- Coordinator name shows as a number: confirm user role (36/37) and staff_code_mapping for that coordinator; escalate unmapped ZEN-* codes.
- Panel vs Tasks mismatch: review staging alignment checks; some patients are in tasks but not panel (or vice versa) due to scope differences.
- Missing latest visit: verify transforms (4c) ran in staging-only and that tasks include valid dates.

## Examples — Step-by-Step
1) From Patient Panel, open a patient.
2) Choose Task Type “Phone Review”, set Status “Completed”, add detailed notes.
3) Set Due Date for next follow-up if needed.
4) Save — the workflow stage updates, minutes aggregate, and the visit may be reflected after transforms.

## Role Responsibilities
- Care Coordinator (CC): Owns ongoing workflows, follow-ups, scheduling, and task documentation.
- Lead Coordinator (LC): Oversees CCs, validates assignments, reviews monthly summaries.

## References
- Staging Alignment Checks (A/B/D/E/F) reports under outputs/reports.
- Admin dashboard coordinator name resolver (uses users and staff_code_mapping).