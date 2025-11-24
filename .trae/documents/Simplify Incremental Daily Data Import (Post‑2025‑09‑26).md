## Goals
- Reduce the steps to add new day’s data after 2025‑09‑26.
- Avoid re‑downloading and re‑transforming historical data already verified.
- Keep changes staging‑safe by default; allow controlled promotion.

## Key Idea
- Introduce an "incremental" pipeline driven by a persisted watermark date per source (patients, provider tasks, coordinator tasks).
- Import only rows with date > watermark, transform only deltas, run a lightweight verification.

## Technical Design
- Watermark table: `etl_watermarks(source_name TEXT PRIMARY KEY, last_import_date TEXT)` in `production.db`.
  - Seed: set `last_import_date = '2025-09-26'` for sources.
  - Update to the max date successfully imported after each run.
- Unified delta script: `import_delta.ps1` (simple single command).
  - Reads watermark → computes `StartDate = last_import_date + 1 day`.
  - Imports only new rows from CSVs into `sheets_data.db` using existing `csv_to_sql.py`.
  - Supports `-Date YYYY-MM-DD` to process a specific day and `-Range Start End` for backfills.
- Delta transforms (append‑only):
  - Build temporary `staging_provider_tasks_delta`, `staging_coordinator_tasks_delta` for rows >= `StartDate`.
  - Merge into `staging_provider_tasks` / `staging_coordinator_tasks` via `INSERT OR IGNORE` on a stable key `(patient_id, activity_date, service, provider_code)`.
  - Update `staging_patient_visits` and summaries only for affected weeks/months.
- Lightweight verification (`--quick`):
  - Counts imported vs merged; sample unmatched (limit 50) using current `verify_normalization_linkage.py` with a quick mode flag.
  - Abort promotion if collisions spike or linkage drops below thresholds.

## User Flow
- One command to ingest today’s data: `./scripts/import_delta.ps1 -Date 2025-11-22` or `-SinceLast` (default).
- Optional Admin UI button: “Import today’s data” → runs the same pipeline and prints a short summary.

## Safeguards & Edge Cases
- Late arrivals older than watermark: support `-Range` or `-StartDate` overrides; pipeline backfills and updates watermark appropriately.
- Idempotency: `INSERT OR IGNORE` avoids duplicates; dedupe key prevents re‑ingest of same rows.
- Staging‑only by default; promotion step is separate and gated by verification.

## Changes Needed
- Create `etl_watermarks` table and seed baseline `2025-09-26` per source.
- Add `import_delta.ps1` orchestration script with parameters (`-Date`, `-Range`, `-SinceLast`, `-Promote` optional).
- Extend `4b-transform.ps1` or add a small SQL file to support delta append/merge flow.
- Add `--quick` flag to `verify_normalization_linkage.py` to limit heavy checks.
- (Optional) Admin UI action to trigger and show results.

## Validation
- Run delta on a test day; confirm:
  - Watermark advances to the max date ingested.
  - Staging tables reflect only new rows; curated tables untouched.
  - Quick verification passes thresholds (e.g., collisions ≤ baseline, linkage stable for provider tasks).

## Risks & Mitigations
- Risk: late data older than watermark missed → mitigated by `-Range` backfill.
- Risk: incorrect dedupe key → choose conservative composite key and keep a comparison log.
- Risk: linkage for very recent patients low → accept; promotion requires manual review.

## Next Steps
- Implement watermark + delta import script.
- Wire up delta append transforms.
- Add quick verification mode.
- (Optional) Add Admin UI trigger.

Please confirm this plan; upon approval, I will implement the delta pipeline and quick verification, keeping staging‑only by default and documenting the watermark state.