**Coordinator & Provider Monthly Partitioning And Safe Update Workflow**

Date: 2025-09-23

Overview

- **Purpose:**: Document the plan to partition coordinator and provider task data by month, ensure patients are created and linked correctly, and provide a safe update workflow to prepare and swap `production.db` after validating transforms.
- **Scope:**: Partition `coordinator_tasks` and `provider_tasks` into monthly tables, add clear source provenance, and provide step-by-step commands and SQL templates to run transforms on a copy of the live database (`update_data.db`) before an atomic swap.

Background / Problem Summary

- **Issue:**: Current import of `SOURCE_COORDINATOR_TASKS_HISTORY` inserts the raw `Pt Name` into `coordinator_tasks.patient_id` (text), requiring later fixes. Date formats in source files are inconsistent which makes month-based partitioning unreliable unless normalized first.
- **Risk:**: `production.db` is live — do NOT overwrite it directly. Use a consistent backup and validation process.

Goals

- **Primary:**: Produce per-month task tables named `coordinator_tasks_YYYY_MM` and `provider_tasks_YYYY_MM` populated with normalized dates and numeric `patient_id` references to `patients` (creating missing patients when necessary).
- **Secondary:**: Preserve provenance by optionally importing new CSVs into new source tables (e.g. `SOURCE_COORDINATOR_TASKS_HISTORY_2`) so imports are idempotent and auditable.

High-Level Workflow

1. Stop the app or ensure no processes are writing to `production.db`.
2. Create a consistent copy: `update_data.db` using SQLite `.backup`.
3. Import latest consolidated CSVs into new SOURCE tables (optional) using `scripts/3_import_to_database.ps1` pointing at `update_data.db`.
4. Normalize dates and create a staging table `staging_coordinator_tasks` / `staging_provider_tasks`.
5. Create monthly tables for target months and populate them from staging, joining to `patients` to obtain numeric `patient_id`.
6. Run validation queries and reports.
7. Once validated, perform the atomic swap: rename files so `update_data.db` becomes the new `production.db` and keep a backup copy.

Commands (PowerShell / sqlite3 examples)

- **Create a consistent backup copy (use sqlite3 .backup)**:

```powershell
# Create a consistent backup copy called update_data.db
sqlite3 production.db ".backup 'update_data.db'"

# Verify the copy exists
Get-Item .\update_data.db
```

- **Stop application and ensure DB lock is released**: (platform-specific: stop the Streamlit process or service)

- **Run import scripts against `update_data.db`** (example, adjust params if scripts accept them):

```powershell
# Example: import consolidated CSVs into SOURCE tables in update_data.db
.\scripts\3_import_to_database.ps1 -DatabasePath .\update_data.db

# If you prefer to import into new SOURCE table names, adapt the script or call csv loader directly:
python src\utils\csv_to_sql.py --db .\update_data.db --table SOURCE_COORDINATOR_TASKS_HISTORY_2 --csv downloads\coordinators\combined.csv
```

- **Run transforms on `update_data.db`** (example):

```powershell
# Run the transform orchestrator (ensure script supports -DatabasePath)
.\scripts\4_transform_data_enhanced.ps1 -DatabasePath .\update_data.db

# Or run individual SQL scripts against update_data.db with sqlite3:
sqlite3 .\update_data.db "BEGIN; .read src/sql/complete_patient_transformation.sql; .read src/sql/fix_coordinator_data_issues.sql; COMMIT;"
```

Notes: Some PS scripts accept `-DatabasePath` already; if not, edit the script to pass the alternative path to the SQL runner.

SQL Templates

1. Normalize dates into a staging table (coordinator tasks example)

