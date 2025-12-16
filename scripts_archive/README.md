# Scripts Archive

**Date Archived:** December 16, 2024

## Purpose

This folder contains 1,300+ files that were archived from the `scripts/` directory during the project cleanup. These are primarily utility scripts, data analysis tools, automation setups, and supporting files that are not part of the active data pipeline.

## Active Scripts (Kept in Parent Folder)

The **only** scripts actively used are in `../scripts/`:
- `1_download_files_complete.ps1` - Download CSVs from Google Sheets
- `2_consolidate_files.ps1` - Consolidate CSV files
- `backup_production_db.ps1` - Manual database backup
- `run_capture_workflows.ps1` - Workflow execution
- `run_capture_workflows_direct.ps1` - Workflow execution (variant)

## Archive Contents Overview

### Top-Level Files (170+ files)

#### Python Scripts (~63 files)
- `add_*.py` - Add/migrate database columns
- `analyze_*.py` - Data analysis scripts
- `audit_*.py` - Database auditing
- `backup_*.py` - Backup utilities
- `build_*.py` - Build/populate tables
- `cleanup_*.py` - Database cleanup
- `compare_*.py` - Data comparison utilities
- Purpose: One-off utilities and analysis scripts
- Status: Legacy utilities, functionality integrated or obsolete

#### SQL Scripts (~45 files)
- `compare_*.sql` - Compare production vs staging/sheets
- `migration_*.sql` - Database migrations
- Purpose: Schema exploration and data validation
- Status: Historical reference for schema changes

#### Documentation (~35 files)
- `*.md` - Markdown documentation
- `*.txt` - Text files
- `AUTO_GIT_COMMIT_*.md` - Automation documentation
- Purpose: Setup and configuration guides
- Status: Reference documentation for legacy automation

#### Configuration Files (~15 files)
- `*.bat` - Batch files
- `autocommit.py` - Auto-commit configuration
- Purpose: Automation setup and triggering
- Status: Not part of current workflow

#### Data Files (~12 files)
- `*.csv` - CSV data exports
- `*.db` - SQLite database files
- `*.zip` - Backup packages
- Purpose: Temporary data and backups
- Status: Snapshots, no longer needed

### Subdirectories

#### `/automation` (18MB)
- `capture_workflows.js` - JavaScript automation scripts
- `node_modules/` - NPM dependencies
- Purpose: Browser automation for workflow capture
- Status: Complex automation setup, not actively used
- Action: Consider deleting if workflow capture is working via other means

#### `/tools` (47MB)
- Various executable tools and utilities
- Purpose: Supporting tools for development
- Status: Development artifacts
- Action: Archive for reference, delete if not needed after 6 months

#### `/outputs` (3.2MB)
- Generated data and reports
- CSV exports from analysis scripts
- Purpose: Output from various data processes
- Status: Temporary outputs, can be regenerated
- Action: Safe to delete

#### `/migrations` (25KB)
- Database migration tracking
- Purpose: Historical record of schema changes
- Status: Reference only
- Action: Keep for history, archive safe to keep

#### `/logs` (4KB)
- Log files from various processes
- Purpose: Execution history
- Status: Old logs, can be cleared
- Action: Safe to delete

#### `/production_auto_pull` (24KB)
- Auto-pull automation setup
- Purpose: Git automation
- Status: Not part of current workflow
- Action: Archive for reference

#### `/archive` (260KB)
- Already organized archive from Phase 1 cleanup
- Contains: Old PowerShell import/transform scripts
- Already has README.md
- Status: Well-organized, no action needed

## Why These Files Were Archived

1. **Not Part of Active Pipeline** - Only 5 PowerShell scripts needed for data refresh
2. **Development Artifacts** - Analysis scripts, one-off utilities, test data
3. **Legacy Automation** - Git automation, browser automation not in active use
4. **Temporary Outputs** - Generated reports, test data, CSV exports
5. **Documentation** - Setup guides for automation no longer used
6. **Size Reduction** - scripts/ folder reduced from 87MB to <1MB

## What's Safe to Delete

### Safe to Delete Immediately
- `/outputs/` - Temporary generated data (3.2MB)
- `/logs/` - Old log files (4KB)
- `*.csv` files - Exported data
- `*.db` files (except if needed for reference) - Backup databases
- `*.bat` files - Batch file automation
- `/production_auto_pull/` - Old git automation (24KB)

### Keep for 6 Months, Then Evaluate
- `/tools/` - May have useful utilities (47MB)
- `/automation/` - Complex setup, might be reference (18MB)
- Python analysis scripts - For troubleshooting similar issues

### Keep Long-Term
- `/migrations/` - Historical record of schema changes
- `/archive/` - Already organized, well-documented
- SQL comparison scripts - Reference for data validation

## Statistics

- **Total Files:** 1,300+
- **Total Size:** 87MB uncompressed
- **By Type:**
  - Python: 63 files
  - SQL: 45 files
  - JavaScript: 188 files (in automation/)
  - Documentation: 151 files
  - Other: 850+ files

## How to Use This Archive

### Finding a Specific File
```bash
# Search by name
find . -name "*pattern*"

# List Python scripts
ls -1 *.py | head -20

# List by directory
ls -1 automation/
ls -1 tools/
```

### Recovering a File
```bash
# Copy back to scripts folder
cp scripts_archive/filename.py ../scripts/

# Copy directory back
cp -r scripts_archive/tools ../scripts/
```

### Understanding Script Purpose
1. Check the filename - usually descriptive
2. Read the first few lines for docstring
3. Search for similar issue: `grep -r "issue_name" .`
4. Check git history for context
5. Review related README or documentation file

## Cleanup Recommendation

### Immediate Deletions (Safe - 3.2MB)
- `outputs/` - Temporary data
- `logs/` - Old logs
- `*.csv` files
- `*.bat` files

### 6-Month Evaluation
- `tools/` - If no reference needed
- `automation/` - If workflow capture working via other means
- Python utility scripts - If issues stop recurring

### Keep Indefinitely
- `archive/` - Well-organized reference
- `migrations/` - Schema history
- SQL comparison scripts - Troubleshooting reference

## Related Documentation

- **Active Scripts:** See `../scripts/` folder
- **Data Pipeline:** See `../../refresh_production_data.ps1`
- **Project Architecture:** See `../../docs/CONSOLIDATED_SYSTEM_DOCUMENTATION.md`
- **Project Cleanup:** See `../../CLEANUP_INDEX.md`

## Important Notes

⚠️ **This folder can be significantly reduced**
- `outputs/`, `logs/`, and `*.csv` can be deleted immediately (saves 3.2MB)
- `tools/` and `automation/` could be deleted if not referencing (saves 65MB)
- After cleanup, this archive could go from 87MB to ~15-20MB

✅ **Safe to archive**
- All files are backed up in git history
- Non-critical files that can be regenerated
- Reference material for troubleshooting

🔒 **Keep for reference**
- `archive/` - Already clean
- `migrations/` - Schema history
- Python scripts - Troubleshooting patterns

## Questions?

For questions about:
- **Specific file:** Check filename and grep for context
- **Directory purpose:** See overview above
- **Script functionality:** Review first lines of file
- **Git history:** `git log --all -- scripts_archive/filename`
- **Recovery:** Copy from here or restore from git

---

**Note:** This archive reduced the scripts/ folder from 87MB to <1MB while preserving all critical functionality. The active data pipeline requires only 5 PowerShell scripts. Everything else is reference/historical material that can be deleted after 6 months if not needed.
