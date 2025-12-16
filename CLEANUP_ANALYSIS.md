# Project Cleanup Analysis & Plan

## Current Data Refresh Architecture

### Active Data Pipeline
The project uses a **consolidated two-part refresh system**:

1. **refresh_production_data.ps1** - Master orchestration script
   - Handles backup, download, transformation, and post-processing
   - Calls transform_production_data_v3_fixed.py for data import
   - Runs src/sql/post_import_processing.sql for aggregations
   - **This is the single source of truth for data refresh**

2. **transform_production_data_v3_fixed.py** - Data transformation engine
   - Processes CSV files from downloads/ folder
   - Handles all billing code assignment and minute range extraction
   - Populates provider_task_billing_status, coordinator_monthly_summary, provider_weekly_payroll
   - **This is the core import logic**

3. **src/sql/post_import_processing.sql** - Post-import aggregations
   - Creates summary views and materialized tables
   - Updates patient data and workflow summaries
   - **Called by refresh_production_data.ps1 after import**

### Old/Redundant Scripts to Delete
```
scripts/1_download_files_complete.ps1          → Called by refresh_production_data.ps1
scripts/2_consolidate_files.ps1               → Called by refresh_production_data.ps1
scripts/3_import_to_database.ps1              → Replaced by transform_production_data_v3_fixed.py
scripts/4_transform_data_enhanced.ps1         → Replaced by transform_production_data_v3_fixed.py
scripts/4a-transform.ps1                      → DELETE (old variant)
scripts/4b-transform.ps1                      → DELETE (old variant)
scripts/4c-transform.ps1                      → DELETE (old variant)
scripts/backup_database.ps1                   → Functionality in refresh_production_data.ps1
scripts/auto_git_commit.ps1                   → Not part of active workflow
scripts/auto_git_commit_with_db.ps1           → Not part of active workflow
scripts/auto_git_pull.ps1                     → Not part of active workflow
scripts/download_sheets.ps1                   → Called by 1_download_files_complete.ps1
scripts/generate_monthly_partitions.ps1       → Not in active workflow
```

**Action:** Delete old scripts 3, 4, 4a-4c, backup_database.ps1, and other non-essential scripts. Keep only those called by refresh_production_data.ps1.

---

## SQL Scripts Cleanup

### Active SQL Scripts
Located in `src/sql/`:

**KEEP:**
- `post_import_processing.sql` - **CRITICAL** - Called by refresh_production_data.ps1 after every import

**Purpose of other 100+ SQL files:**
- Most are development/debugging/schema exploration scripts
- Many are old migrations and one-off data fixes
- Some created temporary tables or explored data issues that have since been resolved

**Recommendation:** Create a `src/sql/archive/` folder and move all SQL files EXCEPT `post_import_processing.sql` there. Keep the archive for reference but don't clutter the active src/sql/ directory.

---

## Dashboard Files Cleanup

### Active Dashboards to KEEP
```
src/dashboards/admin_dashboard.py
src/dashboards/care_coordinator_dashboard_enhanced.py
src/dashboards/care_provider_dashboard_enhanced.py
src/dashboards/weekly_provider_billing_dashboard.py
src/dashboards/weekly_provider_payroll_dashboard.py
src/dashboards/monthly_coordinator_billing_dashboard.py
src/dashboards/onboarding_dashboard.py
src/dashboards/data_entry_dashboard.py
src/dashboards/lead_coordinator_dashboard.py
src/dashboards/coordinator_manager_dashboard.py
```

### Support Files to KEEP
```
src/dashboards/dashboard_display_config.py    - Shared configuration
src/dashboards/phone_review.py                - Imported by care_coordinator_dashboard_enhanced.py and care_provider_dashboard_enhanced.py
```

### DELETE Completely
```
src/dashboards/_do_not_use/                   - Entire folder (10+ obsolete dashboard variants)
src/dashboards/workflow_module_for_reference.txt - Text reference file (not used)
src/dashboards/test_dashboard_functions.py    - Test file (not in active use)
```

### KEEP or DELETE?
```
src/dashboards/workflow_module.py
  Status: KEEP - Imported by app.py for workflow management functions
  Contains: get_workflow_templates(), get_workflow_template_steps(), create_workflow_instance(), etc.
  Used by: Workflow reassignment functionality in admin dashboard
```

### phone_review.py Files
```
old_dashboards_do_not_use!!!/phone_review.py
  DELETE - In obsolete folder

src/components/phone_review.py
  Status: UNKNOWN - Check if imported anywhere

src/dashboards/phone_review.py
  DELETE - Active dashboards import from here, but check which one they actually use
  ACTUALLY: This is the one being imported, KEEP IT
```

---

## Root-Level Python Files Cleanup

**Total files: 208 Python files**
**Only needed: app.py**

