# PROJECT LIVING DOCUMENT

## Session Log — 2025-11-19 — Coordinator Help: Visual Mockups Added

Context
- Request: "Show the elements being described in Help; use HTML to simulate what we need to do or what we're looking at."
- Scope: Non-management Care Coordinator Help tab in `src/dashboards/care_coordinator_dashboard_enhanced.py`.

Changes Made
1) Appended static HTML mockups to Help tab:
   - Patient Panel example table with realistic headers and one sample row (Status, First/Last Name, Facility, Provider, Last Visit Date, Service Type, POC-A, POC-M, Mins).
   - Workflow Manager example controls (mock select/input fields for template, start date, patient, coordinator; disabled Start Workflow button).
   - Ongoing Workflows example table (Workflow, Patient, Coordinator, Started, Completed/Total Steps, Actions with disabled buttons).
   - Task Entry example layout (Date, Patient, Task Type, Duration; Notes area; disabled Log Task button).
   - Lightweight CSS to mimic Streamlit/Material styles while clearly marking controls as static.
2) Increased Help components.html height to 1100 to accommodate visuals.

Verification
- Streamlit dev server remains running (http://localhost:8504/) and autoreloaded without terminal errors.
- Opened preview and visually confirmed the mockups render correctly.

Risk & Gap Analysis
- Consistency drift: Mock examples could diverge from real widget labels/columns if upstream UI changes. Mitigation: centralize help strings/column names or generate mock content from the same source definitions.
- Accessibility: Static visuals may not fully convey interactive affordances. Mitigation: add brief text notes and consider small animated GIFs/screenshots.
- Styling mismatch: HTML/CSS approx may not perfectly match Streamlit widget look. Mitigation: fine-tune CSS or capture screenshots directly from the app.

Technical Debt
- Help content is duplicated across coordinator variants. We should centralize help content in `docs/help/coordinator` and render via a single utility.
- No pre-commit validation to catch help-text drift (column/label changes). Consider a check that compares help doc keys vs UI schema.

Next Steps (Proposed)
- Centralize help content and examples: move HTML fragments into a helper and reuse across dashboards.
- Add anchors and optional screenshots for each element; possibly link to a fuller guide in `docs/help/coordinator`.
- Consider generating mock tables from a tiny DataFrame built from the same column list used in the panel to ensure exact match.

---

## Session Log — 2025-11-19 — Coordinator Help: Interactive (Real Widgets, Read-only)

Context
- Request: "Forget the screenshot and use the actual elements in the help view to explain what they do and how to use them."
- Scope: Same Help tab in `care_coordinator_dashboard_enhanced.py`.

Changes Made
1) Added live Streamlit widgets (disabled/read-only) under "Interactive Examples":
   - Patient Panel: `st.dataframe` with the exact panel columns and a sample row.
   - Workflow Manager: `st.selectbox`, `st.date_input`, `st.button` (disabled) to show the real Quick Start fields.
   - Ongoing Workflows: `st.dataframe` showing status columns (Workflow, Patient, Coordinator, Started, Completed/Total Steps).
   - Task Entry: `st.date_input`, `st.selectbox`, `st.number_input`, `st.text_area`, `st.button` (all disabled) to mirror task logging.
2) Kept the descriptive HTML guide above for context; interactive widgets appear below with explanatory captions.

Verification
- Dev server autoreloaded; preview at http://localhost:8504/ shows the new "Interactive Examples" expanders without errors.
- Terminal shows server running; no new errors detected.

Risk & Gap Analysis
- Widget capability drift: If Streamlit changes widget signatures (e.g., disabled support), the help view could fail. Mitigation: guard with try/except and fallback to static HTML.
- Confusion risk: Users might think the disabled controls are actionable. Mitigation: labels/captions clearly mark them as read-only.
- Data integrity: Interactive examples intentionally do not write; in future, if a "sandbox" mode is requested, ensure it writes to a dummy in-memory store only.

Technical Debt
- Help still duplicated across coordinator variants. Centralize content and renderers to prevent drift.
- Add a small test to assert the help view constructs without errors (widgets + components.html) on startup.

Next Steps (Proposed)
- Option to generate examples from the same column schema used in the real panel to guarantee labels match.
- Optional: add toggles for "Sample vs Live" where live examples bind to current patients but still blocked from logging/creating.
- Consider extracting these help renderers into `src/utils/help_components.py` for reuse.


## Session Log — 2025-11-19 — Sidebar Help Buttons Removed

Context
- Request: "get rid of the buttons on the left navigation menu now that we have them allocated with each dashboard"
- Scope: `Streamlit/app.py` sidebar; keep authentication/impersonation controls unchanged.

Changes Made
- Removed two duplicate bottom-of-sidebar Help navigation blocks containing:
  - `st.sidebar.button("Coordinator Help (same tab)")`
  - `st.sidebar.button("Provider Help (same tab)")`
  - `st.sidebar.button("Coordinator Patient Panel Help (same tab)")`
  - `st.sidebar.button("General Help Guide (same tab)")`
  - `st.sidebar.button("Help & User Guide (inline)")`
- Left a short comment indicating help is now embedded within each dashboard.
- Preserved `auth_module` sidebar elements (login/impersonation/logout) — not navigation.

Verification
- Started a Streamlit dev server on port 8505 and opened the preview (http://localhost:8505/).
- Visually confirmed the sidebar no longer displays Help buttons; dashboard-embedded Help remains accessible.
- No terminal errors observed during reload.

Risk & Gap Analysis
- Discoverability: Global Help shortcuts removed may reduce immediate discoverability outside dashboards.
  - Mitigation: Ensure each dashboard has prominent in-context Help; consider adding a top navbar Help link if needed.
- Residual references: Any lingering calls to `go_help(...)` triggered by sidebar widgets may now be dead paths.
  - Mitigation: prune unused code and add a lightweight UI construction test.
- Multi-role parity: Verify Provider and Coordinator dashboards both expose embedded Help consistently.

Technical Debt
- Help routing utilities remain in `app.py` (e.g., `go_help`); consider centralizing/removing if no longer needed.
- No automated check ensuring sidebar lacks navigation buttons; consider a UI linter/test.

Next Steps (Proposed)
- Audit for any remaining references to sidebar Help widgets and update internal links in dashboards.
- Optionally add a global Help link in a header/top bar if stakeholders request discoverability.
- Add a simple test to assert sidebar widget set excludes Help navigation.

---

## Session Log — 2025-11-20 — Provider Help: Tailored Interactive Views

Context
- Request: unique, role-tailored help views; start with coordinators and providers; ensure provider documentation is covered in detail.
- Scope: Provider dashboard in `src/dashboards/care_provider_dashboard_enhanced.py`.

Changes Made
1) Added reusable helper `render_provider_help_examples()` that renders read-only, live Streamlit widgets for:
   - My Patients panel: `st.dataframe` with real provider panel columns.
   - Onboarding Queue & Initial TV: `st.selectbox`, `st.date_input`, `st.text_area`, and a disabled `st.button`.
   - Phone Reviews entry: `st.selectbox`, `st.date_input`, `st.text_area`, and a disabled `st.button`.
   - Task Review summary: `st.dataframe` with a sample row.
2) Wired helper into all provider Help tabs:
   - Manager with onboarding queue.
   - Manager without onboarding queue (both help tab variants).
   - Regular provider without onboarding queue.
   - Added missing Help tab content for regular provider when onboarding queue exists.

Verification
- Dev server running at http://localhost:8506; preview opened and Help tabs display interactive examples without errors.
- No terminal errors observed on reload.

Risk & Gap Analysis
- Coverage drift: examples may diverge from the live forms if fields change. Mitigation: generate examples from source schema in future.
- Confusion risk: disabled controls may look actionable. Mitigation: captions and 'read-only' labeling retained.
- Missing coordinator parity: coordinator Help is interactive already; ensure alignment and avoid duplication.

Technical Debt
- Duplicated help tab construction across branches; should centralize help rendering.
- No automated test to assert help tabs construct across roles/states.

Next Steps (Proposed)
- Implement 'Sample vs Live' toggle allowing read-only binding to real patients (no writes).
- Add 'Sandbox mode' option writing to a dummy store for true interaction without data risk.
- Extract help renderers to `src/utils/help_components.py` for reuse across roles.


## Session Log — 2025-11-20 — Provider Help: Standalone HTML (Annotated)

Context
- Request: "Show the actual table/forms and, alongside them, explain what each column, color, dropdown, and control means. No Streamlit — pure HTML page first."
- Scope: Provider dashboard Help (standalone HTML preview), to be embedded later.

