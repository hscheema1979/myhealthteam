# Patient Panel & HH Column Enhancements - Implementation Summary

**Date**: 2026-03-05
**Author**: Claude Code
**Status**: Code Complete - Ready for Testing and Deployment

---

## Overview

This document summarizes the implementation of 10 new persistent columns for the Patient Panel and Facility Patient Info views. These columns are now editable in the ZMO tabs across all dashboards (Admin, Care Coordinators, Care Providers).

## New Columns Added

| Column Name | Data Type | Description | Valid Values |
|-------------|-----------|-------------|--------------|
| `transportation_status` | TEXT | Patient transportation availability | Available / Unavailable |
| `hh_status` | TEXT | Home Health status | Active / Discharged |
| `medlist_date` | TEXT (Date) | Last updated timestamp for medication list | Date string |
| `smartph_active` | INTEGER | SmartPh enrollment flag | 0 = No, 1 = Yes |
| `language` | TEXT | Patient's preferred language | Free text |
| `rpm_team` | TEXT | RPM category tags | BP, DM, Obese, etc. |
| `bh_team` | INTEGER | Behavioral Health team flag | 0 = No, 1 = Yes |
| `cog_team` | INTEGER | Cognitive team flag | 0 = No, 1 = Yes |
| `pcp_name` | TEXT | Primary Care Physician name | Free text |
| `consents` | TEXT | Consent form status/link | Free text |

---

## Files Modified

### 1. SQL Schema Script
**File**: `src/sql/add_patient_panel_enhancement_columns.sql` (NEW)

Adds 10 new columns to both `patients` and `patient_panel` tables, plus performance indexes.

**Key Features**:
- Adds columns to `patients` table (source of truth)
- Adds columns to `patient_panel` table (display/editing view)
- Creates indexes for frequently queried columns (hh_status, smartph_active, bh_team, cog_team, rpm_team)

### 2. ETL Transformation Script
**File**: `transform_production_data_v3_fixed.py`

**Changes Made**:
1. **CREATE TABLE patient_panel** (lines ~1391-1456)
   - Added 10 new columns to table schema

2. **INSERT INTO patient_panel SELECT** (lines ~1480-1549)
   - Added `p.column_name` mappings to preserve existing data from `patients` table
   - Used `COALESCE` for integer columns (smartph_active, bh_team, cog_team) to default to 0

### 3. Post-Import Processing Script
**File**: `src/sql/post_import_processing.sql`

**Changes Made**:
- Added 6 new indexes for performance optimization (lines ~810-815)
  - `idx_patient_panel_hh_status`
  - `idx_patient_panel_smartph_active`
  - `idx_patient_panel_bh_team`
  - `idx_patient_panel_cog_team`
  - `idx_patient_panel_rpm_team`
  - `idx_patient_panel_transportation_status`

### 4. ZMO Module (UI Layer)
**File**: `src/zmo_module.py`

**Changes Made**:
1. **PATIENT_PANEL_COLUMNS** set (lines ~33-61)
   - Added 10 new columns to enable saving to `patient_panel` table

2. **PATIENTS_TABLE_COLUMNS** set (lines ~63-122)
   - Added 10 new columns to enable saving to `patients` table

3. **format_column_name()** function (lines ~291-318)
   - Added friendly display names for all 10 new columns
   - Examples: "Transportation Status", "HH Status", "SmartPh Active", etc.

4. **Column Configuration** (lines ~870-905)
   - Added specialized configs for different column types:
     - **Selectbox-like columns**: `transportation_status`, `hh_status` with help text
     - **Boolean columns**: `smartph_active`, `bh_team`, `cog_team` with 0/1 values and help text
     - **Date column**: `medlist_date` with date help text
     - **Text columns**: `consents`, `rpm_team`, `pcp_name`, `language` with wide width

---

## Data Flow and Persistence

### Data Storage Strategy
- **Source of Truth**: `patients` table
- **Display/Editing**: `patient_panel` table
- **ETL Mapping**: Columns are mapped from `patients` to `patient_panel` during data refresh

