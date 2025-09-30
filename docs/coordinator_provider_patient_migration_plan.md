# Coordinator, Provider, and Patient Migration Plan

Date: 2025-09-23

Version: 1.0

Purpose

- Provide a single, cohesive plan to migrate and transform coordinator, provider, and patient data from source CSVs / SOURCE\_\* tables into production-ready tables.
- Include architecture, detailed steps, SQL templates, required updates to `src/database.py`, execution tracking templates, validation queries, and rollback instructions.

Table of Contents

1. Executive Summary
2. Goals and Success Criteria
3. Architecture & Data Flow
4. Key Tables and Naming Conventions
5. Patient Matching Strategy
6. Coordinator & Provider Task Partitioning Strategy
7. Safe Database Update Workflow
8. SQL Templates
   - Staging normalization
   - Monthly partition creation
   - Monthly partition population
   - Patient creation from task data
9. Database API / `src/database.py` Updates
10. Execution Checklist & Tracking
11. Validation Queries and Smoke Tests
12. Rollback and Recovery
13. Automation and Next Steps

14. Executive Summary

- The project standardizes ingestion of coordinator/provider task data and patient data by:
  - Importing source CSVs into clearly-named SOURCE tables (or `_2` variants for new imports).
  - Normalizing dates and patient-name formats in staging tables.
  - Creating per-month task partitions named `coordinator_tasks_YYYY_MM` and `provider_tasks_YYYY_MM`.
  - Ensuring `patients` contains canonical patient records and monthly task partitions reference numeric `patient_id`.
  - Performing all transforms on a consistent backup `update_data.db` (created via SQLite `.backup`) and swapping atomically after validation.

2. Goals and Success Criteria

- Goals:
  - Accurate patient matching (minimize unmatched rows).
  - All coordinator/provider tasks assigned to numeric `patient_id` where possible.
  - Monthly partitioning for performance and reporting.
  - Safe, auditable update of `production.db`.
- Success criteria:
  - Validation counts match source CSV exports within an expected tolerance.
  - Unmatched patient rows reduced to acceptable threshold (configurable).
  - Dashboards load without errors after swap; critical metrics consistent.

3. Architecture & Data Flow

- Data flow:
  1. Google Sheets / CSV → `downloads/`
  2. Consolidation & clean scripts → `downloads/consolidated/*.csv`
  3. `scripts/3_import_to_database.ps1` (or `src/utils/csv_to_sql.py`) → `SOURCE_*` tables in `update_data.db`
  4. Normalize → `staging_*` tables
  5. Patient creation/merge → `patients`
  6. Populate monthly partitions `coordinator_tasks_YYYY_MM` and `provider_tasks_YYYY_MM`
  7. Validate → swap `update_data.db` → `production.db`

4. Key Tables and Naming Conventions

- SOURCE tables: `SOURCE_COORDINATOR_TASKS_HISTORY`, `SOURCE_PROVIDER_TASKS_HISTORY`, `SOURCE_PATIENT_DATA` (incoming imports). Consider `_2` suffix for new runs.
- Staging tables: `staging_coordinator_tasks`, `staging_provider_tasks` (normalized, parsed fields).
- Production partitions: `coordinator_tasks_YYYY_MM`, `provider_tasks_YYYY_MM`.
- Canonical patient table: `patients` (with `patient_id`, `first_name`, `last_name`, `date_of_birth`, `last_first_dob` and `source_system` provenance).

5. Patient Matching Strategy

- Primary match: `patients.last_first_dob = SOURCE Pt Name` when `Pt Name` has `Last, First MM/DD/YYYY` or `Last, First DOB` format.
- Secondary match: combine `first_name || ' ' || last_name` with parsed name from `Pt Name`.
- If DOB is present in `Pt Name`, parse it and perform exact `date_of_birth` match.
- For unmatched rows where `Pt Name` includes DOB, create a minimal `patients` row (with `source_system = 'COORDINATOR_TASKS_IMPORT'`) and then re-run joins.

6. Coordinator & Provider Task Partitioning Strategy

- Create monthly tables for each YYYY_MM required. Each partition contains the same schema as `coordinator_tasks` or `provider_tasks` but includes `source_system` and `imported_at` columns.
- Populate partitions from `staging_*` after normalizing dates and matching to `patients`.

7. Safe Database Update Workflow (Recommended)
1. Ensure app is stopped or quiesced.
1. Create a consistent backup using SQLite `.backup`:

```powershell
sqlite3 production.db ".backup 'update_data.db'"
```

3. Run imports and transforms in `update_data.db`.
4. Run validation queries and compare counts with source CSV totals.
5. When satisfied, rename files to swap:

```powershell
Rename-Item -Path .\production.db -NewName production.db.preupdate -Force
Rename-Item -Path .\update_data.db -NewName production.db -Force
```

6. Start app and run smoke tests.

7. SQL Templates

8.1 Staging normalization (coordinator tasks example)

```sql
DROP TABLE IF EXISTS staging_coordinator_tasks;
CREATE TABLE staging_coordinator_tasks AS
SELECT
  rowid AS source_rowid,
  "Pt Name",
  "Staff",
  "Date Only",
  "Mins B",
  -- Normalized ISO date if parsable
  CASE
    WHEN instr("Date Only", '/') > 0 AND length("Date Only") >= 8
      THEN date(substr("Date Only", 7, 4) || '-' || substr("Date Only", 1, 2) || '-' || substr("Date Only", 4, 2))
    ELSE NULL
  END AS activity_date,
  trim("Pt Name") AS patient_name_raw
FROM SOURCE_COORDINATOR_TASKS_HISTORY;

CREATE INDEX IF NOT EXISTS idx_staging_coordinator_activity_date ON staging_coordinator_tasks(activity_date);
CREATE INDEX IF NOT EXISTS idx_staging_coordinator_name_raw ON staging_coordinator_tasks(patient_name_raw);
```

8.2 Monthly partition creation (templated)

```sql
-- Create empty monthly partition with matching schema
CREATE TABLE IF NOT EXISTS coordinator_tasks_{YYYY}_{MM} AS
SELECT * FROM coordinator_tasks WHERE 0;

-- Add provenance columns if not present
ALTER TABLE coordinator_tasks_{YYYY}_{MM} ADD COLUMN IF NOT EXISTS source_system TEXT;
ALTER TABLE coordinator_tasks_{YYYY}_{MM} ADD COLUMN IF NOT EXISTS imported_at TEXT;
```

8.3 Populate monthly partition from staging

```sql
INSERT INTO coordinator_tasks_{YYYY}_{MM} (
  patient_id, patient_name, coordinator_id, activity_date, duration_minutes, source_system, imported_at
)
SELECT
  p.patient_id,
  s.patient_name_raw,
  s."Staff" AS coordinator_id,
  s.activity_date,
  CAST(s."Mins B" AS INTEGER) AS duration_minutes,
  'SOURCE_COORDINATOR_TASKS_HISTORY' AS source_system,
  CURRENT_TIMESTAMP AS imported_at
FROM staging_coordinator_tasks s
LEFT JOIN patients p ON p.last_first_dob = s.patient_name_raw
WHERE s.activity_date BETWEEN date('{YYYY}-{MM}-01') AND date('{YYYY}-{MM}-01', '+1 month', '-1 day');
```

8.4 Create patients from `Pt Name` when `Last, First DOB` pattern exists

```sql
INSERT INTO patients (first_name, last_name, date_of_birth, last_first_dob, source_system)
SELECT
  trim(substr(name, instr(name, ',')+1, instr(name, ' ', instr(name, ',')+1) - instr(name, ',') - 1)) AS first_name,
  trim(substr(name, 1, instr(name, ',')-1)) AS last_name,
  date(parsed_dob) AS date_of_birth,
  name AS last_first_dob,
  'COORDINATOR_TASKS_IMPORT' AS source_system
FROM (
  SELECT patient_name_raw AS name,
    -- extract DOB if present in MM/DD/YYYY at end
    substr(patient_name_raw, -10, 10) AS parsed_dob
  FROM staging_coordinator_tasks
  WHERE length(patient_name_raw) > 8 AND instr(patient_name_raw, ',') > 0
);
```

9. Database API / `src/database.py` Updates

- Update existing functions and add new ones to support dashboards and partitioned data. Key functions to update/add (examples):

- `get_db_connection()` — ensure it accepts an optional `db_path` argument to target `update_data.db` for testing.
- `get_all_users()` — return user metadata for admin views.
- `get_users_by_role(role_identifier)` — allow role id or name filter.
- `get_user_patient_assignments(user_id, include_inactive=False)` — include patient status and assignment metadata.
- `get_coordinator_weekly_patient_minutes(coordinator_id, weeks_back=4)` — return per-patient breakdown.
- `get_coordinator_monthly_minutes(coordinator_id, year, month)` — returns total minutes; use partitioned tables when available.
- `get_provider_patient_panel_enhanced(user_id)` — return the enhanced patient panel for provider dashboard.
- `add_patient(first_name, last_name, date_of_birth, source_system='DATA_ENTRY')` — insert and return `patient_id`.