Changes Made
- Created `docs/help/provider/provider_help_annotated.html` — Bootstrap-based, static HTML showing:
  - Color Legend (Green/Yellow/Red/Blue) with definitions.
  - My Patients table with real headers and sample rows; row backgrounds mirror recency colors; blue badge for ≥200 minutes; right-side list explains each column.
  - Onboarding Queue & Initial TV form: visit type, date, notes, mental health checkboxes, code status, cognitive/functional, GOC, goals/concerns/specialists; inline help notes and right-side explainer list.
  - Phone Reviews form: task type, date, notes, disabled log button; help notes and explainer list.
  - Task Review: filters (date range, task multi-select, status) + disabled Export CSV; summary table; right-side explainer list.

Verification
- Launched local static server: `python -m http.server 8510 --directory docs/help/provider`.
- Preview URL: http://localhost:8510/provider_help_annotated.html — renders without browser errors.

Risk & Gap Analysis
- Drift risk: Text labels and columns may diverge from live Streamlit components.
  - Mitigation: Generate HTML content from shared schema; centralize labels.
- Discoverability: Standalone page not yet linked from the app.
  - Mitigation: Add dashboard Help tab link and embed after approval.
- Interaction: Controls are static; sandbox mode will be considered later for safe practice.

Technical Debt
- Help content now exists in both Streamlit and standalone HTML; needs centralization to avoid duplication.

Next Steps (Proposed)
- Confirm wording/structure; then embed HTML (or port to Streamlit components) in Provider Help tabs.
- Add optional "Sample vs Live" toggle and Sandbox mode when integrating.
- Extract help renderers into shared `src/utils/help_components.py`.


## Session Log — 2025-11-20 — Provider Help HTML updated per confirmed definitions

Context
- User confirmed the proposed field definitions (separate Visit Type vs Modality; GOC Status vocabulary; Subjective Risk Level scale; ER/Hospitalizations capture) and asked to proceed with integration in the standalone HTML help.

Changes Made
- Updated `docs/help/provider/provider_help_annotated.html` Onboarding section:
  - Split Visit Type (purpose) from Modality (Home vs Telehealth).
  - Added GOC Status dropdown with: New, Revise, Confirm, Established, Needs Review.
  - Added Subjective Risk Level dropdown with: Low, Moderate, High, Critical.
  - Added ER Visits/Hospitalizations (12 mo) numeric field plus optional details textarea.
  - Revised side-by-side help list to reflect the above and clarified purposes/options.
- Previewed at `http://localhost:8510/provider_help_annotated.html` using local static server; no browser errors.

Risk & Gap Analysis
- Vocab alignment risk: The standalone help now uses standardized terms; Streamlit views may still have legacy wording until updated (risk of drift).
- Mental health subtypes: Kept as Anxiety/Depression/PTSD/Substance Use to avoid over-specification; can be expanded later if needed.
- Data validation: HTML help is illustrative; real app must enforce required fields and valid states.

Technical Debt
- Help schemas are duplicated (HTML and Streamlit). Centralization is needed to prevent drift.
- Coordinator Help not yet updated with the same schema/options.

Next Steps (Proposed)
- Mirror these changes in Streamlit Provider Help tabs, using a shared schema.
- Implement Coordinator Help with identical pattern and shared definitions.
- Add Sample vs Live toggle and optional Sandbox mode in Help examples.
- Audit in-place navigation; ensure no sidebar Help buttons remain.
- Extract help renderers into shared `src/utils/help_components.py`.


## Session Log — 2025-11-20 — Coordinator Help: Standalone HTML (Annotated)

Context
- Request: "This is perfect — please do the same for coordinators, bypassing Streamlit for now. Show the web page view as an HTML file with elements and their corresponding help dialogues."
- Scope: Coordinator dashboard Help (standalone HTML preview), to be embedded later.

Changes Made
- Created `docs/help/coordinator/coordinator_help_annotated.html` — Bootstrap-based, static HTML showing:
  - Color Legend consistent with provider view (Green/Yellow/Red/Blue) with definitions.
  - My Patients (Coordinator) panel: realistic headers (Status, First/Last Name, Facility, Provider, Last Contact/Visit, Service Type, POC-A, POC-M, Minutes) and sample rows; right-side explainer for each column.
  - Workflow Manager (Quick Start): template selection, start date, patient/coordinator pickers; disabled Start Workflow; side-by-side help describing templates, prerequisites, and downstream effects.
  - Ongoing Workflows: table with Workflow, Patient, Coordinator, Started, Completed/Total Steps; right-side explainer for statuses and actions.
  - Task Entry: date, patient, task type, duration, notes; disabled Log Task; help notes on required fields, task taxonomy, and data validation.
  - Tooltips on key labels; inline help text mirroring coordinator responsibilities.

Verification
- Launched local static server: `python -m http.server 8511 --directory docs/help/coordinator`.
- Preview URL: http://localhost:8511/coordinator_help_annotated.html — renders without browser errors; terminal indicates server running.

Risk & Gap Analysis
- Drift risk: Labels/columns may diverge from live Streamlit coordinator views until we centralize schemas.
- Role boundaries: Confirm which items coordinators can update vs read-only (e.g., GOC updates, Code/Cognitive/Functional notes). We assumed coordinators can log tasks and manage workflows but not alter provider-only clinical statuses.
- Data validation: The HTML page is illustrative; real app must enforce required fields, valid durations, and permissible actions per role.

Technical Debt
- Help content duplicated across provider/coordinator and HTML/Streamlit. Centralize help schemas and renderers.
- No automated tests yet to catch mismatches between help docs and UI.

Next Steps (Proposed)
- Mirror coordinator help into Streamlit Help tab using a shared schema and renderers.
- Add "Sample vs Live" toggle and optional Sandbox mode for safe practice.
- Audit navigation to ensure help links point to embedded tabs; add top-level Help link if needed.
- Extract help components into `src/utils/help_components.py` to eliminate duplication.

---

Session Log — 2025-11-20 — Align patient name color highlighting with dashboard

Summary
- Implemented name-specific highlights for patient First/Last Name cells in both Provider and Coordinator annotated help pages to match the actual dashboard behavior.
- Added CSS classes: `.name-highlight`, `.name-green`, `.name-yellow`, `.name-red` and applied them to sample rows (Ada = Green, Ben = Yellow, Carla = Red).
- Retained existing row-level Green/Yellow/Red backgrounds for clarity; name-level highlighting now explicitly mirrors dashboard emphasis on the name.

Risk & Gap Analysis
- Visual consistency: If the live dashboard uses text-only color (no background) or a different shade, our pill-style highlight may diverge slightly. Confirm desired styling (text-only vs. badge).
- Accessibility: Ensure sufficient color contrast and non-color indicator (we kept row background and badges, but may need an icon or label for screen-readers in Streamlit).
- Theming drift: If the dashboard theme changes, standalone help pages may fall out of sync without a shared style source.

Technical Debt
- Duplicated color definitions exist in separate HTML files; no centralized style reference.
- No automated visual test to detect drift from the live dashboard.

Next Steps (Proposed)
- Confirm preferred highlight format: row background only, name text color only, or name pill/badge with background.
- Centralize color palette and status mapping (Green/Yellow/Red) in a shared CSS/JS module used by Streamlit and static help pages.
- Add a small legend next to names in help pages explaining the color meaning for new users (optional).
- Consider adding aria-labels or icons to denote status for accessibility.

---

Session Log — 2025-11-20 — Export annotated help pages to PDF

Summary
- Generated PDFs for Provider and Coordinator annotated help pages using headless Chromium (Edge/Chrome).
- Saved to outputs\reports\provider_help_annotated.pdf and outputs\reports\coordinator_help_annotated.pdf for easy emailing to staff.

Risk & Gap Analysis
- Print CSS: The static pages are not yet optimized with a dedicated print stylesheet. Margins, page breaks, and header/footer might differ from expectations.
- Color fidelity: Name highlights and row backgrounds print in color; confirm if grayscale is desired for some recipients.
- Page length: Long sections may split awkwardly without explicit print-break hints.

Technical Debt
- No centralized print theme or print-specific CSS across help pages.
- Manual PDF generation; no scripted CI task or UI button to produce PDFs.

Next Steps (Proposed)
- Add print.css for consistent margins, page breaks, and optional header/footer with logo and date.
- Provide a “Download PDF” action directly on help pages (served PDFs or on-demand generation).
- Confirm paper size (Letter vs A4), margins, and whether to include page numbers.
- If needed, add grayscale-friendly palette to ensure legibility when printed in B/W.

---

Session Log — 2025-11-20 — Enforce US Letter (8.5x11) print layout and re-export PDFs

Summary
- Added print CSS to both Provider and Coordinator annotated help pages to enforce US Letter (8.5x11) and preserve color highlights.
- Re-exported PDFs: outputs\reports\provider_help_annotated_letter.pdf and outputs\reports\coordinator_help_annotated_letter.pdf.