### Data Preservation
During ETL refresh (`transform_production_data_v3_fixed.py`):
1. Columns are selected from `patients` table: `p.column_name`
2. Inserted into `patient_panel` table to preserve existing data
3. Integer columns use `COALESCE(p.column, 0)` to handle NULL values

### UI Editing Flow
When users edit data in ZMO tabs:
1. `save_edits_to_database()` function in `zmo_module.py` detects changes
2. Determines target table (`patient_panel` or `patients`) based on column mapping
3. Updates both tables to maintain consistency
4. Updates `updated_date` timestamp automatically

---

## Dashboard Integration

### ZMO Tab Availability
The new columns are now editable in the ZMO (Patient Data Management) tab across all dashboards:

- ✅ **Admin Dashboard** (`src/dashboards/admin_dashboard.py`)
- ✅ **Care Coordinator Dashboard** (`src/dashboards/care_coordinator_dashboard_enhanced.py`)
- ✅ **Care Provider Dashboard** (`src/dashboards/care_provider_dashboard_enhanced.py`)
- ✅ **Onboarding Dashboard** (`src/dashboards/onboarding_dashboard.py`)
- ✅ **Lead Coordinator Dashboard** (`src/dashboards/lead_coordinator_dashboard.py`)
- ✅ **Coordinator Manager Dashboard** (`src/dashboards/coordinator_manager_dashboard.py`)

All dashboards use the shared `src/zmo_module.py` component, so updates are automatically available everywhere.

### Column Management
Users can:
- Show/hide columns using the column management UI
- Search and filter columns
- Reorder columns for better workflow
- Reset column configuration to defaults

---

## Deployment Instructions

### Step 1: Apply Schema Changes (Local Development)

```bash
# Navigate to project root
cd /home/ubuntu/hscheema1979/myhealthteam

# Apply SQL script to add columns to existing database
# Note: This will skip if columns already exist (ALTER TABLE idempotency)
sqlite3 production.db < src/sql/add_patient_panel_enhancement_columns.sql

# Verify columns were added
sqlite3 production.db "PRAGMA table_info(patients);" | grep -E "(transportation_status|hh_status|medlist_date)"
sqlite3 production.db "PRAGMA table_info(patient_panel);" | grep -E "(transportation_status|hh_status|medlist_date)"
```

### Step 2: Test the Changes Locally

1. **Start the application**:
   ```bash
   streamlit run app.py
   ```

2. **Navigate to any dashboard with ZMO tab** (e.g., Admin Dashboard)

3. **Verify the new columns appear**:
   - Click "Column Management" section
   - Search for new columns (e.g., "Transportation Status", "HH Status")
   - Enable checkboxes to show columns

4. **Test editing**:
   - Edit a value in one of the new columns
   - Click "Save Changes to Database"
   - Refresh and verify the change persisted

### Step 3: Deploy to Production (VPS2)

```bash
# 1. Commit the changes
git add transform_production_data_v3_fixed.py src/sql/post_import_processing.sql src/zmo_module.py src/sql/add_patient_panel_enhancement_columns.sql
git commit -m "Add Patient Panel & HH Enhancement Columns

- Add 10 new persistent columns to patient tracking
- Columns: transportation_status, hh_status, medlist_date, smartph_active,
  language, rpm_team, bh_team, cog_team, pcp_name, consents
- Editable in ZMO tabs across all dashboards
- Data stored in patients table, displayed in patient_panel
- Includes performance indexes for frequently queried columns

Refs: Patient Panel & HH Column Enhancements requirement"
git push origin main

# 2. SSH to production server
ssh server2

# 3. Navigate to application directory
cd /opt/myhealthteam

# 4. Pull latest changes
git pull origin main

# 5. Apply schema changes to production database
sqlite3 production.db < src/sql/add_patient_panel_enhancement_columns.sql

# 6. Restart the service
sudo systemctl restart myhealthteam

# 7. Verify service status
sudo systemctl status myhealthteam

# 8. Check application logs for errors
journalctl -u myhealthteam -f --lines=50
```

### Step 4: Verify Production Deployment

1. **Access the production application**: https://care.myhealthteam.org