`````sql
-- Create a staging table with a normalized activity_date column
DROP TABLE IF EXISTS staging_coordinator_tasks;
````markdown
**Coordinator, Provider & Patient Migration Plan — Monthly Partitioning and Safe Update Workflow**

Date: 2025-09-23 (updated)

Table of contents
- Introduction and goals
- Safety & safe-swap summary
- Phase 0: Pre-checks and inventory
- Phase 1: Source import (CSV -> SOURCE_* tables)
- Phase 2: Staging and normalization (coordinator + provider)
- Phase 3: Monthly partition creation and population
- Phase 4: Patient creation & patient_id resolution
- Phase 5: Validation, indexes and summaries
- Phase 6: Swap to production and rollback plan
- Database function updates for dashboards (`src/database.py`)
- Execution checklist and runbook
- Appendix: SQL & PowerShell code snippets

Introduction and goals
- Purpose: migrate coordinator/provider task history into monthly partitioned tables and ensure tasks reference canonical numeric `patients.patient_id`. Provide a reproducible, auditable, and safe workflow to prepare data in a working copy (`update_data.db`) and atomically swap into production after validation.
- Scope: coordinator tasks, provider tasks, patient creation, provenance, indexing, and dashboard view compatibility.

Safety & safe-swap summary (short)
- Never overwrite `production.db` directly. Use `sqlite3 .backup` to create `update_data.db` for transforms.
- Run all transforms and validations against `update_data.db`.
- When validated, stop the app, archive `production.db`, and atomically rename `update_data.db` into `production.db` (keep a pre-update backup).

Phase 0: Pre-checks and inventory
- Confirm available source CSV files in `downloads/` and check script `scripts/1_download_files_complete.ps1` and `scripts/2_consolidate_files.ps1`.
- Confirm current counts and sample rows from live DB (example commands):
  - `sqlite3 production.db "SELECT COUNT(*) FROM SOURCE_COORDINATOR_TASKS_HISTORY;"`
  - `sqlite3 production.db "SELECT COUNT(*) FROM SOURCE_PROVIDER_TASKS_HISTORY;"`
  - `sqlite3 production.db "SELECT COUNT(*) FROM SOURCE_PATIENT_DATA;"`

Phase 1: Source import (CSV -> SOURCE_* tables)
- Best practice: import latest CSVs into new, auditable SOURCE tables (append a `_2` suffix) so original SOURCE tables remain unchanged for reference. Example targets:
  - `SOURCE_COORDINATOR_TASKS_HISTORY_2`
  - `SOURCE_PROVIDER_TASKS_HISTORY_2`
  - `SOURCE_PATIENT_DATA` (or keep the current table name if it already receives ZMO_Main.csv)

PowerShell example (import into update_data.db)
```powershell
# create consistent working copy
sqlite3 .\production.db ".backup 'update_data.db'"

# import CSVs into update_data.db source tables (csv_to_sql.py supports table and db path)
python .\src\utils\csv_to_sql.py --db .\update_data.db --table SOURCE_COORDINATOR_TASKS_HISTORY_2 --csv .\downloads\cmlog.csv --skip-empty-columns
python .\src\utils\csv_to_sql.py --db .\update_data.db --table SOURCE_PROVIDER_TASKS_HISTORY_2 --csv .\downloads\psl.csv --skip-empty-columns
python .\src\utils\csv_to_sql.py --db .\update_data.db --table SOURCE_PATIENT_DATA --csv .\downloads\patients\ZMO_Main.csv --skip-empty-columns
`````

Phase 2: Staging and normalization

- Create staging tables that normalize dates, extract patient-name components, and provide clean fields for partitioning.

SQL: `src/sql/staging_coordinator_tasks.sql` (suggested)

```sql
DROP TABLE IF EXISTS staging_coordinator_tasks;
CREATE TABLE staging_coordinator_tasks AS
SELECT
  rowid AS src_rowid,
  "Staff" AS staff_code,
  "Pt Name" AS patient_name_raw,
  TRIM("Type") AS task_type,
  TRIM("Notes") AS notes,
  "Mins B" AS minutes_raw,
  -- normalized ISO date (YYYY-MM-DD) when possible
  CASE
    WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    ELSE NULL
  END AS activity_date,
  -- derived partition key 'YYYY_MM'
  CASE
    WHEN "Date Only" IS NOT NULL THEN
      CASE
        WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
        WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
        ELSE NULL
      END
    ELSE NULL
  END AS year_month
FROM SOURCE_COORDINATOR_TASKS_HISTORY_2;

CREATE INDEX IF NOT EXISTS idx_staging_coordinator_year_month ON staging_coordinator_tasks(year_month);
CREATE INDEX IF NOT EXISTS idx_staging_coordinator_activity_date ON staging_coordinator_tasks(activity_date);
```

SQL: `src/sql/staging_provider_tasks.sql` (suggested)

```sql
DROP TABLE IF EXISTS staging_provider_tasks;
CREATE TABLE staging_provider_tasks AS
SELECT
  rowid AS src_rowid,
  "Prov" AS provider_code,
  "Patient Last, First DOB" AS patient_name_raw,
  TRIM("Service") AS service,
  TRIM("Coding") AS billing_code,
  "Minutes" AS minutes_raw,
  CASE
    WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    ELSE NULL
  END AS activity_date,
  CASE
    WHEN "DOS" IS NOT NULL THEN
      CASE
        WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
        WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
        ELSE NULL
      END
    ELSE NULL
  END AS year_month
