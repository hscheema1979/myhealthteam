# SQL Archive

**Date Archived:** December 16, 2024

## Purpose

This folder contains 101 SQL scripts that were archived during the project cleanup. These are primarily schema migrations, data transformations, debugging queries, and one-off fixes that are no longer part of the active data pipeline.

## Active Production SQL

The **only** SQL file actively used in production is:
- `../post_import_processing.sql` - Post-import aggregations and view creation (26KB)

This file is called automatically by `refresh_production_data.ps1` after every data import.

## Archive Contents Overview

### Schema Creation & Migration (~25 files)
- `create_*.sql` - Database table and view creation scripts
- `migrate_*.sql` - Schema migration scripts
- `5_schema_enhancement.sql` - Schema improvements
- Purpose: Used to initialize and evolve database structure
- Status: Database schema is now stable; these are historical references

### Data Transformation & Population (~35 files)
- `populate_*.sql` - Data population scripts
- `transform_*.sql` - Data transformation queries
- `complete_*.sql` - Comprehensive data operations
- Purpose: Used during data imports and transformations
- Status: Functionality integrated into `transform_production_data_v3_fixed.py`

### Billing & Payroll Processing (~15 files)
- `create_weekly_billing_system.sql` - Weekly billing tables
- `create_provider_*.sql` - Provider-related tables
- `populate_provider_*.sql` - Provider data population
- `populate_coordinator_*.sql` - Coordinator data population
- Purpose: Specific billing and payroll workflows
- Status: Core functionality preserved in post_import_processing.sql

### Views & Analytics (~12 files)
- `create_dashboard_views.sql` - Dashboard query views
- `create_patient_*.sql` - Patient-related views
- `enhanced_*.sql` - Enhanced query definitions
- Purpose: Optimized queries for dashboard display
- Status: Views now created in post_import_processing.sql

### Debugging & Exploration (~14 files)
- `diagnose_*.sql` - Diagnostic queries
- `explicit_*.sql` - Test/verification queries
- `one_record_*.sql` - Test data queries
- `check_*.sql` - Validation queries
- Purpose: Used to explore and debug data issues
- Status: Issues resolved; kept for troubleshooting reference

## Why These Files Were Archived

1. **Single Source of Truth** - All active SQL is now in `post_import_processing.sql`
2. **Simplified Pipeline** - Data refresh uses Python (`transform_production_data_v3_fixed.py`) + single SQL file
3. **Code Organization** - Reduces clutter in src/sql/ directory
4. **Historical Preservation** - Maintains record of how schema evolved
5. **Documentation** - Current schema documented in CONSOLIDATED_SYSTEM_DOCUMENTATION.md

## Database Schema Status

The current production database schema is:
- **Stable and Optimized** - No schema changes needed
- **Well-Documented** - See CONSOLIDATED_SYSTEM_DOCUMENTATION.md (Section: "Database Design and Data Model")
- **Fully Functional** - All 10 dashboards working with current schema
- **Backed by post_import_processing.sql** - All views and aggregations defined there

### Key Tables in Use
- `users`, `roles`, `user_roles` - Authentication
- `patients`, `user_patient_assignments` - Patient management
- `provider_task_billing_status` - Weekly provider billing
- `provider_weekly_payroll_status` - Weekly provider payroll
- `coordinator_monthly_summary` - Monthly coordinator aggregations
- `coordinator_tasks_YYYY_MM` - Monthly partitioned tasks
- `onboarding_patients` - Onboarding workflow tracking

## When You Might Need These Files

### Schema Analysis
If adding new database features:
- Review `create_*.sql` files to understand existing patterns
- Check migration scripts for historical changes
- See how similar tables were created

### Data Issue Resolution
If troubleshooting data problems:
- Check `populate_*.sql` files to understand data loading logic
- Review `transform_*.sql` for transformation rules
- Look at `diagnose_*.sql` for similar issues

### Performance Optimization
If optimizing queries:
- Review archived views in `create_dashboard_views.sql`
- Check `enhanced_*.sql` for query optimization approaches
- Study aggregation logic in `populate_*.sql`

### Historical Context
Understanding the evolution of the system:
- Review schema creation scripts chronologically
- See what migrations were needed over time
- Understand how data structures evolved

## How to Use These Files

### To Examine a File
```bash
# View file contents
cat src/sql/archive/filename.sql

# Search within files
grep -r "table_name" src/sql/archive/
grep -r "SELECT" src/sql/archive/ | grep "patient"
```

### To Run a Historical Query
```bash
# Connect to database
sqlite3 production.db

# Load and run a query from archive
.read src/sql/archive/diagnose_missing_patients.sql
```

### To Understand Current vs Archived
```bash
# See what's active
ls -la ../post_import_processing.sql

# See what's archived
ls -la archive/ | head -20
```

## Archive Statistics

- **Total Files:** 101 SQL scripts
- **Total Size:** ~500KB uncompressed
- **Largest Files:** Comprehensive transformation scripts (10-20KB each)
- **Compression:** Compresses to ~100KB if archiving long-term
- **File Types:** 
  - CREATE TABLE/VIEW scripts
  - INSERT/UPDATE/DELETE scripts
  - Diagnostic/debugging queries

## Related Information

### Active SQL
- `../post_import_processing.sql` - The only active SQL file
- Located in parent: `src/sql/`
- Called by: `refresh_production_data.ps1`

### Data Transformation
- `../../transform_production_data_v3_fixed.py` - Python data processor
- Runs before `post_import_processing.sql`
- Handles CSV parsing and initial data loading

### Database Documentation
- `../../docs/CONSOLIDATED_SYSTEM_DOCUMENTATION.md` - Complete schema docs
- `../../docs/PROJECT_REFACTOR_PLAN.md` - System architecture

### Data Pipeline
- `../../refresh_production_data.ps1` - Master orchestrator
- Steps: Backup → Download → Consolidate → Transform (Python) → Post-Process (SQL)

## Retention Policy

- **6-Month Retention:** Keep for reference and troubleshooting
- **12-Month Review:** Evaluate need for continued storage
- **Git History:** All files permanently preserved in git
- **Compression:** Consider compressing if keeping beyond 1 year
- **Recovery:** Can restore from git or this archive anytime

## Important Notes

⚠️ **Do NOT run archived SQL files in production without review**
- These are historical references
- May reference outdated table structures
- May have conflicts with current schema
- Always test in development first

✅ **Use only for reference and understanding**
- Review how things were done historically
- Understand schema evolution
- Guide future similar implementations

🔒 **Current schema is documented and stable**
- See CONSOLIDATED_SYSTEM_DOCUMENTATION.md
- No schema changes needed for active operations
- All functionality working with current schema

## Questions?

For questions about:
- **Current Schema:** See CONSOLIDATED_SYSTEM_DOCUMENTATION.md
- **Data Pipeline:** See refresh_production_data.ps1
- **Specific SQL File:** Check filename and git history
- **Historical Changes:** Review git commits for these files
- **Running Old Queries:** Ask team before executing archived SQL

---

**Note:** These files are kept for historical reference and troubleshooting. Active SQL operations use only `../post_import_processing.sql`. The database is stable, documented, and fully functional.