Example signature (with db_path optional):

```python
def get_db_connection(db_path: str = None):
    """Return a SQLite connection. If db_path provided, use that path (useful for update_data.db)."""
    ...
```

10. Execution Checklist & Tracking

Use this table to track each step during execution. Fill `Responsible`, `Timestamp`, `Command`, and `Result/Notes`.

| Step                                       | Responsible | Timestamp | Command / SQL run                                                                  | Result / Notes |
| ------------------------------------------ | ----------: | --------- | ---------------------------------------------------------------------------------- | -------------- |
| Create update copy (`.backup`)             |             |           | `sqlite3 production.db ".backup 'update_data.db'"`                                 |                |
| Import CSVs to SOURCE\_\* (update_data.db) |             |           | `.\scripts\3_import_to_database.ps1 -DatabasePath .\update_data.db`                |                |
| Normalize staging tables                   |             |           | `sqlite3 .\update_data.db ".read src/sql/staging_coordinator_tasks.sql"`           |                |
| Create monthly partitions                  |             |           | `sqlite3 .\update_data.db ".read src/sql/create_monthly_task_tables.sql"`          |                |
| Populate monthly partitions                |             |           | `sqlite3 .\update_data.db ".read src/sql/transform_coordinator_tasks_monthly.sql"` |                |
| Run patient creation fixes                 |             |           | `sqlite3 .\update_data.db ".read src/sql/fix_coordinator_data_issues.sql"`         |                |
| Run validations                            |             |           | Validation queries in Section 11                                                   |                |
| Stop app and swap DBs                      |             |           | Rename commands in Section 7                                                       |                |
| Smoke test app                             |             |           | Dashboard checks + sample queries                                                  |                |

11. Validation Queries and Smoke Tests

- Compare totals to source CSV "expected" numbers.

Basic checks:

```sql
SELECT COUNT(*) FROM SOURCE_COORDINATOR_TASKS_HISTORY;
SELECT COUNT(*) FROM staging_coordinator_tasks;
SELECT COUNT(*) FROM coordinator_tasks_2025_09;
SELECT COUNT(*) FROM patients;

-- Unmatched rows
SELECT COUNT(*) FROM staging_coordinator_tasks s
LEFT JOIN patients p ON p.last_first_dob = s.patient_name_raw
WHERE p.patient_id IS NULL;
```

Smoke tests:

- Launch the app (or a local instance) pointed to new `production.db` and verify critical dashboards (Admin summary, Coordinator panel, Provider panel) load.
- Spot-check patient counts and time-served metrics for selected providers/coordinators.

12. Rollback and Recovery

- Keep `production.db.preupdate` after swap until final sign-off (do not delete immediately).
- To rollback:

```powershell
Stop-Service <app-service> # or stop process
Rename-Item -Path .\production.db -NewName production.db.failed -Force
Rename-Item -Path .\production.db.preupdate -NewName production.db -Force
Start-Service <app-service>
```

13. Automation and Next Steps

- Implement `scripts/safe_swap_db.ps1` to automate the backup, transform run, validations, and conditional swap when validations pass.
- Implement `src/sql/*` scripts listed in Section 8 as distinct files so `.
ead` can be used in the orchestrator.
- Update `src/database.py` to support `db_path` argument and add the new helper functions listed in Section 9.
- Optional: Add a small Python validation utility `scripts/validate_update_db.py` that runs the validation queries and returns exit code 0 when thresholds pass.

Appendix: Useful Commands

```powershell
# Create update copy
sqlite3 production.db ".backup 'update_data.db'"

# Run import and transforms
.\scripts\3_import_to_database.ps1 -DatabasePath .\update_data.db
.\scripts\4_transform_data_enhanced.ps1 -DatabasePath .\update_data.db

# Validation (example)
sqlite3 .\update_data.db "SELECT COUNT(*) FROM coordinator_tasks_2025_09;"

# Swap
Rename-Item -Path .\production.db -NewName production.db.preupdate -Force
Rename-Item -Path .\update_data.db -NewName production.db -Force
```

Contact / Ownership

- Data Engineer / Owner: [fill name]
- Reviewer: [fill name]

End of document.