FROM SOURCE_PROVIDER_TASKS_HISTORY_2;

CREATE INDEX IF NOT EXISTS idx_staging_provider_year_month ON staging_provider_tasks(year_month);
CREATE INDEX IF NOT EXISTS idx_staging_provider_activity_date ON staging_provider_tasks(activity_date);
```

Phase 3: Monthly partition creation and population

- Strategy: create per-month tables named `coordinator_tasks_YYYY_MM` and `provider_tasks_YYYY_MM`. Each table has the same schema (explicitly declared) and indexes on `patient_id`, `coordinator_id`/`provider_id`, and `task_date`.

Suggested table schema (use explicit columns for stability):

```sql
CREATE TABLE IF NOT EXISTS coordinator_tasks_template (
  coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT, -- optional source id
  patient_id INTEGER, -- FK -> patients(patient_id)
  patient_name_raw TEXT,
  coordinator_id TEXT,
  coordinator_name TEXT,
  task_date DATE,
  duration_minutes INTEGER,
  task_type TEXT,
  notes TEXT,
  source_system TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS provider_tasks_template (
  provider_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT,
  patient_id INTEGER,
  patient_name_raw TEXT,
  provider_id TEXT,
  provider_name TEXT,
  task_date DATE,
  minutes_of_service INTEGER,
  service_code TEXT,
  billing_code TEXT,
  notes TEXT,
  source_system TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

PowerShell helper: `scripts/generate_monthly_partitions.ps1` (example usage)

```powershell
# Usage: .\scripts\generate_monthly_partitions.ps1 -StartYear 2024 -StartMonth 1 -EndYear 2025 -EndMonth 12
param(
  [int]$StartYear = 2024,
  [int]$StartMonth = 1,
  [int]$EndYear = 2025,
  [int]$EndMonth = 12,
  [string]$DatabasePath = '.\update_data.db'
)

for ($y = $StartYear; $y -le $EndYear; $y++) {
  $m1 = ($y -eq $StartYear) ? $StartMonth : 1
  $m2 = ($y -eq $EndYear) ? $EndMonth : 12
  for ($m = $m1; $m -le $m2; $m++) {
    $ym = "{0}_{1:D2}" -f $y, $m
    $sql = @"
    CREATE TABLE IF NOT EXISTS coordinator_tasks_$ym AS SELECT * FROM coordinator_tasks_template WHERE 0;
    CREATE INDEX IF NOT EXISTS idx_coordinator_${ym}_patient ON coordinator_tasks_$ym(patient_id);
    CREATE INDEX IF NOT EXISTS idx_coordinator_${ym}_coord ON coordinator_tasks_$ym(coordinator_id);
    CREATE INDEX IF NOT EXISTS idx_coordinator_${ym}_date ON coordinator_tasks_$ym(task_date);

    CREATE TABLE IF NOT EXISTS provider_tasks_$ym AS SELECT * FROM provider_tasks_template WHERE 0;
    CREATE INDEX IF NOT EXISTS idx_provider_${ym}_patient ON provider_tasks_$ym(patient_id);
    CREATE INDEX IF NOT EXISTS idx_provider_${ym}_prov ON provider_tasks_$ym(provider_id);
    CREATE INDEX IF NOT EXISTS idx_provider_${ym}_date ON provider_tasks_$ym(task_date);
"@
    sqlite3 $DatabasePath $sql
  }
}
```

Populate monthly tables (example SQL template)
`src/sql/transform_coordinator_tasks_monthly.sql` (run per month or scripted)

```sql
-- Replace {YYYY_MM} with e.g. 2025_01 before running, or use a PS wrapper to run multiple months
INSERT INTO coordinator_tasks_{YYYY_MM} (
  task_id, patient_id, patient_name_raw, coordinator_id, coordinator_name, task_date, duration_minutes, task_type, notes, source_system
)
SELECT
  CAST(src.src_rowid AS TEXT) as task_id,
  NULL as patient_id, -- populate later via patient resolution step
  src.patient_name_raw,
  src.staff_code as coordinator_id,
  NULL as coordinator_name,
  src.activity_date,
  CASE WHEN src.minutes_raw GLOB '*[0-9]*' THEN CAST(src.minutes_raw AS INTEGER) ELSE NULL END as duration_minutes,
  src.task_type,
  src.notes,
  'SOURCE_COORDINATOR_TASKS_HISTORY_2' as source_system
FROM staging_coordinator_tasks src
WHERE src.year_month = '{YYYY_MM}'
  AND src.activity_date IS NOT NULL;
```

Do the same for provider tasks in `src/sql/transform_provider_tasks_monthly.sql`.

Phase 4: Patient creation & patient_id resolution

- After monthly inserts store `patient_name_raw` for later resolution. Then:
  1. Create missing patients from monthly partitions (rows where `patient_id` is null and `patient_name_raw` contains a parsable DOB or name pattern).
  2. Update monthly tables setting `patient_id` to the newly-created `patients.patient_id` where `patients.last_first_dob` matches the raw string.

SQL: create missing patients (suggested `src/sql/fix_coordinator_data_issues.sql`)

```sql
-- Insert minimal patient rows for uniquely parsable names found in partitions
INSERT INTO patients (first_name, last_name, date_of_birth, last_first_dob, source_system, created_date, updated_date)
SELECT DISTINCT
  TRIM(SUBSTR(pn, INSTR(pn, ',')+1, INSTR(pn, ' ', INSTR(pn, ',')+1) - INSTR(pn, ',') - 1)) AS first_name,
  TRIM(SUBSTR(pn, 1, INSTR(pn, ',')-1)) AS last_name,
  -- try to parse DOB at end of string when present as MM/DD/YYYY or MM/DD/YY
  (CASE
    WHEN pn GLOB '*[0-1][0-9]/[0-3][0-9]/????' THEN date(substr(pn, -10, 4) || '-' || substr(pn, -10, 1) || '-' || substr(pn, -10, 4))
    ELSE NULL
  END) AS date_of_birth,
  pn AS last_first_dob,
  'COORDINATOR_TASKS_AUTO' as source_system,
  datetime('now'), datetime('now')
FROM (
  SELECT DISTINCT patient_name_raw as pn FROM (
    SELECT patient_name_raw FROM coordinator_tasks_2025_01
    UNION ALL
    SELECT patient_name_raw FROM coordinator_tasks_2025_02
    -- add unions for months processed or build this dynamically
  ) WHERE pn IS NOT NULL AND pn != ''
)
WHERE NOT EXISTS (SELECT 1 FROM patients p WHERE p.last_first_dob = pn);
```

SQL: update monthly partitions to resolve patient_id

```sql
-- Example for January 2025
UPDATE coordinator_tasks_2025_01
SET patient_id = (
  SELECT p.patient_id FROM patients p WHERE p.last_first_dob = coordinator_tasks_2025_01.patient_name_raw LIMIT 1
)
WHERE patient_id IS NULL AND patient_name_raw IS NOT NULL;
```

Repeat for each monthly partition (or script it).

Phase 5: Validation, indexes and summaries

- Run validation queries on `update_data.db` before swap. Example `scripts/validation_checks.sql` should include:
  - counts by source, month and unmatched rows
  - ratio of tasks with numeric patient_id
  - sample unmatched patient_name_raw rows

Example checks

```sql
-- Total tasks processed
SELECT 'coord_total', COUNT(*) FROM staging_coordinator_tasks;
SELECT 'coord_month_2025_01', COUNT(*) FROM coordinator_tasks_2025_01;

-- Matched vs unmatched
SELECT
  COUNT(*) as total_tasks,
  SUM(CASE WHEN patient_id IS NOT NULL THEN 1 ELSE 0 END) as matched_tasks,
  ROUND(100.0 * SUM(CASE WHEN patient_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*),2) as pct_matched
FROM coordinator_tasks_2025_01;

-- Sample unmatched
SELECT patient_name_raw, task_date, duration_minutes FROM coordinator_tasks_2025_01 WHERE patient_id IS NULL LIMIT 50;
```

Performance indexes (run after large inserts)

```sql
CREATE INDEX IF NOT EXISTS idx_coord_2025_01_patient ON coordinator_tasks_2025_01(patient_id);
CREATE INDEX IF NOT EXISTS idx_coord_2025_01_coord ON coordinator_tasks_2025_01(coordinator_id);
CREATE INDEX IF NOT EXISTS idx_coord_2025_01_date ON coordinator_tasks_2025_01(task_date);
```

Phase 6: Swap to production and rollback plan

- Steps to finalize (run only after validation passes):
  1. Stop the app (Streamlit) or ensure no open writers.
  2. Archive `production.db` (keep WAL/SHM):

```powershell
$ts = (Get-Date).ToString('yyyy-MM-dd_HH-mm-ss')
Copy-Item .\production.db ".\backups\production_backup_$ts.db" -Force
```

3. Atomically rename the validated `update_data.db` to `production.db`:

```powershell
Move-Item .\production.db ".\backups\production_pre_swap_$ts.db" -Force
Move-Item .\update_data.db .\production.db -Force
Remove-Item .\production.db-wal -ErrorAction SilentlyContinue
Remove-Item .\production.db-shm -ErrorAction SilentlyContinue
```

4. Start the app and run smoke checks (dashboard loads, sample queries).
5. If rollback required, use the pre-swap archive:

```powershell
Move-Item .\production.db .\production_failed_swap_$ts.db -Force
Move-Item .\backups\production_pre_swap_$ts.db .\production.db -Force
```

Database function updates for dashboards (`src/database.py`)

- Requirement: make `src/database.py` functions accept an optional `db_path` so transforms/QA can run against `update_data.db` without changing global scripts. Add helper wrapper `get_db_connection(db_path=None)`.

Suggested function signatures and SQL patterns (implement in `src/database.py`):

- get_db_connection(db_path: str | None = None) -> sqlite3.Connection

  - Use `db_path` if provided, default to `production.db` in repo root.

- get_all_users(db_path=None) -> list[dict]

  - Returns user list for Admin dashboard.

- get_coordinator_monthly_minutes(coordinator_id, year, month, db_path=None) -> int

  - Query: `SELECT SUM(duration_minutes) FROM coordinator_tasks_{year}_{month:02d} WHERE coordinator_id = ?`

- get_provider_monthly_minutes(provider_id, year, month, db_path=None) -> int

  - Query similar to coordinator.

- get_coordinator_patients(coordinator_id, db_path=None, limit=100, offset=0) -> list[dict]
  - Join partitioned tables (or union a small set of months) to return assigned patients with last activity.

Implementation notes:

- Avoid dynamic table names directly in parameterized queries. Build SQL safely using Python formatting for the table name after validating `year` and `month` types.
- Use `conn.row_factory = sqlite3.Row` to return dictionaries.

Example helper (illustrative, add to `src/database.py`):

```python
def get_db_connection(db_path: str | None = None):
    import sqlite3
    path = db_path or os.path.join(ROOT_DIR, 'production.db')
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def get_coordinator_monthly_minutes(coordinator_id: str, year: int, month: int, db_path: str | None = None):
    table = f"coordinator_tasks_{year}_{month:02d}"
    conn = get_db_connection(db_path)
    try:
        cur = conn.execute(f"SELECT SUM(duration_minutes) as total_minutes FROM {table} WHERE coordinator_id = ?", (coordinator_id,))
        row = cur.fetchone()
        return row['total_minutes'] or 0
    finally:
        conn.close()
```

Execution checklist and runbook
| Step | Script / SQL | Target DB | Responsible | Timestamp | Result |
|---|---|---:|---|---|---|
| Create `update_data.db` via `.backup` | `sqlite3 production.db ".backup 'update_data.db'"` | update_data.db | Data Engineer | | |
| Import CSVs into `_2` source tables | `src/utils/csv_to_sql.py` calls | update_data.db | Data Engineer | | |
| Build staging tables | `src/sql/staging_coordinator_tasks.sql` | update_data.db | Data Engineer | | |
| Generate monthly partitions | `scripts/generate_monthly_partitions.ps1` | update_data.db | Data Engineer | | |
| Populate monthly partitions | `src/sql/transform_coordinator_tasks_monthly.sql` (per month) | update_data.db | Data Engineer | | |
| Create missing patients & resolve ids | `src/sql/fix_coordinator_data_issues.sql` and `UPDATE` statements | update_data.db | Data Engineer | | |
| Run validation suite | `scripts/validation_checks.sql` | update_data.db | QA / Data Eng | | |
| Archive production & swap | `scripts/safe_swap_db.ps1` (or manual PS) | production.db | Ops | | |
| Smoke tests | Dashboard checks and queries | production.db | QA / Dev | | |

Appendix: snippet collection

- `scripts/safe_swap_db.ps1` (recommended) will wrap `.backup`, run a sequence of SQL files (staging -> partitions -> fix -> validation) against `update_data.db` and ask for manual confirmation before swapping. Keep the script interactive; do NOT enable auto-swap by default.

Notes and next steps

- I can:
  - Add the provider staging/transform SQL files (I included templates above) and commit them to `src/sql/`.
  - Add `scripts/safe_swap_db.ps1` that executes the pipeline and runs `scripts/validation_checks.sql`.
  - Update `src/database.py` with the helper functions described and add unit-style smoke-check functions that run on `update_data.db`.

If you want me to implement any of those next steps (create the SQL files, create the PowerShell orchestrator, or patch `src/database.py`) tell me which to do first and I will make the changes and run local validations against a non-destructive `update_data.db` copy.

```

```