### Categories to DELETE (207 files)
```
check_*.py                    ~40 files - Database schema exploration
test_*.py                     ~50 files - Testing and verification scripts
debug_*.py                    ~20 files - Debugging aids
fix_*.py                      ~10 files - One-off fixes
analyze_*.py                  ~15 files - Data analysis scripts
inspect_*.py                  ~5 files - Schema inspection
validate_*.py                 ~10 files - Validation tests
Other temporary files         ~57 files - Migration, sample data, etc.
```

**Action:** DELETE all root-level .py files EXCEPT app.py

---

## Summary: What to Keep vs Delete

### KEEP (Core Active Files)
```
Root Level:
├── app.py                                     (Main Streamlit app)
├── transform_production_data_v3_fixed.py      (Data transformation engine)
├── refresh_production_data.ps1                (Data refresh orchestrator)

Dashboards (10 active):
├── src/dashboards/admin_dashboard.py
├── src/dashboards/care_coordinator_dashboard_enhanced.py
├── src/dashboards/care_provider_dashboard_enhanced.py
├── src/dashboards/weekly_provider_billing_dashboard.py
├── src/dashboards/weekly_provider_payroll_dashboard.py
├── src/dashboards/monthly_coordinator_billing_dashboard.py
├── src/dashboards/onboarding_dashboard.py
├── src/dashboards/data_entry_dashboard.py
├── src/dashboards/lead_coordinator_dashboard.py
├── src/dashboards/coordinator_manager_dashboard.py
├── src/dashboards/dashboard_display_config.py
├── src/dashboards/phone_review.py
├── src/dashboards/workflow_module.py

SQL:
├── src/sql/post_import_processing.sql         (Post-import aggregations)

Scripts (support for data refresh):
├── scripts/1_download_files_complete.ps1
├── scripts/2_consolidate_files.ps1
└── (Other scripts called by refresh_production_data.ps1)

Core Libraries:
├── src/database.py
├── src/config/ui_style_config.py
├── src/utils/ (all active utilities)
```

### DELETE Completely
```
Root Level:
├── 207 Python files (check_*, test_*, debug_*, fix_*, analyze_*, etc.)

Dashboards:
├── src/dashboards/_do_not_use/ (entire folder)
├── src/dashboards/workflow_module_for_reference.txt
├── src/dashboards/test_dashboard_functions.py

Old Scripts (in scripts/):
├── 3_import_to_database.ps1
├── 4_transform_data_enhanced.ps1
├── 4a-transform.ps1
├── 4b-transform.ps1
├── 4c-transform.ps1
├── backup_database.ps1
├── (Other non-active scripts)

SQL Archive:
├── Move 100+ SQL files to src/sql/archive/ (for reference, not active use)
└── Keep only post_import_processing.sql in src/sql/
```

---

## Expected Results After Cleanup

**Before:**
- 208 root-level Python files
- 10+ obsolete dashboard variants in _do_not_use/
- 100+ SQL exploration/migration scripts cluttering src/sql/
- 15+ old data refresh scripts in scripts/
- Project folder is confusing and hard to navigate

**After:**
- 1 root-level Python file (app.py)
- 1 data transform script (transform_production_data_v3_fixed.py)
- 1 master refresh script (refresh_production_data.ps1)
- 10 active dashboards + 3 support files in src/dashboards/
- 1 active SQL file (post_import_processing.sql) + archive folder
- Clear, minimal project structure
- ~90% reduction in file count
- Easy for new developers to understand architecture

---

## Cleanup Execution Plan

### Phase 1: Verify Everything Works
1. Run `refresh_production_data.ps1 -SkipDownload -SkipBackup` to verify current pipeline
2. Launch `app.py` and verify all dashboards load correctly
3. Confirm no imports are broken

### Phase 2: Archive Old SQL Scripts
1. Create `src/sql/archive/` folder
2. Move all SQL files except `post_import_processing.sql` to archive
3. Document which SQL files relate to which data issues (in ARCHIVE_INDEX.md)

### Phase 3: Delete Old Dashboard Variants
1. Delete `src/dashboards/_do_not_use/` folder
2. Delete `src/dashboards/workflow_module_for_reference.txt`
3. Delete `src/dashboards/test_dashboard_functions.py`

### Phase 4: Clean Up Root Python Files
1. Create `old_scripts_archive/` folder in root
2. Move all 207 root-level Python files to archive (for 6-month retention)
3. Commit to git with clear message

### Phase 5: Clean Up Old Scripts
1. Review scripts/ folder
2. Delete old transform and import scripts (keep only those called by refresh_production_data.ps1)
3. Keep download, backup, and utility scripts that are active

### Phase 6: Final Verification
1. Run full data refresh: `refresh_production_data.ps1`
2. Launch app and verify all dashboards
3. Commit final clean state to git
4. Tag as "v-cleanup-complete"

---

## Risk Assessment: VERY LOW RISK

This cleanup is **very safe** because:
- All active code is in `src/` subdirectories and `app.py`
- All data pipeline is documented in `refresh_production_data.ps1`
- We're only deleting development/debugging artifacts
- Everything being deleted is in git history (can be recovered)
- No production database changes
- No dashboard code changes