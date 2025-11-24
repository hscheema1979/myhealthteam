## Goals
- Apply the same normalization/validation logic used for staging to production data to confirm correctness.
- Generate clear, two-way comparison reports to ensure no data is lost.

## Scope
- Patient identity, visits, provider tasks (incl. RVZ), coordinator tasks, and panel presence.
- Limit comparisons to a date window (e.g., >= 2025-09-26) to avoid heavy scans.

## Approach
- Use TEMP views and read-only queries so production tables remain untouched.
- Reconstruct production-equivalent datasets by normalizing identifiers and dates to match staging conventions.
- Compare in both directions and write CSVs under `scripts/outputs/reports/`.

## Implementation (Read-Only)
### 1) Patient Identity
- TEMP view `P_PATIENTS_EQUIV` over `patients`:
  - Normalize `patient_id` and `last_first_dob` to canonical `LAST FIRST DOB` (strip prefixes, remove commas, collapse spaces).
- Compare with `staging_patients`:
  - `patients_in_staging_missing_in_production.csv`
  - `patients_in_production_missing_in_staging.csv`

### 2) Patient Visits
- TEMP view `P_PATIENT_VISITS_EQUIV` over `patient_visits`:
  - Normalize `patient_id` and `last_visit_date`.
- Compare with `staging_patient_visits`:
  - `patient_visits_rows_missing_in_staging.csv`
  - `patient_visits_rows_missing_in_production.csv`

### 3) Provider Tasks (Including RVZ)
- Production provider tasks are monthly-partitioned (e.g., `provider_tasks_YYYY_MM`).
- Script enumerates tables `provider_tasks_%` and builds a union TEMP view `P_PROVIDER_TASKS_EQUIV`:
  - Columns: normalized `patient_id`, `activity_date`, `provider_code_norm`, `service`.
- Compare with `staging_provider_tasks`:
  - `provider_rows_missing_in_staging_production.csv`
  - `provider_rows_missing_in_production_staging.csv`

### 4) Coordinator Tasks
- Enumerate `coordinator_tasks_%` and build TEMP view `P_COORDINATOR_TASKS_EQUIV` with normalized `patient_id`, `activity_date`, `staff_code_norm`, `task_type`.
- Compare with `staging_coordinator_tasks`:
  - `coordinator_rows_missing_in_staging_production.csv`
  - `coordinator_rows_missing_in_production_staging.csv`

### 5) Panel Presence
- TEMP view `P_PANEL_EQUIV` over `patient_panel` with normalized `patient_id`.
- Cross-check presence with `staging_patient_panel`:
  - `panel_patients_missing_in_staging.csv`
  - `panel_patients_missing_in_production.csv`

## Metrics & Thresholds
- Report counts and percentages for matched/unmatched rows per domain (patients, visits, provider/coordinator tasks).
- Flag anomalies when missing-in-one-direction exceeds a small threshold for the recent window.

## Outputs
- CSVs in `scripts/outputs/reports/` for each comparison.
- A summary `production_vs_staging_validation_summary.txt` with counts and quick notes.

## Risks & Mitigations
- Monthly partition enumeration: if many tables exist, restrict to the last 3–6 months.
- Identifier normalization differences: use the same normalization pipeline as staging to avoid false mismatches.
- RVZ handling: ensure RVZ (appended to provider tasks) uses identical normalization keys.

## Next Steps
- Implement the read-only TEMP views and comparison queries.
- Run over the recent date window (>= 2025-09-26), generate reports, and review results.

Confirm, and I will implement the TEMP views + two-way comparisons (read-only) and deliver the CSVs and summary.