Details
- CSS: @media print with @page { size: Letter; margin: 0.5in; } and print-color-adjust to preserve color.
- Avoided awkward breaks with page-break-inside: avoid on major containers.

Risk & Gap Analysis
- Margins and pagination: 0.5" margins assumed; confirm if 1" is preferred. Page numbers not included.
- Cross-browser rendering: Headless Edge/Chrome adhere to @page, but minor layout shifts are possible.

Next Steps (Proposed)
- Confirm margin preference and whether to include page numbers or header/footer (logo, date).
- If desired, add a print.css for consistent styling across all help pages.

---

Session Log — 2025-11-20 — Improve on-screen readability: full-width layout; remove view scale controls

Summary
- Switched annotated help pages from container to container-fluid to maximize available width.
- Kept full-width container-fluid. Removed the view scale controls and JS per user request, and reset default scaling to 100% to avoid confusion.

Risk & Gap Analysis
- Scaling reduces font sizes and paddings; validate readability across common displays. May need per-breakpoint tuning.
- Previously proposed scaling affected all elements uniformly. With default 100% restored and no visible scale controls, verify headings, badges, and tables still read well side-by-side at typical resolutions.
- Does not change the underlying grid; for very narrow screens, stacking still occurs by design.

Next Steps (Proposed)
- If desired, add per-section flex wrappers to force side-by-side for specific sections at ≥lg breakpoints.
- Drop the persisted scale preference idea (localStorage) to avoid confusion; consider per-section layout tuning instead.
- Confirm preferred default scale and whether 80% is acceptable for staff on smaller displays.

## Session Log — 2025-11-20 — Unified patient_id normalization applied in sheets views and comparison script; parse errors fixed

Context
- Goal: Adopt unified patient_id normalization across pipelines (staging and sheets) and validate via comparison reports.
- Files: `scripts/define_sheets_normalized_views.sql`, `scripts/compare_production_vs_sheets_using_views.sql`.

Changes Made
1) Updated `define_sheets_normalized_views.sql` to enforce the unified normalization rule in these views:
   - `sheets.V_PROVIDER_TASKS_NORM`
   - `sheets.V_COORDINATOR_TASKS_NORM`
   - `sheets.V_PATIENTS_EQUIV`
   Rule: Strip prefixes `ZEN-`, `PM-`, `ZMN-`, `BlessedCare-`/`BleessedCare-` (case variants), `3PR-` and `3PR -`; normalize commas to spaces; trim and case-normalize as appropriate.
2) Updated `compare_production_vs_sheets_using_views.sql` to apply the same normalization consistently in all CTEs:
   - Provider comparisons: `sheets_provider`, `staging_provider` (including `patient_name_raw` normalization where used).
   - Coordinator comparisons: `sheets_coord`, `staging_coord` (and date filter `>= date('now','-3 months')`).
   - Patient visits comparisons: both blocks `sheets_visits`, `staging_visits` including date normalization for 8-char formats.
3) Fixed multiple SQL parse errors by simplifying and re-parenthesizing REPLACE chains, using `TRIM(REPLACE(patient_id, ',', ' '))` as the inner normalization term and then chaining REPLACEs outward.
4) Executed `define_sheets_normalized_views.sql` against `sheets_data.db` to (re)create normalized views.
5) Executed `compare_production_vs_sheets_using_views.sql` against `production.db`; confirmed successful run (exit code 0). CSV mismatch reports were generated in `outputs/reports`.

Verification
- `sqlite3 .\\production.db ".read scripts\\compare_production_vs_sheets_using_views.sql"` exited with code 0 (no parse errors).
- Reports written under `outputs/reports/` for:
  - provider_tasks_rows_missing_in_staging_views.csv
  - provider_tasks_rows_missing_in_sheets_views.csv
  - coordinator_tasks_rows_missing_in_staging_views.csv
  - coordinator_tasks_rows_missing_in_sheets_views.csv
  - patient_visits_rows_missing_in_staging_views.csv
  - patient_visits_rows_missing_in_sheets_views.csv

Risk & Gap Analysis
- Over-stripping risk: Prefix removal might collide with legitimate hyphenated surnames or IDs containing similar tokens.
  - Mitigation: Use conservative early-short-token rule and restrict removal to known prefixes at start of strings; maintain comma-to-space normalization only, not blanket hyphen removal.
- Case normalization: We used `UPPER` where prior code used mixed case; verify downstream joins are case-insensitive as expected.
- Source drift: Staging SQL files (`src/sql/*.sql`) still need refactoring to use the shared rule; differences can cause mismatch noise.
- Date normalization: Patient visits include an 8-char date format transform; ensure no unintended transforms for other formats.

Technical Debt
- Normalization logic duplicated across multiple scripts (sheets views, compare script, staging SQL). We should centralize in a reusable SQL snippet or documented macro pattern.
- Lack of unit tests for normalization; consider adding sample cases in `test_patient_id_fix.py` and SQL-based checks.

Next Steps (Proposed)
- Refactor and apply the unified normalization rule in:
  - `src/sql/staging_provider_tasks.sql`
  - `src/sql/staging_coordinator_tasks.sql`
  - `src/sql/staging_alignment_checks.sql`
  - `src/sql/create_patient_visits.sql`
  - `src/sql/populate_patients.sql`
- Re-run alignment reports:
  - `scripts/compare_tables_normalized.sql`
  - `src/sql/staging_alignment_checks.sql`
  - Capture mismatch counts and potential collisions for review.
- Document edge cases explicitly in this living doc: hyphenated surnames, case handling, prefix variants.
- Consider a shared helper or view for normalization to avoid duplication and reduce parse error risk in future edits.

Session Log — 2025-11-20 (afternoon)
Scope: Apply shared patient_id normalization in staging reports and visits; re-run comparisons; document counts and risks.

Changes Implemented
- Updated `src/sql/staging_alignment_checks.sql` to use the unified patient_id normalization across all relevant CTEs and sections (date mismatches, service mismatches, tasks without panel, panel without tasks, provider name alignment, coordinator vs provider panel).
- Updated `src/sql/create_patient_visits.sql` to normalize patient_name consistently and use the normalized value as patient_id; adjusted GROUP BY and LEFT JOIN subqueries to use the shared normalization chain.
- Updated `src/sql/populate_patients.sql` to standardize patient_id derivation from the normalized `LAST FIRST DOB` field and aligned `last_first_dob` normalization with the shared rule.
- Fixed `scripts/compare_tables_normalized.sql` (commented out missing duplicate column `[Patient Last, First DOB.1]` and restored proper statement termination) to allow execution in our environment.

Verification
- Executed `src/sql/staging_alignment_checks.sql` against `production.db` successfully; new report counts:
  - staging_panel_vs_tasks_date_mismatches.csv: 1
  - staging_panel_vs_tasks_service_mismatches.csv: 1
  - staging_tasks_without_panel.csv: 756
  - staging_panel_without_tasks.csv: 519
  - patient_id_norm_collisions_views.csv: 5
- Executed `scripts/compare_tables_normalized.sql` successfully after fixes; observed:
  - Cleaned counts per source: SOURCE_COORDINATOR_TASKS_HISTORY=165,065; SOURCE_PATIENT_DATA=1,037; SOURCE_PROVIDER_TASKS_HISTORY=5,109
  - Totals: unique_name_dob≈3,107; total_rows≈171,211
  - Sample of cross-source duplicates printed to stdout (saved in terminal logs).
- Unit tests:
  - `test_patient_id_normalization.py` passed curated cases (5/5) and ran a smoke test against `SOURCE_PATIENT_DATA` when present.
  - `scripts/normalization_tests.sql` reported mismatch_count = 0 for the curated SQL corpus.


Risk & Gap Analysis (additional)
- Column drift: `SOURCE_PROVIDER_TASKS_HISTORY` may not always have duplicate columns (e.g., `.1`); our comparison script now guards by commenting out that union, but a more robust solution would programmatically detect columns via PRAGMA and construct dynamic SQL.
- Over-stripping variants: We currently remove `BlessedCare/BleessedCare` dash and space variants and short tokens like `ZEN`, `PM`, `ZMN`, `3PR`. Confirm we are not stripping legitimate name fragments that could appear at the start (e.g., surnames beginning with `Zen-`).
- Consistency across pipelines: Ensure downstream views/scripts that join on `patient_id` or `last_first_dob` adopt this exact normalization to prevent subtle mismatches.

Technical Debt (additional)
- Duplicated normalization chains across several SQL files increases parse error risk (parentheses balance) and maintenance overhead.
- No unitized test corpus for patient_id normalization edge cases (prefix variants, hyphenated surnames, multi-space collapse). Suggest adding a small canonical table of tricky samples and a check script.

