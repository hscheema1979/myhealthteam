# Old Scripts Archive

**Date Archived:** December 16, 2024

## Purpose

This folder contains 208 Python scripts that were removed during the project cleanup. These are primarily development, testing, debugging, and one-off utility scripts that were cluttering the root directory.

## Contents Overview

### Categories of Archived Files

#### Database Exploration & Validation (~40 files)
- `check_*.py` - Database schema inspection and validation scripts
- Examples: `check_admin_users.py`, `check_billing_data_availability.py`, `check_coordinator_tables.py`
- Purpose: Used to explore database structure and verify data during development
- Status: No longer needed as database schema is documented in CONSOLIDATED_SYSTEM_DOCUMENTATION.md

#### Testing & Verification (~50 files)
- `test_*.py` - Testing and verification scripts
- Examples: `test_admin_dashboard_load.py`, `test_billing_functions.py`, `test_coordinator_workflow_fix.py`
- Purpose: Ad-hoc testing during development phases
- Status: Superseded by proper testing procedures

#### Debugging & Analysis (~25 files)
- `debug_*.py` - Debugging aids and analysis scripts
- `analyze_*.py` - Data analysis and investigation scripts
- `investigate_*.py` - Inquiry and exploration scripts
- Purpose: Used to troubleshoot specific issues and explore data problems
- Status: Issues have been resolved, archive kept for reference

#### Fixes & Migrations (~20 files)
- `fix_*.py` - One-off fix scripts for specific data issues
- `migrate_*.py` - Data migration scripts
- `populate_*.py` - Data population scripts
- Purpose: Used to fix specific data corruption or transformation issues
- Status: One-time use scripts, no longer needed

#### Utilities & Helpers (~68 files)
- Various utility scripts for data processing, reporting, and system inspection
- Examples: `consolidate_similar_names.py`, `get_user_ids.py`, `sample_coordinator_data.py`
- Purpose: Supporting utilities used during development
- Status: Functionality now integrated into main application or no longer needed

## Why These Files Were Archived

1. **Cleanup Initiative** - Project had grown to 208 root-level Python files, making navigation difficult
2. **Development Artifacts** - Most were created to solve specific problems during development
3. **Redundancy** - Functionality now part of core application or data pipeline
4. **Documentation** - Database and data issues are now well-documented
5. **Simplified Pipeline** - Data refresh now uses `refresh_production_data.ps1` + `transform_production_data_v3_fixed.py`

## When You Might Need These Files

### Troubleshooting Issues
If you encounter problems similar to what these files addressed, they can provide context:
- Check git history or this archive for how the problem was previously solved
- Review `debug_*.py` or `analyze_*.py` files for similar issues

### Historical Context
Understanding how data transformations evolved:
- Review `migrate_*.py` files to see what data issues were fixed
- Check `fix_*.py` files for one-off corrections that might be recurring

### Reference Implementation
If implementing similar functionality:
- Look at archived test files for testing approaches
- Check utility scripts for helper function implementations

## How to Use These Files

### To Restore a Single File
```bash
# Copy from archive back to root
cp old_scripts_archive/check_billing_data.py check_billing_data.py
```

### To Find a Specific File
```bash
# Search by name pattern
ls old_scripts_archive/check_*.py

# Search within files
grep -r "function_name" old_scripts_archive/
```

### To Understand What a File Does
1. Check the filename - usually descriptive (e.g., `test_billing_functions.py`)
2. Look at the file header/docstring
3. Review git history: `git log --all -- old_scripts_archive/filename.py`
4. Search git for when it was used: `git log -S "filename" --all`

## Retention Policy

- **6-Month Retention:** Keep for reference and historical context
- **12-Month Decision:** Evaluate whether to keep longer or delete
- **Git History:** All files permanently preserved in git history
- **Recovery:** Anytime needed, restore from git or this archive

## Archive Statistics

- **Total Files:** 208
- **Largest Category:** Testing & Verification (~50 files)
- **Approximate Size:** ~5-10 MB uncompressed
- **Compression:** Can be compressed to ~1-2 MB if archiving long-term

## Related Documentation

- **Active Project:** See `../app.py` and `../src/dashboards/`
- **Data Pipeline:** See `../refresh_production_data.ps1`
- **Architecture:** See `../docs/CONSOLIDATED_SYSTEM_DOCUMENTATION.md`
- **Cleanup Details:** See `../CLEANUP_COMPLETED.md`

## Questions?

If you need context about why something was archived or how it worked:
1. Check the filename and git history
2. Review CLEANUP_COMPLETED.md for full cleanup details
3. Ask team members who worked on the code
4. Refer to CONSOLIDATED_SYSTEM_DOCUMENTATION.md for current architecture

---

**Note:** These files are kept for historical reference only. The active, production-ready code is in the parent directory and `src/` folder.
