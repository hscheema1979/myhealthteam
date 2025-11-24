# Coordinator — Patient Panel

Last Updated: 2025-11-19

## Summary
How to review and manage your assigned patients, understand last visits, and ensure accurate assignments.

## Data Sources
- Patient Panel: staging_patient_panel (staging-only in current phase), curated patient_panel (production when promoted)
- Assignments and roles: users, user_roles (CC=36, LC=37), staff_code_mapping
- Visits: staging_patient_visits, last_visit updated in panel via transforms

## Inputs Required
- Assignment changes (assign/reassign coordinator)
- Patient notes (when needed)

## Outputs Downstream
- Correct assignment displays in Admin and Coordinator dashboards
- Last visit updates after transforms; affects summaries

## Guardrails
- ID normalization: ensure patient IDs match normalized prefixes (ZEN-, PM-, ZMN-)
- Coordinator name resolution relies on users/staff_code_mapping; unmapped codes show “Unknown”

## Troubleshooting
- Patient missing from panel: check staging alignment checks and data scope (3-month coordinator range)
- Coordinator name shows as number: verify mapping entry in staff_code_mapping

## Steps
1) Open Coordinator Patient Panel
2) Filter by your assignments
3) Review last_visit; drill into patient if needed
4) Update assignment if responsibility changes

## References
- Staging Alignment Checks A/B/D/E/F in outputs/reports