Next Steps
- Extend refactor to remaining staging SQLs (`staging_provider_tasks.sql`, `staging_coordinator_tasks.sql`) if/where patient_id normalization is introduced.
- Re-run full view-based comparisons (`scripts/compare_production_vs_sheets_using_views.sql`) and snapshot counts; compare against prior baselines.
- Add a small helper SQL file (`src/sql/patient_id_normalization_standard.sql`) or use `patient_id_normalization_function.sql` as the documented snippet to reduce duplication; consider a view that exposes `normalized_patient_id(field)` via consistent expression.
- Document explicit edge cases and decisions (case handling, hyphen collapsing rules, start-of-string only prefix stripping) in this living doc.

### Session Log — 2025-11-21 — Canonical patient_id transform & verifier parameterization

Context
- Goal: Transform source/staging data to match production by trimming/splitting name + DOB to create patient_id = "LASTNAME FIRSTNAME MM/DD/YYYY".
- Defensive collaboration: We are fixing the canonical rules and aligning verification to staging first, then measuring linkage to production.

Changes Implemented
- Updated src/sql/staging_provider_tasks.sql:
  - Keep comma for splitting Last vs First; strip vendor/facility prefixes without removing the comma.
  - Uppercase names; remove internal spaces; preserve hyphens.
  - Extract DOB from the end; convert 2-digit years to 20YY; output patient_id as "LASTNAME FIRSTNAME MM/DD/YYYY".
  - Preserve existing date normalization for activity_date and year_month; maintain indexes.
- Updated scripts/verify_normalization_linkage.py:
  - Parameterized to use --staging-db (default sheets_data.db) and ATTACH --prod-db (default production.db) as prod.
  - Computes linkage rates for provider/coordinator against prod.patients; writes CSVs to scripts/outputs/reports.
  - Appends a concise summary to PROJECT_LIVING_DOCUMENT.md; avoids terminal prints by default.

Risk & Gap Analysis
- DOB century ambiguity: 2-digit years default to 20YY; elderly patients may be mis-expanded. Mitigation: consider inferring century from DOS/year_month or age if available.
- Missing comma or DOB: Rows lacking expected delimiters yield NULL patient_id. Mitigation: collect unmatched samples; evaluate a secondary parser (space-delimited) with strict safeguards.
- Coordinator normalization: Still a heuristic REPLACE chain (no canonical parser). Mitigation: implement coordinator canonical parse mirroring provider rules next.
- Unicode/hidden whitespace: Collapse not yet applied. Mitigation: add a shared utility to normalize Unicode whitespace across imports before parsing.
- Collision risk: Multiple distinct raw names mapping to the same canonical patient_id. Mitigation: audit collisions; if necessary, add tie-break metadata or human review while keeping canonical format stable.

Acceptance Criteria (for this phase)
- Canonical patient_id: EXACTLY "LASTNAME FIRSTNAME MM/DD/YYYY" (names uppercase; internal spaces removed; hyphens preserved).
- Provider linkage rate ≥ 90% vs prod.patients; Coordinator linkage rate ≥ 85%.
- No regression in activity_date and year_month generation in staging.
- All verification outputs written to scripts/outputs/reports and summarized ONLY here (no terminal spam).

Next Steps
- Rebuild staging via scripts/4a-transform.ps1 and scripts/4b-transform.ps1.
- Run scripts/verify_normalization_linkage.py with defaults (staging=sheets_data.db; prod=production.db).
- Append linkage counts, unmatched samples, and collision summaries to this document.
- Implement Unicode whitespace collapse and a centralized Python normalization (names/DOB) used by both SQL transforms and verification.
- Extend canonical parsing to coordinator data to replace the heuristic REPLACE chains.

Ownership & Review
- Implementer: AI (Safety Engineer & Skeptical Implementer).
- Reviewer: User (Strategy Lead). Please review acceptance criteria and confirm proceeding to staging rebuild + verification.


### Session Log — 2025-11-21 — Recent-only import focus (post-last-task) and ZMO new patients

Scope & Intent
- User direction: Ignore old data; focus on tasks AFTER the last recorded task date in production.db.
- Include new patients added in the ZMO file and ~2+ months of recent task data.

Plan (Defensive & Incremental)
1) Compute cutoff_last_task_date = MAX(activity_date) across provider/coordinator task tables in production.db.
   - Mitigation: Consider a small buffer (e.g., 14 days) to catch backdated entries.
2) Confirm ZMO source(s): file path(s), sheet names, and column schema for patient name, DOB, activity_date, task_type, notes.
3) Update scripts/3_import_to_database.ps1 to accept StartDate and filter rows with activity_date >= cutoff_last_task_date (or cutoff - buffer).
4) Import the ZMO patients/tasks into sheets_data.db staging.
5) Run transforms (4a/4b) to compute canonical patient_id (LASTNAME FIRSTNAME MM/DD/YYYY); preserve hyphens; uppercase names; remove internal spaces.
6) Verify staging linkage against production (verify_normalization_linkage.py with prod attached): record linkage %, collisions, and unmatched samples ONLY in this document.
7) If acceptance criteria met, merge validated recent tasks and new patients into production.db; otherwise, produce an unmatched sample report for review.

Risks & Gaps
- Backdated or corrected tasks may precede cutoff; using a buffer reduces miss risk.
- DOB format variance (YY vs YYYY) may cause mis-expansion; elderly patient century handling needed.
- ZMO schema unknowns: We must confirm column names and delimiter usage (commas in Last, First DOB). 
- Potential duplicate patients in ZMO; collisions in canonical patient_id must be audited.
- Time zone and date parsing: Ensure activity_date normalization to YYYY-MM-DD in staging.

Acceptance Criteria
- Cutoff computed as MAX(activity_date) across all task sources in production.db; buffer decision explicitly documented.
- ZMO import constrained to activity_date >= cutoff (or cutoff - buffer), fully accounted in reports.
- Canonical patient_id generated for ≥90% of recent tasks; linkage ≥90% provider and ≥85% coordinator where matching is expected.
- All outputs written to scripts/outputs/reports; summaries appended ONLY here.

Required Inputs (from User)
- ZMO file path(s) and sheet names to import.
- Confirmation of task tables to use for cutoff (e.g., SOURCE_PROVIDER_TASKS_HISTORY, SOURCE_COORDINATOR_TASKS_HISTORY, or staging_* equivalents), and the date column name(s).
- Decision on buffer window (0 vs 14 days) for backdated entries.

Next Actions (pending approval)
- Implement StartDate filter in 3_import_to_database.ps1.
- Compute cutoff_last_task_date and proceed with ZMO recent-only import into staging.
- Run transforms + verifier and append results here.

## Session Log — Recent-only Import Cutover (Strict)
Date: 2025-11-21
Owner: AI Assistant (Implementation), User (Reviewer)

Objective
- Implement recent-only data import into staging using strict StartDate = 2025-09-26 (no buffer), then rebuild staging transforms and run verification.

Decisions & Rationale
- Strict StartDate filter applied post-import within SQLite for reliability and performance.
- Coordinator source filtered by "Date Only"; Provider source filtered by "DOS"; both normalized to YYYY-MM-DD before comparison.
- Patient import (ZMO_Main.csv) remains unchanged to avoid accidental deletions of patient records.

Planned Steps (this session)
1. Run scripts/3_import_to_database.ps1 with -DatabasePath "..\\sheets_data.db" -StartDate "2025-09-26" to import and strictly filter recent rows.
2. Run 4a-transform.ps1 and 4b-transform.ps1 to rebuild staging patients, assignments, panel, and tasks.
3. Run scripts/verify_normalization_linkage.py with staging attached to production to validate canonical patient_id alignment and linkage.
4. Append results (row counts, anomalies, acceptance status) to this document.

Risk & Gap Analysis
- Backdated or corrected entries with dates < 2025-09-26 will be excluded by design (strict mode).
- Malformed or missing date values will normalize to NULL and be pruned by the filter; confirm if we need to retain NULL-dated rows in future.
- Variations in CSV date formats (MM/DD/YYYY vs MM/DD/YY) covered by normalization; additional edge cases (e.g., textual months) would be dropped.
- Staging transforms depend on activity_date indexes; ensure filtering does not break downstream queries.

Acceptance Criteria
- Only rows with normalized date >= 2025-09-26 exist in SOURCE_* task tables (combined and monthly variants where imported).
- 4a and 4b transforms succeed without errors; staging_* tables and indexes created.
- Verification script reports expected linkage rates and flags no critical mismatches.
- This Session Log updated with outcomes and any noted technical debt.

