# Scripts Archive

**Date Archived:** December 16, 2024

## Purpose

This folder contains 28 PowerShell scripts that were archived during the project cleanup. These are primarily old data pipeline scripts, automation setup scripts, and backup scheduling scripts that are no longer part of the active data refresh workflow.

## Active Production Scripts

The **core active scripts** are in the parent `scripts/` folder:
- `1_download_files_complete.ps1` - Download CSVs from Google Sheets
- `2_consolidate_files.ps1` - Consolidate downloaded CSV files
- `backup_production_db.ps1` - Manual database backup utility
- `run_capture_workflows.ps1` - Workflow execution
- `run_capture_workflows_direct.ps1` - Workflow execution (direct variant)

These are orchestrated by the master script:
- `../../refresh_production_data.ps1` - Single entry point for all data refresh operations

## Archive Contents Overview

### Old Data Import Pipeline (~9 files)
- `3_import_to_database.ps1` - Old import script (replaced by Python)
- `4_transform_data_enhanced.ps1` - Old transform script (replaced by Python)
- `4a-transform.ps1` - Old transform variant A
- `4b-transform.ps1` - Old transform variant B
- `4c-transform.ps1` - Old transform variant C
- `5_import_cmlog_data.ps1` - CMLOG-specific import
- `import_delta.ps1` - Incremental import script
- `daily_diff_import_*.ps1` - Daily differential imports (3 variants)
- Purpose: Previous data pipeline stages before consolidation into refresh_production_data.ps1
- Status: Replaced by `transform_production_data_v3_fixed.py` and unified refresh workflow

### Automation & Scheduling (~13 files)
- `auto_git_commit.ps1` - Automatic git commits
- `auto_git_commit_with_db.ps1` - Git commits with database
- `auto_git_pull.ps1` - Automatic git pull
- `schedule_autocommit.ps1` - Schedule git automation
- `schedule_daily_import.ps1` - Schedule daily data imports
- `setup_auto_git_commit.ps1` - Setup automation
- `setup_auto_git_commit_with_db.ps1` - Setup with DB
- `setup_auto_git_pull.ps1` - Setup git pull
- Purpose: Automation of git operations and data imports
- Status: Not part of current workflow; manual operations preferred

### Backup & Scheduling (~6 files)
- `backup_database.ps1` - Old backup script
- `backup_now.ps1` - Manual backup trigger
- `hourly_backup_system.ps1` - Hourly backup automation
- `setup_backup_schedule.ps1` - Backup scheduling setup
- `setup_hourly_backup_schedule.ps1` - Hourly backup setup
- `setup_hourly_backup_simple.ps1` - Simple hourly backup
- Purpose: Various backup scheduling approaches
- Status: Backup functionality integrated into refresh_production_data.ps1

### Other Utilities (~2 files)
- `create_and_populate_summaries.ps1` - Summary creation (integrated into SQL)
- `setup_streamlit_monitor_task.ps1` - Streamlit monitoring setup
- Purpose: Supporting utilities
- Status: Functionality integrated or not needed

## Why These Files Were Archived

1. **Consolidation** - Multiple data pipeline scripts consolidated into single `refresh_production_data.ps1`
2. **Python Migration** - Data transformation moved to `transform_production_data_v3_fixed.py`
3. **Simplified Workflow** - No need for manual step selection or separate import stages
4. **Automation Removal** - Automated git/backup operations not part of standard workflow
5. **Centralized Control** - Single master script provides clarity and consistency

## Current Data Pipeline

```
refresh_production_data.ps1 (Master Orchestrator)
│
├─ Backup production.db
├─ Download CSVs
│  └─ 1_download_files_complete.ps1
├─ Consolidate CSVs
│  └─ 2_consolidate_files.ps1
├─ Transform Data
│  └─ transform_production_data_v3_fixed.py
└─ Post-Process
   └─ src/sql/post_import_processing.sql
```

This replaced the old multi-step process of manually running scripts 1, 2, 3, 4 in sequence.

## When You Might Need These Files

### Understanding Previous Approach
If learning how data pipeline evolved:
- Review old transform scripts to understand previous logic
- See how import staging evolved
- Understand previous backup strategies

### Troubleshooting Legacy Issues
If encountering problems with historical data:
- Check archived import scripts for data loading approaches
- Review old transform logic for similar issues
- Look at diagnostic comments in archived scripts

### Reference Implementation
If building similar functionality:
- Review backup scripts for backup approaches
- Check scheduling scripts for automation patterns
- See how imports were previously staged