2. **Test ZMO tab functionality**:
   - Login as any user with access to dashboards
   - Navigate to ZMO tab
   - Verify new columns appear in column management
   - Test editing a value and saving

3. **Check database**:
   ```bash
   ssh server2
   cd /opt/myhealthteam
   sqlite3 production.db "SELECT patient_id, transportation_status, hh_status, medlist_date FROM patient_panel LIMIT 5;"
   ```

---

## Data Refresh Impact

### ETL Process Behavior
When running `refresh_production_data.ps1`:

1. **Before ETL**: Existing data in new columns is preserved in `patients` table
2. **During ETL**: Columns are mapped from `patients` → `patient_panel`
3. **After ETL**: Both tables contain the same data for these columns

### Important Notes
- ✅ **Data is safe**: Existing entries in new columns will NOT be lost during ETL
- ✅ **Manual entries safe**: User edits in production are preserved
- ✅ **Default values**: NULL for text columns, 0 for integer columns if not set

---

## Testing Checklist

Before deploying to production, verify:

- [ ] SQL script runs without errors
- [ ] Columns appear in both `patients` and `patient_panel` tables
- [ ] New columns appear in ZMO tab column management
- [ ] Columns can be shown/hidden using checkboxes
- [ ] Data can be edited in the UI
- [ ] Changes persist after save and page refresh
- [ ] Integer columns (smartph_active, bh_team, cog_team) accept 0/1 values
- [ ] Text columns accept free-form input
- [ ] Indexes are created for performance
- [ ] No errors in application logs

---

## Rollback Plan

If issues occur after deployment:

```bash
# SSH to production server
ssh server2
cd /opt/myhealthteam

# Option 1: Drop the new columns (reversible)
sqlite3 production.db <<EOF
ALTER TABLE patient_panel DROP COLUMN transportation_status;
ALTER TABLE patient_panel DROP COLUMN hh_status;
ALTER TABLE patient_panel DROP COLUMN medlist_date;
ALTER TABLE patient_panel DROP COLUMN smartph_active;
ALTER TABLE patient_panel DROP COLUMN language;
ALTER TABLE patient_panel DROP COLUMN rpm_team;
ALTER TABLE patient_panel DROP COLUMN bh_team;
ALTER TABLE patient_panel DROP COLUMN cog_team;
ALTER TABLE patient_panel DROP COLUMN pcp_name;
ALTER TABLE patient_panel DROP COLUMN consents;

ALTER TABLE patients DROP COLUMN transportation_status;
ALTER TABLE patients DROP COLUMN hh_status;
ALTER TABLE patients DROP COLUMN medlist_date;
ALTER TABLE patients DROP COLUMN smartph_active;
ALTER TABLE patients DROP COLUMN language;
ALTER TABLE patients DROP COLUMN rpm_team;
ALTER TABLE patients DROP COLUMN bh_team;
ALTER TABLE patients DROP COLUMN cog_team;
ALTER TABLE patients DROP COLUMN pcp_name;
ALTER TABLE patients DROP COLUMN consents;
EOF

# Option 2: Revert code changes (if code has issues)
git revert HEAD
sudo systemctl restart myhealthteam
```

---

## Future Enhancements

Possible improvements to consider:

1. **Dropdown Validation**: Add selectbox widgets for status columns (transportation_status, hh_status) to restrict values
2. **Date Picker**: Use proper date picker for `medlist_date` column
3. **Checkbox UI**: Use checkbox widgets for boolean columns (smartph_active, bh_team, cog_team) instead of 0/1 input
4. **Multi-select**: Use tag/multi-select widget for `rpm_team` column to handle multiple categories
5. **Consent Link**: Make `consents` column a clickable link if it contains URLs
6. **Data Validation**: Add validation rules in `save_edits_to_database()` function
7. **Audit Trail**: Track changes to these columns in audit_log table

---

## Support and Documentation

For questions or issues:
- Review this document for implementation details
- Check application logs: `journalctl -u myhealthteam -f`
- Review CLAUDE.md for database refresh procedures
- Check `docs/technical_debt_duplicate_functions.md` for database patterns

---

**End of Implementation Summary**