User Inputs Confirmed
- StartDate provided and confirmed by user: 2025-09-26. Strict, no buffer.

Next Actions (execution starts now)
- Proceed with import, transforms, and verification.

## Session Log — 2025-11-20 — Provider Help: Standalone HTML (Annotated)

Context
- Request: "Show the actual table/forms and, alongside them, explain what each column, color, dropdown, and control means. No Streamlit — pure HTML page first."
- Scope: Provider dashboard Help (standalone HTML preview), to be embedded later.

Changes Made
- Created `docs/help/provider/provider_help_annotated.html` — Bootstrap-based, static HTML showing:
  - Color Legend (Green/Yellow/Red/Blue) with definitions.
  - My Patients table with real headers and sample rows; row backgrounds mirror recency colors; blue badge for ≥200 minutes; right-side list explains each column.
  - Onboarding Queue & Initial TV form: visit type, date, notes, mental health checkboxes, code status, cognitive/functional, GOC, goals/concerns/specialists; inline help notes and right-side explainer list.
  - Phone Reviews form: task type, date, notes, disabled log button; help notes and explainer list.
  - Task Review: filters (date range, task multi-select, status) + disabled Export CSV; summary table; right-side explainer list.

Verification
- Launched local static server: `python -m http.server 8510 --directory docs/help/provider`.
- Preview URL: http://localhost:8510/provider_help_annotated.html — renders without browser errors.

Risk & Gap Analysis
- Drift risk: Text labels and columns may diverge from live Streamlit components.
  - Mitigation: Generate HTML content from shared schema; centralize labels.
- Discoverability: Standalone page not yet linked from the app.
  - Mitigation: Add dashboard Help tab link and embed after approval.
- Interaction: Controls are static; sandbox mode will be considered later for safe practice.

Technical Debt
- Help content now exists in both Streamlit and standalone HTML; needs centralization to avoid duplication.

Next Steps (Proposed)
- Confirm wording/structure; then embed HTML (or port to Streamlit components) in Provider Help tabs.
- Add optional "Sample vs Live" toggle and Sandbox mode when integrating.
- Extract help renderers into shared `src/utils/help_components.py`.


## Session Log — 2025-11-20 — Provider Help HTML updated per confirmed definitions

Context
- User confirmed the proposed field definitions (separate Visit Type vs Modality; GOC Status vocabulary; Subjective Risk Level scale; ER/Hospitalizations capture) and asked to proceed with integration in the standalone HTML help.

Changes Made
- Updated `docs/help/provider/provider_help_annotated.html` Onboarding section:
  - Split Visit Type (purpose) from Modality (Home vs Telehealth).
  - Added GOC Status dropdown with: New, Revise, Confirm, Established, Needs Review.
  - Added Subjective Risk Level dropdown with: Low, Moderate, High, Critical.
  - Added ER Visits/Hospitalizations (12 mo) numeric field plus optional details textarea.
  - Revised side-by-side help list to reflect the above and clarified purposes/options.
- Previewed at `http://localhost:8510/provider_help_annotated.html` using local static server; no browser errors.

Risk & Gap Analysis
- Vocab alignment risk: The standalone help now uses standardized terms; Streamlit views may still have legacy wording until updated (risk of drift).
- Mental health subtypes: Kept as Anxiety/Depression/PTSD/Substance Use to avoid over-specification; can be expanded later if needed.
- Data validation: HTML help is illustrative; real app must enforce required fields and valid states.

Technical Debt
- Help schemas are duplicated (HTML and Streamlit). Centralization is needed to prevent drift.
- Coordinator Help not yet updated with the same schema/options.

Next Steps (Proposed)
- Mirror these changes in Streamlit Provider Help tabs, using a shared schema.
- Implement Coordinator Help with identical pattern and shared definitions.
- Add Sample vs Live toggle and optional Sandbox mode in Help examples.
- Audit in-place navigation; ensure no sidebar Help buttons remain.
- Extract help renderers into shared `src/utils/help_components.py`.


## Session Log — 2025-11-20 — Coordinator Help: Standalone HTML (Annotated)

Context
- Request: "This is perfect — please do the same for coordinators, bypassing Streamlit for now. Show the web page view as an HTML file with elements and their corresponding help dialogues."
- Scope: Coordinator dashboard Help (standalone HTML preview), to be embedded later.

Changes Made
- Created `docs/help/coordinator/coordinator_help_annotated.html` — Bootstrap-based, static HTML showing:
  - Color Legend consistent with provider view (Green/Yellow/Red/Blue) with definitions.
  - My Patients (Coordinator) panel: realistic headers (Status, First/Last Name, Facility, Provider, Last Contact/Visit, Service Type, POC-A, POC-M, Minutes) and sample rows; right-side explainer for each column.
  - Workflow Manager (Quick Start): template selection, start date, patient/coordinator pickers; disabled Start Workflow; side-by-side help describing templates, prerequisites, and downstream effects.
  - Ongoing Workflows: table with Workflow, Patient, Coordinator, Started, Completed/Total Steps; right-side explainer for statuses and actions.
  - Task Entry: date, patient, task type, duration, notes; disabled Log Task; help notes on required fields, task taxonomy, and data validation.
  - Tooltips on key labels; inline help text mirroring coordinator responsibilities.

Verification
- Launched local static server: `python -m http.server 8511 --directory docs/help/coordinator`.
- Preview URL: http://localhost:8511/coordinator_help_annotated.html — renders without browser errors; terminal indicates server running.

Risk & Gap Analysis
- Drift risk: Labels/columns may diverge from live Streamlit coordinator views until we centralize schemas.
- Role boundaries: Confirm which items coordinators can update vs read-only (e.g., GOC updates, Code/Cognitive/Functional notes). We assumed coordinators can log tasks and manage workflows but not alter provider-only clinical statuses.
- Data validation: The HTML page is illustrative; real app must enforce required fields, valid durations, and permissible actions per role.

Technical Debt
- Help content duplicated across provider/coordinator and HTML/Streamlit. Centralize help schemas and renderers.
- No automated tests yet to catch mismatches between help docs and UI.

Next Steps (Proposed)
- Mirror coordinator help into Streamlit Help tab using a shared schema and renderers.
- Add "Sample vs Live" toggle and optional Sandbox mode for safe practice.
- Audit navigation to ensure help links point to embedded tabs; add top-level Help link if needed.
- Extract help components into `src/utils/help_components.py` to eliminate duplication.

---

Session Log — 2025-11-20 — Align patient name color highlighting with dashboard

Summary
- Implemented name-specific highlights for patient First/Last Name cells in both Provider and Coordinator annotated help pages to match the actual dashboard behavior.
- Added CSS classes: `.name-highlight`, `.name-green`, `.name-yellow`, `.name-red` and applied them to sample rows (Ada = Green, Ben = Yellow, Carla = Red).
- Retained existing row-level Green/Yellow/Red backgrounds for clarity; name-level highlighting now explicitly mirrors dashboard emphasis on the name.

Risk & Gap Analysis
- Visual consistency: If the live dashboard uses text-only color (no background) or a different shade, our pill-style highlight may diverge slightly. Confirm desired styling (text-only vs. badge).
- Accessibility: Ensure sufficient color contrast and non-color indicator (we kept row background and badges, but may need an icon or label for screen-readers in Streamlit).
- Theming drift: If the dashboard theme changes, standalone help pages may fall out of sync without a shared style source.

Technical Debt
- Duplicated color definitions exist in separate HTML files; no centralized style reference.
- No automated visual test to detect drift from the live dashboard.

Next Steps (Proposed)
- Confirm preferred highlight format: row background only, name text color only, or name pill/badge with background.
- Centralize color palette and status mapping (Green/Yellow/Red) in a shared CSS/JS module used by Streamlit and static help pages.
- Add a small legend next to names in help pages explaining the color meaning for new users (optional).
- Consider adding aria-labels or icons to denote status for accessibility.

---

Session Log — 2025-11-20 — Export annotated help pages to PDF

Summary
- Generated PDFs for Provider and Coordinator annotated help pages using headless Chromium (Edge/Chrome).
- Saved to outputs\reports\provider_help_annotated.pdf and outputs\reports\coordinator_help_annotated.pdf for easy emailing to staff.

Risk & Gap Analysis
- Print CSS: The static pages are not yet optimized with a dedicated print stylesheet. Margins, page breaks, and header/footer might differ from expectations.
- Color fidelity: Name highlights and row backgrounds print in color; confirm if grayscale is desired for some recipients.
- Page length: Long sections may split awkwardly without explicit print-break hints.

Technical Debt
- No centralized print theme or print-specific CSS across help pages.
- Manual PDF generation; no scripted CI task or UI button to produce PDFs.