### Historical Analysis
If analyzing system evolution:
- See what automation attempts were made
- Understand why single unified pipeline is better
- Learn from previous approaches

## How to Use These Files

### To Examine a File
```powershell
# View file contents
Get-Content archive/filename.ps1

# Search within files
Select-String -Path "archive/*.ps1" -Pattern "function_name"
```

### To Run a Historical Script
```powershell
# Navigate to scripts folder
cd scripts

# Run archived script (use with caution)
.\archive\old_script.ps1 -Parameter value
```

### To Understand Specific Script
1. Check filename - usually descriptive (e.g., `daily_diff_import_coordinator.ps1`)
2. Review comments and function definitions in file
3. Search git history: `git log --all -- scripts/archive/filename.ps1`
4. Find related issue or ticket that script addressed

⚠️ **WARNING:** These scripts may reference old table structures or deprecated approaches. Test thoroughly before running.

## Archive Statistics

- **Total Files:** 28 PowerShell scripts
- **Total Size:** ~300-500KB uncompressed
- **Categories:**
  - Data import/transform: 9 files
  - Automation/scheduling: 13 files
  - Backup utilities: 6 files
- **Compression:** Compresses to ~50-75KB if needed

## Comparison: Old vs New Workflow

### Old Workflow (Complex)
```
Step 1: Download data manually
  .\1_download_files_complete.ps1

Step 2: Wait for completion, consolidate
  .\2_consolidate_files.ps1

Step 3: Wait for completion, import
  .\3_import_to_database.ps1

Step 4: Wait for completion, transform
  .\4_transform_data_enhanced.ps1 or 4a/4b/4c?

Step 5: Hope post-processing ran
  (Or run manually if missed)

Step 6: Verify everything worked
  (Or troubleshoot if something failed)
```

### New Workflow (Simple)
```
.\refresh_production_data.ps1

(Automatically does all 5 steps in order)
```

**Benefits:**
- No confusion about which step to run
- Automatic sequencing
- Unified error handling
- Clear rollback instructions
- One entry point for data refresh

## Related Information

### Master Orchestrator
- `../../refresh_production_data.ps1` - Single entry point
- Handles: Backup → Download → Consolidate → Transform → Post-Process

### Active Scripts in Parent Folder
- `1_download_files_complete.ps1` - Still used by refresh orchestrator
- `2_consolidate_files.ps1` - Still used by refresh orchestrator
- `backup_production_db.ps1` - Manual backup when needed
- `run_capture_workflows.ps1` - Workflow execution (separate process)

### Data Transformation
- `../../transform_production_data_v3_fixed.py` - Python data processor
- Replaces all archived 3_import and 4_transform variants

### Documentation
- `../../docs/CONSOLIDATED_SYSTEM_DOCUMENTATION.md` - System architecture
- `../../docs/PROJECT_REFACTOR_PLAN.md` - Future roadmap
- `../../CLEANUP_COMPLETED.md` - Cleanup details

## Retention Policy

- **6-Month Retention:** Keep for reference and historical context
- **12-Month Review:** Evaluate if long-term storage needed
- **Git History:** All files preserved permanently in git
- **Compression:** Can compress to ~50KB if keeping beyond 1 year
- **Recovery:** Restore from git anytime: `git show commit:scripts/archive/filename.ps1`

## Important Notes

⚠️ **These scripts are deprecated - do not use in production**
- Use `refresh_production_data.ps1` instead
- Archived scripts may reference old/changed structures
- Test thoroughly before running any archived script
- Always have current backup before experimenting

✅ **Use for reference only**
- Understand previous approaches
- Learn from evolution of the system
- Guide similar implementations
- Troubleshoot historical issues

🔒 **Current approach is simpler and better**
- Single unified refresh pipeline
- Automatic error handling
- Clear success/failure indicators
- Rollback instructions provided

## Questions?

For questions about:
- **Current Data Pipeline:** See `../../refresh_production_data.ps1`
- **Running Data Refresh:** See docs/CONSOLIDATED_SYSTEM_DOCUMENTATION.md (Deployment section)
- **Specific Archived Script:** Check filename and git history
- **Why Things Changed:** See `../../CLEANUP_COMPLETED.md`
- **System Architecture:** See `../../docs/CONSOLIDATED_SYSTEM_DOCUMENTATION.md`

---

**Note:** These files are kept for historical reference only. All data refresh operations should use `../../refresh_production_data.ps1`. The current simplified pipeline is more reliable, maintainable, and easier to understand.