Next Steps (Proposed)
- Add print.css for consistent margins, page breaks, and optional header/footer with logo and date.
- Provide a “Download PDF” action directly on help pages (served PDFs or on-demand generation).
- Confirm paper size (Letter vs A4), margins, and whether to include page numbers.
- If needed, add grayscale-friendly palette to ensure legibility when printed in B/W.

---

Session Log — 2025-11-20 — Enforce US Letter (8.5x11) print layout and re-export PDFs

Summary
- Added print CSS to both Provider and Coordinator annotated help pages to enforce US Letter (8.5x11) and preserve color highlights.
- Re-exported PDFs: outputs\reports\provider_help_annotated_letter.pdf and outputs\reports\coordinator_help_annotated_letter.pdf.

Details
- CSS: @media print with @page { size: Letter; margin: 0.5in; } and print-color-adjust to preserve color.
- Avoided awkward breaks with page-break-inside: avoid on major containers.

Risk & Gap Analysis
- Margins and pagination: 0.5" margins assumed; confirm if 1" is preferred. Page numbers not included.
- Cross-browser rendering: Headless Edge/Chrome adhere to @page, but minor layout shifts are possible.

Next Steps (Proposed)
- Confirm margin preference and whether to include page numbers or header/footer (logo, date).
- If desired, add a print.css for consistent styling across all help pages.

---

Session Log — 2025-11-20 — Improve on-screen readability: full-width layout; remove view scale controls

Summary
- Switched annotated help pages from container to container-fluid to maximize available width.
- Kept full-width container-fluid. Removed the view scale controls and JS per user request, and reset default scaling to 100% to avoid confusion.

Risk & Gap Analysis
- Scaling reduces font sizes and paddings; validate readability across common displays. May need per-breakpoint tuning.
- Previously proposed scaling affected all elements uniformly. With default 100% restored and no visible scale controls, verify headings, badges, and tables still read well side-by-side at typical resolutions.
- Does not change the underlying grid; for very narrow screens, stacking still occurs by design.

Next Steps (Proposed)
- If desired, add per-section flex wrappers to force side-by-side for specific sections at ≥lg breakpoints.
- Drop the persisted scale preference idea (localStorage) to avoid confusion; consider per-section layout tuning instead.
- Confirm preferred default scale and whether 80% is acceptable for staff on smaller displays.

## Session Log — 2025-11-20 — Unified patient_id normalization applied in sheets views and comparison script; parse errors fixed

Context
- Goal: Adopt unified patient_id normalization across pipelines (staging and sheets) and validate via comparison reports.
- Files: `scripts/define_sheets_normalized_views.sql`, `scripts/compare_production_vs_sheets_using_views.sql`.

Changes Made
1) Updated `define_sheets_normalized_views.sql` to enforce the unified normalization rule in these views:
   - `sheets.V_PROVIDER_TASKS_NORM`
   - `sheets.V_COORDINATOR_TASKS_NORM`
   - `sheets.V_PATIENTS_EQUIV`
   Rule: Strip prefixes `ZEN-`, `PM-`, `ZMN-`, `BlessedCare-`/`BleessedCare-` (case variants), `3PR-` and `3PR -`; normalize commas to spaces; trim and case-normalize as appropriate.
2) Updated `compare_production_vs_sheets_using_views.sql` to apply the same normalization consistently in all CTEs:
   - Provider comparisons: `sheets_provider`, `staging_provider` (including `patient_name_raw` normalization where used).
   - Coordinator comparisons: `sheets_coord`, `staging_coord` (and date filter `>= date('now','-3 months')`).
   - Patient visits comparisons: both blocks `sheets_visits`, `staging_visits` including date normalization for 8-char formats.
3) Fixed multiple SQL parse errors by simplifying and re-parenthesizing REPLACE chains, using `TRIM(REPLACE(patient_id, ',', ' '))` as the inner normalization term and then chaining REPLACEs outward.
4) Executed `define_sheets_normalized_views.sql` against `sheets_data.db` to (re)create normalized views.
5) Executed `compare_production_vs_sheets_using_views.sql` against `production.db`; confirmed successful run (exit code 0). CSV mismatch reports were generated in `outputs/reports`.

Verification
- `sqlite3 .\\production.db ".read scripts\\compare_production_vs_sheets_using_views.sql"` exited with code 0 (no parse errors).
- Reports written under `outputs/reports/` for:
  - provider_tasks_rows_missing_in_staging_views.csv
  - provider_tasks_rows_missing_in_sheets_views.csv
  - coordinator_tasks_rows_missing_in_staging_views.csv
  - coordinator_tasks_rows_missing_in_sheets_views.csv
  - patient_visits_rows_missing_in_staging_views.csv
  - patient_visits_rows_missing_in_sheets_views.csv

Risk & Gap Analysis
- Over-stripping risk: Prefix removal might collide with legitimate hyphenated surnames or IDs containing similar tokens.
  - Mitigation: Use conservative early-short-token rule and restrict removal to known prefixes at start of strings; maintain comma-to-space normalization only, not blanket hyphen removal.
- Case normalization: We used `UPPER` where prior code used mixed case; verify downstream joins are case-insensitive as expected.
- Source drift: Staging SQL files (`src/sql/*.sql`) still need refactoring to use the shared rule; differences can cause mismatch noise.
- Date normalization: Patient visits include an 8-char date format transform; ensure no unintended transforms for other formats.

Technical Debt
- Normalization logic duplicated across multiple scripts (sheets views, compare script, staging SQL). We should centralize in a reusable SQL snippet or documented macro pattern.
- Lack of unit tests for normalization; consider adding sample cases in `test_patient_id_fix.py` and SQL-based checks.

Next Steps (Proposed)
- Refactor and apply the unified normalization rule in:
  - `src/sql/staging_provider_tasks.sql`
  - `src/sql/staging_coordinator_tasks.sql`
  - `src/sql/staging_alignment_checks.sql`
  - `src/sql/create_patient_visits.sql`
  - `src/sql/populate_patients.sql`
- Re-run alignment reports:
  - `scripts/compare_tables_normalized.sql`
  - `src/sql/staging_alignment_checks.sql`
  - Capture mismatch counts and potential collisions for review.
- Document edge cases explicitly in this living doc: hyphenated surnames, case handling, prefix variants.
- Consider a shared helper or view for normalization to avoid duplication and reduce parse error risk in future edits.

Session Log — 2025-11-20 (afternoon)
Scope: Apply shared patient_id normalization in staging reports and visits; re-run comparisons; document counts and risks.

Changes Implemented
- Updated `src/sql/staging_alignment_checks.sql` to use the unified patient_id normalization across all relevant CTEs and sections (date mismatches, service mismatches, tasks without panel, panel without tasks, provider name alignment, coordinator vs provider panel).
- Updated `src/sql/create_patient_visits.sql` to normalize patient_name consistently and use the normalized value as patient_id; adjusted GROUP BY and LEFT JOIN subqueries to use the shared normalization chain.
- Updated `src/sql/populate_patients.sql` to standardize patient_id derivation from the normalized `LAST FIRST DOB` field and aligned `last_first_dob` normalization with the shared rule.
- Fixed `scripts/compare_tables_normalized.sql` (commented out missing duplicate column `[Patient Last, First DOB.1]` and restored proper statement termination) to allow execution in our environment.

Verification
- Executed `src/sql/staging_alignment_checks.sql` against `production.db` successfully; new report counts:
  - staging_panel_vs_tasks_date_mismatches.csv: 1
  - staging_panel_vs_tasks_service_mismatches.csv: 1
  - staging_tasks_without_panel.csv: 756
  - staging_panel_without_tasks.csv: 519
  - patient_id_norm_collisions_views.csv: 5
- Executed `scripts/compare_tables_normalized.sql` successfully after fixes; observed:
  - Cleaned counts per source: SOURCE_COORDINATOR_TASKS_HISTORY=165,065; SOURCE_PATIENT_DATA=1,037; SOURCE_PROVIDER_TASKS_HISTORY=5,109
  - Totals: unique_name_dob≈3,107; total_rows≈171,211
  - Sample of cross-source duplicates printed to stdout (saved in terminal logs).
- Unit tests:
  - `test_patient_id_normalization.py` passed curated cases (5/5) and ran a smoke test against `SOURCE_PATIENT_DATA` when present.
  - `scripts/normalization_tests.sql` reported mismatch_count = 0 for the curated SQL corpus.


Risk & Gap Analysis (additional)
- Column drift: `SOURCE_PROVIDER_TASKS_HISTORY` may not always have duplicate columns (e.g., `.1`); our comparison script now guards by commenting out that union, but a more robust solution would programmatically detect columns via PRAGMA and construct dynamic SQL.
- Over-stripping variants: We currently remove `BlessedCare/BleessedCare` dash and space variants and short tokens like `ZEN`, `PM`, `ZMN`, `3PR`. Confirm we are not stripping legitimate name fragments that could appear at the start (e.g., surnames beginning with `Zen-`).
- Consistency across pipelines: Ensure downstream views/scripts that join on `patient_id` or `last_first_dob` adopt this exact normalization to prevent subtle mismatches.

Technical Debt (additional)
- Duplicated normalization chains across several SQL files increases parse error risk (parentheses balance) and maintenance overhead.
- No unitized test corpus for patient_id normalization edge cases (prefix variants, hyphenated surnames, multi-space collapse). Suggest adding a small canonical table of tricky samples and a check script.

Next Steps
- Extend refactor to remaining staging SQLs (`staging_provider_tasks.sql`, `staging_coordinator_tasks.sql`) if/where patient_id normalization is introduced.
- Re-run full view-based comparisons (`scripts/compare_production_vs_sheets_using_views.sql`) and snapshot counts; compare against prior baselines.
- Add a small helper SQL file (`src/sql/patient_id_normalization_standard.sql`) or use `patient_id_normalization_function.sql` as the documented snippet to reduce duplication; consider a view that exposes `normalized_patient_id(field)` via consistent expression.
- Document explicit edge cases and decisions (case handling, hyphen collapsing rules, start-of-string only prefix stripping) in this living doc.

### Session Log — 2025-11-21 — Canonical patient_id transform & verifier parameterization

Context
- Goal: Transform source/staging data to match production by trimming/splitting name + DOB to create patient_id = "LASTNAME FIRSTNAME MM/DD/YYYY".
- Defensive collaboration: We are fixing the canonical rules and aligning verification to staging first, then measuring linkage to production.

Changes Implemented
- Updated src/sql/staging_provider_tasks.sql:
  - Keep comma for splitting Last vs First; strip vendor/facility prefixes without removing the comma.
  - Uppercase names; remove internal spaces; preserve hyphens.
  - Extract DOB from the end; convert 2-digit years to 20YY; output patient_id as "LASTNAME FIRSTNAME MM/DD/YYYY".
  - Preserve existing date normalization for activity_date and year_month; maintain indexes.
- Updated scripts/verify_normalization_linkage.py:
  - Parameterized to use --staging-db (default sheets_data.db) and ATTACH --prod-db (default production.db) as prod.
  - Computes linkage rates for provider/coordinator against prod.patients; writes CSVs to scripts/outputs/reports.
  - Appends a concise summary to PROJECT_LIVING_DOCUMENT.md; avoids terminal prints by default.

Risk & Gap Analysis
- DOB century ambiguity: 2-digit years default to 20YY; elderly patients may be mis-expanded. Mitigation: consider inferring century from DOS/year_month or age if available.
- Missing comma or DOB: Rows lacking expected delimiters yield NULL patient_id. Mitigation: collect unmatched samples; evaluate a secondary parser (space-delimited) with strict safeguards.
- Coordinator normalization: Still a heuristic REPLACE chain (no canonical parser). Mitigation: implement coordinator canonical parse mirroring provider rules next.
- Unicode/hidden whitespace: Collapse not yet applied. Mitigation: add a shared utility to normalize Unicode whitespace across imports before parsing.
- Collision risk: Multiple distinct raw names mapping to the same canonical patient_id. Mitigation: audit collisions; if necessary, add tie-break metadata or human review while keeping canonical format stable.

Acceptance Criteria (for this phase)
- Canonical patient_id: EXACTLY "LASTNAME FIRSTNAME MM/DD/YYYY" (names uppercase; internal spaces removed; hyphens preserved).
- Provider linkage rate ≥ 90% vs prod.patients; Coordinator linkage rate ≥ 85%.
- No regression in activity_date and year_month generation in staging.
- All verification outputs written to scripts/outputs/reports and summarized ONLY here (no terminal spam).

Next Steps
- Rebuild staging via scripts/4a-transform.ps1 and scripts/4b-transform.ps1.
- Run scripts/verify_normalization_linkage.py with defaults (staging=sheets_data.db; prod=production.db).
- Append linkage counts, unmatched samples, and collision summaries to this document.
- Implement Unicode whitespace collapse and a centralized Python normalization (names/DOB) used by both SQL transforms and verification.
- Extend canonical parsing to coordinator data to replace the heuristic REPLACE chains.

Ownership & Review
- Implementer: AI (Safety Engineer & Skeptical Implementer).
- Reviewer: User (Strategy Lead). Please review acceptance criteria and confirm proceeding to staging rebuild + verification.


### Session Log — 2025-11-21 — Recent-only import focus (post-last-task) and ZMO new patients

Scope & Intent
- User direction: Ignore old data; focus on tasks AFTER the last recorded task date in production.db.
- Include new patients added in the ZMO file and ~2+ months of recent task data.

Plan (Defensive & Incremental)
1) Compute cutoff_last_task_date = MAX(activity_date) across provider/coordinator task tables in production.db.
   - Mitigation: Consider a small buffer (e.g., 14 days) to catch backdated entries.
2) Confirm ZMO source(s): file path(s), sheet names, and column schema for patient name, DOB, activity_date, task_type, notes.
3) Update scripts/3_import_to_database.ps1 to accept StartDate and filter rows with activity_date >= cutoff_last_task_date (or cutoff - buffer).
4) Import the ZMO patients/tasks into sheets_data.db staging.
5) Run transforms (4a/4b) to compute canonical patient_id (LASTNAME FIRSTNAME MM/DD/YYYY); preserve hyphens; uppercase names; remove internal spaces.
6) Verify staging linkage against production (verify_normalization_linkage.py with prod attached): record linkage %, collisions, and unmatched samples ONLY in this document.
7) If acceptance criteria met, merge validated recent tasks and new patients into production.db; otherwise, produce an unmatched sample report for review.

Risks & Gaps
- Backdated or corrected tasks may precede cutoff; using a buffer reduces miss risk.
- DOB format variance (YY vs YYYY) may cause mis-expansion; elderly patient century handling needed.
- ZMO schema unknowns: We must confirm column names and delimiter usage (commas in Last, First DOB). 
- Potential duplicate patients in ZMO; collisions in canonical patient_id must be audited.
- Time zone and date parsing: Ensure activity_date normalization to YYYY-MM-DD in staging.

Acceptance Criteria
- Cutoff computed as MAX(activity_date) across all task sources in production.db; buffer decision explicitly documented.
- ZMO import constrained to activity_date >= cutoff (or cutoff - buffer), fully accounted in reports.
- Canonical patient_id generated for ≥90% of recent tasks; linkage ≥90% provider and ≥85% coordinator where matching is expected.
- All outputs written to scripts/outputs/reports; summaries appended ONLY here.

Required Inputs (from User)
- ZMO file path(s) and sheet names to import.
- Confirmation of task tables to use for cutoff (e.g., SOURCE_PROVIDER_TASKS_HISTORY, SOURCE_COORDINATOR_TASKS_HISTORY, or staging_* equivalents), and the date column name(s).
- Decision on buffer window (0 vs 14 days) for backdated entries.

Next Actions (pending approval)
- Implement StartDate filter in 3_import_to_database.ps1.
- Compute cutoff_last_task_date and proceed with ZMO recent-only import into staging.
- Run transforms + verifier and append results here.


### Normalization Linkage Verification (staging vs prod)
Timestamp: 2025-11-21 01:33:43
Staging DB: D:\Git\myhealthteam2\Streamlit\scripts\staging_transform.db
Production DB (attached as 'prod'): D:\Git\myhealthteam2\Streamlit\scripts\staging_transform.db

- Provider linkage: 149/42815 matched (0.35%).
- Coordinator linkage: 0/39933 matched (0.00%).
- Tasks without panel: 21; Panel without tasks: 481.
- Provider collisions: 1; Coordinator collisions: 0.

## Session Log — 2025-11-21 — Sandbox-only staging transforms & linkage verification

Context
- Strictly sandbox-only work per safety plan; no writes to production.db.
- Ran tasks transform into a dedicated sandbox DB and verified counts/linkage.
- Wrote this session log directly in the IDE (not the terminal).

Actions
1) Ran `scripts/4b-transform.ps1` with:
   - `-DatabasePath D:\Git\myhealthteam2\Streamlit\scripts\staging_transform.db`
   - `-StagingDatabasePath D:\Git\myhealthteam2\Streamlit\scripts\sheets_data.db`
   - Result: built `staging_coordinator_tasks` and `staging_provider_tasks` in sandbox.
2) Sanity counts (sqlite3):
   - `staging_coordinator_tasks` = 39,933
   - `staging_provider_tasks` = 42,815
3) Skipped `4a-transform.ps1` (blocked by missing `facilities`); created minimal `patients` and `patient_panel` in sandbox from `SOURCE_PATIENT_DATA` in `sheets_data.db` to satisfy verifier.
4) Adjusted `scripts/verify_normalization_linkage.py`:
   - Use `sc.patient_name_raw` instead of `sc."Pt Name"` in coordinator normalization queries.
   - Parameterized paths; ran with staging attached to sandbox to validate pipeline wiring.
5) Ran verifier with both staging and prod pointed at sandbox (wiring check only).

Results
- Verifier executed without errors; wrote reports and produced a linkage summary.
- Preliminary linkage (sandbox vs sandbox) shows low match rates (Provider ≈0.35%, Coordinator ≈0%).
  - Interpreted as normalization mismatch between canonical patient_id in tasks vs panel; consistent with the plan to unify canonical parsing.
- Confirmed: no changes to `production.db` during this session.

Risk & Gap Analysis
- 4a-transform dependency on `facilities` blocks full patient staging; needs patch to decouple or stub.
- Canonical patient_id not yet consistent across coordinator/provider transforms and panel; coordinator still uses heuristic REPLACE chains.
- DOB century handling (2-digit years) and name whitespace/hyphen rules must be unified to avoid collisions and misses.
- Verifier linkage against true `production.db` deferred until canonical normalization is implemented to avoid misleading metrics.

Technical Debt
- Normalization logic duplicated across SQL and Python; centralize into a single canonical function or shared SQL snippet.
- 4a-transform should accept a staging-only mode that does not require `facilities`.
- Prior attempts appended logs via terminal; standardized this to IDE file updates.

Next Steps
- Patch `4a-transform.ps1` to run without `facilities` (or stub it) and populate sandbox `staging_patients`/`staging_patient_panel` correctly.
- Implement a shared canonical patient_id normalization used by 4b (tasks) and by patient panel creation.
- Re-run 4b in sandbox with canonical normalization; re-run verifier with `prod` attached to `production.db` to measure true linkage.
- Append updated linkage counts and collision/unmatched summaries here; decide on buffer window for recent-only imports.

Ownership & Review
- Implementer: AI (Safety Engineer & Skeptical Implementer)
- Reviewer: User (Strategy Lead) — confirm the patch approach for 4a and the canonical normalization plan.


### Normalization Linkage Verification (staging vs prod)
Timestamp: 2025-11-21 01:45:54
Staging DB: D:\Git\myhealthteam2\Streamlit\scripts\staging_transform.db
Production DB (attached as 'prod'): D:\Git\myhealthteam2\Streamlit\production.db

- Provider linkage: 114/42815 matched (0.27%).
- Coordinator linkage: 0/39933 matched (0.00%).
- Tasks without panel: 21; Panel without tasks: 486.
- Provider collisions: 1; Coordinator collisions: 0.


### Normalization Linkage Verification (staging vs prod)
Timestamp: 2025-11-21 01:54:03
Staging DB: D:\Git\myhealthteam2\Streamlit\scripts\staging_transform.db
Production DB (attached as 'prod'): D:\Git\myhealthteam2\Streamlit\production.db

- Provider linkage: 4159/47992 matched (8.67%).
- Coordinator linkage: 0/39933 matched (0.00%).
- Tasks without panel: 341; Panel without tasks: 160.
- Provider collisions: 1; Coordinator collisions: 0.

## Session Log — 2025-11-21 — Provider patient_id normalization alignment and linkage re-check (staging-safe)

Context
- Stopped further runtime changes; focused on documenting the issues and alignment steps.
- Strictly sandbox/staging work; no writes to production.db.

Actions
1) Patched scripts/4a-transform.ps1 to be sandbox-safe (guards for facilities/users) and built:
   - staging_patients (619 rows), staging_patient_assignments (619), staging_patient_panel (619).
2) Fixed scripts/4b-transform.ps1 SQL paths to point to ..\src\sql, then rebuilt staging tasks.
3) Adjusted src/sql/staging_provider_tasks.sql patient_id logic to better match production formatting:
   - Preserve internal spaces in names and UPPERCASE names; normalize DOB (including 2-digit year -> 20YY).
   - Avoid overly aggressive space stripping that caused mismatches.
4) Recomputed linkage metrics against production patients read-only.

Results (post-adjustment)
- staging_provider_tasks rows: 47,992; matched to prod patients: 4,159 (8.67%).
- staging_coordinator_tasks rows: 39,933; matched to prod patients: 0 (0%).
- Tasks without panel: 340; Panel without tasks: 160.
- Provider collisions: 1; Coordinator collisions: 0.
- Observation: Production patients patient_id format is uppercase with internal spaces preserved (sample query confirmed).

Risk & Gap Analysis
- Inconsistent patient_id style between panel and tasks:
  - Panel/patients in staging currently use mixed-case and do not UPPERCASE; provider tasks use UPPERCASE. This likely contributes to tasks_without_panel.
- Coordinator linkage at 0%: "Pt Name" lacks DOB in many cases; without DOB embedded, matches to production patient_id (which includes DOB) will fail.
- Normalization logic is duplicated and inconsistent across files (SQL + Python) leading to drift.
- Two-digit year handling and whitespace normalization must be unified to avoid false negatives and collisions.

Decisions/Proposals
- Adopt a single canonical normalization pattern (see src/sql/patient_id_normalization_function.sql) across 4a and 4b:
  - UPPERCASE names, preserve single spaces, strip known prefixes (ZEN-, PM-, ZMN-, BlessedCare variants, 3PR), normalize commas to spaces.
  - Normalize DOB, mapping 2-digit years to 20YY.
- Update 4a (staging_patients + staging_patient_panel) to build patient_id using canonical format matching production (UPPERCASE + DOB), then rebuild.
- Implement coordinator patient_id normalization with DOB:
  - If DOB present in "Pt Name", parse and embed; otherwise create a mapping step: join SOURCE_PATIENT_DATA on name + proximity of DOS to infer DOB, or use normalized_mappings.csv as a fallback.
- Index patient_id in all staging tables after normalization to support efficient joins and verifier checks.

Next Steps (staging-safe)
- Patch 4a to use the canonical patient_id normalization; uppercase names and standard DOB normalization.
- Rebuild 4a and 4b; re-run verify_normalization_linkage.py with prod attached; append updated metrics to this document.
- Add tests for normalization (scripts/normalization_tests.sql and test_patient_id_normalization.py) to prevent regressions.
- Define acceptance criteria: Provider linkage ≥95%, Coordinator linkage ≥90%, tasks_without_panel ≈0, minimal collisions.

Technical Debt
- Divergent normalization implementations across files; must consolidate to a single source-of-truth.
- Sandbox guards (facilities/users) exist only in 4a; replicate or parameterize for other scripts if needed.
- Coordinator DOB derivation/mapping needed; currently brittle and absent.

Open Questions (for Reviewer)
- Confirm we should standardize patient_id as UPPERCASE with spaces preserved (matches production samples).
- Confirm whether coordinator "Pt Name" is expected to include DOB; if not, approve mapping approach to infer/attach DOB for reliable linkage.

## Session Log — 2025-11-21 — Admin Dashboard Patient Search

Context
- Request: Add text input search for patient names in Admin Dashboard > Patient Info tab.
- Reason: Built-in table search is insufficient.

Plan
- Modify src/dashboards/admin_dashboard.py:
  - Insert st.text_input in 	ab3 (Patient Info).
  - Filter patients_df by Name/ID before the Active/Inactive split.
  - Filter logic: Case-insensitive partial match on irst_name, last_name, or patient_id.

Risks
- Case sensitivity (will use case-insensitive).
- Performance (filtering in Python is fine for current dataset size).


## Session Log — 2025-11-21 — Admin Dashboard: Patient Search Placement Refinement

Context
- Request: Move the patient search box in the Admin Dashboard > Patient Info tab to be directly above the 'Active Patients' section.
- Goal: Improve UI layout by grouping search with the list it filters.

Changes Made
1) Modified src/dashboards/admin_dashboard.py:
   - Moved the search filter code block from the top of `tab3` to after the 'Patient Visit Breakdown' section.
   - Fixed an `IndentationError` at line 1142 (empty `if` block).
   - Fixed a `NameError` by restoring the `active_statuses` definition which was inadvertently removed during the move.

Verification
- Verified using browser subagent:
  - App loads without errors.
  - Search box is correctly positioned above 'Active Patients'.
  - Search functionality works (filtering by name updates the patient count).

Risk & Gap Analysis
- Regression risk: Moving code blocks can introduce scope issues (as seen with `active_statuses`). Mitigation: Verified with browser test.

Next Steps
- None. Feature implemented and verified.
