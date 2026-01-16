# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Run the Streamlit application (main entry point)
streamlit run app.py

# The application runs on http://localhost:8501 by default
```

## Database Selection

The application supports two database modes controlled by the `USE_PROTOTYPE_MODE` flag file:

- **Production mode** (default): Uses `production.db` in the project root
- **Prototype mode**: Create a file named `USE_PROTOTYPE_MODE` in the project root to use `prototype.db` instead

Database path is configured in `src/database.py` via `DB_PATH`. The database file is located at the project root level.

## Architecture Overview

### Entry Point and Routing

- **`app.py`**: Main Streamlit application entry point. Handles authentication, routing to role-based dashboards, and login UI.
- **`src/auth_module.py`**: `AuthenticationManager` class handles user sessions, password authentication (SHA-256 hashed), persistent login (30-day sessions via `user_sessions` table), and user impersonation for admins.

### Role-Based Access Control

Users have multiple roles stored in `user_roles` table. Role IDs:
- `33`: Care Provider
- `34`: Admin
- `35`: Onboarding
- `36`: Care Coordinator
- `37`: Lead Coordinator
- `38`: Care Provider Manager
- `39`: Data Entry
- `40`: Coordinator Manager

The `get_primary_dashboard_role()` method in `auth_module.py` determines which dashboard to show based on role precedence: Case Manager (40) > Lead Coordinator (37) > Admin (34) > Provider (33) > Coordinator (36) > Onboarding (35) > Data Entry (39).

Users with multiple roles can use the **Role Switcher** in the sidebar to change dashboards.

### Dashboard Modules

Located in `src/dashboards/`:
- `admin_dashboard.py`: System oversight, user management, Patient Info tab with editable notes columns (labs_notes, imaging_notes, general_notes)
- `care_coordinator_dashboard_enhanced.py`: Patient assignment, workflow coordination, billing
- `care_provider_dashboard_enhanced.py`: Patient management, task tracking
- `onboarding_dashboard.py`: New patient/provider onboarding
- `data_entry_dashboard.py`: Patient data input
- `lead_coordinator_dashboard.py`: Team oversight
- `coordinator_manager_dashboard.py`: Enhanced coordinator management
- `workflow_module.py`: Workflow template/instance management (business logic, no UI)
- `coordinator_tasks_module.py`: Task tracking for coordinators
- `task_review_component.py`: Generic task review UI component
- `coordinator_task_review_component.py`: Coordinator-specific task review

**ZMO Module** (`src/zmo_module.py`): ZMO (Zen Medical Onboarding") module for patient monitoring and management. Features:
- Patient panel with editable notes columns (labs_notes, imaging_notes, general_notes) for all roles (coordinators, providers, onboarding team)
- Role-based access to patient data
- Integration with patient_panel table

### Database Layer

**`src/database.py`** is the central database module with:
- `DB_PATH`: Database path (production.db or prototype.db)
- `get_db_connection(db_path=None)`: Returns SQLite connection with `row_factory=sqlite3.Row`
- `ensure_monthly_coordinator_tasks_table()`: Creates/validates monthly coordinator_tasks_YYYY_MM tables
- `ensure_monthly_provider_tasks_table()`: Creates/validates monthly provider_tasks_YYYY_MM tables
- Patient, coordinator, provider, and task CRUD functions
- Session management: `create_user_session()`, `get_user_by_session()`, `delete_user_session()`
- `get_users_by_role(role_identifier)`: Retrieves users by role ID or role name (supports multiple input patterns)

**Role-Based User Retrieval**: The `get_users_by_role()` function supports flexible role identification:
- Role ID (int): `get_users_by_role(33)` or `get_users_by_role(36)`
- Role Constant: `get_users_by_role(ROLE_CARE_PROVIDER)`
- Role Abbreviation (str): `get_users_by_role("CP")` or `get_users_by_role("CC")`
- Full Role Name (str): `get_users_by_role("Care Coordinator")`

Returns list of dicts with keys: `user_id`, `username`, `full_name`. Used by 8 dashboards for user assignment and filtering.

**Monthly partitioned tables**: Tasks are stored in monthly tables (`coordinator_tasks_YYYY_MM`, `provider_tasks_YYYY_MM`) for performance and data organization. These tables include `source_system` column to track data origin (CSV_IMPORT, MANUAL, DASHBOARD, WORKFLOW).

**Patient Notes Columns**: The `patients` and `patient_panel` tables include three editable notes columns for clinical documentation:
- `labs_notes`: Notes related to laboratory results and testing
- `imaging_notes`: Notes related to imaging studies (X-rays, CT scans, MRIs, etc.)
- `general_notes`: General clinical notes and observations

These columns are editable in:
- Admin Dashboard (Patient Info tab)
- ZMO Module (all roles: coordinators, providers, onboarding team)

**ETL Preservation**: The data refresh workflow (`transform_production_data_v3_fixed.py`) preserves notes columns during `patient_panel` table rebuilds by mapping them from the `patients` table. Notes are not overwritten during CSV imports.

### Core Utilities

**`src/core_utils.py`**: Shared utility functions
- `get_user_role_ids(user_id)`: Returns list of role IDs for a user
- `aggregate_patient_data_by_patient_id()`: Aggregates patient data to remove coordinator-patient duplicates
- `prepare_patient_summary_with_facility_mapping()`: Prepares patient summaries with facility names

**`src/utils/workflow_utils.py`**: Workflow business logic (no Streamlit UI)

### Database Synchronization (db-sync/)

The `db-sync/` directory contains scripts for syncing `production.db` between dev (SRVR/Windows) and production (VPS2/Linux) via SSH:

- `bin/sync_csv_data.ps1`: Smart CSV sync - only syncs rows with `source_system = 'CSV_IMPORT'`, preserves manual entries
- `bin/test_connection.ps1`: Verify SSH and database access
- `bin/setup_scheduled_task.ps1`: Configure automatic 15-min sync

SSH alias `server2` is used (configured in `~/.ssh/config`).

### Data Import Pipeline

Located in `scripts/` (PowerShell) and `src/utils/` (Python):
1. Download external data files
2. Consolidate and transform CSV data
3. Import to database with `source_system = 'CSV_IMPORT'`

## Key Patterns and Conventions

### Database Queries

- Use `get_db_connection()` from `src.database`
- Connections use `row_factory=sqlite3.Row` for dict-like row access
- Always close connections in `finally` blocks or use context managers
- Monthly tables are auto-created via `ensure_monthly_*_tasks_table()`

### Streamlit Patterns

- Use `@st.cache_data(ttl=...)` for expensive database queries
- Session state is used for user authentication (`user_id`, `user_role_ids`, `authenticated_user`)
- Use `st.rerun()` after authentication state changes

**Widget Key Conflict Pattern**: When creating Streamlit widgets with keys, avoid the common error "widget was created with a default value but also had its value set via the Session State API":

```python
# WRONG - causes conflict
st.session_state[f"{key}_patient_type"] = "Follow Up"  # Pre-sets session state
st.selectbox("Type", options, index=1, key=f"{key}_patient_type")  # Also has index

# CORRECT - let the widget manage its own state
st.selectbox("Type", options, key=f"{key}_patient_type")  # No index, no pre-set
```

If you need to initialize session state before widget creation, do NOT provide an `index` parameter - the session state value becomes the default.

### Patient ID Normalization

Patient IDs can be integers or strings. Use `normalize_patient_id(patient_id, conn)` from `src.database` to ensure consistent string representation in database operations.

### Workflow System

- `workflow_templates`: Template definitions with steps
- `workflow_steps`: Individual steps within templates (task_name, owner, deliverable, cycle_time)
- `workflow_instances`: Active workflow instances for patients
- Use `create_workflow_instance()` from `workflow_module.py` to start workflows

## Testing

Test files are in `src/utils/` with `test_*.py` prefix:
- `test_coordinator_basic.py`
- `test_coordinator_functions.py`
- `test_dashboard_functions.py`
- `test_updated_coordinator_functions.py`

## Data Refresh Workflow

**`refresh_production_data.ps1`**: Main script for downloading and importing fresh healthcare data from external sources.

### Usage

```powershell
# Full refresh (download + import + backup)
.\refresh_production_data.ps1

# Skip download (use existing downloaded files)
.\refresh_production_data.ps1 -SkipDownload

# Skip backup (faster, use with caution)
.\refresh_production_data.ps1 -SkipBackup

# Sync CSV data to production VPS2 after import
.\refresh_production_data.ps1 -SyncToProduction
```

### Workflow Steps

1. **Backup**: Creates timestamped backup of `production.db` in `backups/`
2. **Download**: Downloads fresh data from Google Sheets via `scripts/1_download_files_complete.ps1`
3. **Consolidate**: Merges and cleans CSV files via `scripts/2_consolidate_files.ps1` (**CRITICAL STEP**)
4. **Transform**: Runs `transform_production_data_v3_fixed.py` to import data
5. **Post-Process**: Runs `src/sql/post_import_processing.sql` to rebuild views and summaries
6. **Sync** (optional): Smart sync to VPS2 via `db-sync/bin/sync_csv_data.ps1`

### CRITICAL: The Consolidation Step

**The consolidation step (`2_consolidate_files.ps1`) is REQUIRED and CANNOT be skipped.**

This step performs essential data cleaning that the ETL depends on:

1. **Combines monthly CSV files**: Merges CMLog_*, PSL_ZEN-*, and RVZ_ZEN-* files into single cmlog.csv, psl.csv, and rvz.csv
2. **Cleans ZMO_Main.csv** via `src/utils/clean_csv.py`:
   - Removes 178+ "Unnamed:" columns (Google Sheets exports ALL columns that ever existed)
   - Removes 10+ completely empty columns
   - Limits to 53 columns (removes extraneous data beyond column 53)
   - Fixes column names by stripping newlines (e.g., `Assigned \n Reg Prov` → `Assigned  Reg Prov`)

**Why this matters**: Google Sheets CSV exports include every column that has ever existed in the spreadsheet, even if now empty. The raw ZMO_Main.csv download has **248 columns** with malformed column names. The ETL script cannot correctly parse provider/coordinator assignments from the raw file. After cleaning, the file has **53 columns** with properly formatted column names.

**Never skip this step** - running the ETL directly on downloaded files will result in failed provider/coordinator lookups (provider_id = 0, coordinator_id = 0).

### Provider/Coordinator Name Normalization

The ETL (`transform_production_data_v3_fixed.py`) includes a `normalize_name_key()` function that handles provider/coordinator name matching from ZMO data:

**What it does**:
- Uppercases names
- Removes punctuation (commas, periods, dashes, underscores)
- Removes titles/suffixes: NP, PA, MD, DO, ZZ, DDS, RN
- Normalizes spaces

**Examples of normalized matches**:
- "Dabalus NP, Eden" → "DABALUS EDEN" → matches user_id 9 ("Dabalus, Eden")
- "Melara Lara NP, Claudia" → "MELARA LARA CLAUDIA" → matches user_id 7 ("Melara, Claudia")
- "Melara ZZ, Claudia" → "MELARA CLAUDIA" → matches user_id 7 ("Melara, Claudia")

**Provider mapping sources** (in order of precedence):
1. Staff codes from `staff_code_mapping` table
2. User aliases and usernames
3. Normalized full names from `users` table
4. 3-character last name codes

### Important Notes

- The ETL process uses `transform_production_data_v3_fixed.py` which performs a DROP/CREATE cycle on the `patient_panel` table
- Custom columns (like notes columns) must be mapped in the ETL script to be preserved
- **Never use `-SkipDownload` without manually running the consolidation step first** - the ETL depends on cleaned CSV files
- The smart sync preserves manual entries on VPS2 (only syncs `source_system = 'CSV_IMPORT'` rows)

## Scheduled Workflows

**`src/workflows/daily_summary_update.py`**: Automated daily script to update billing and payroll summary tables. Runs at 5:00 AM via Windows Task Scheduler.

### Updates Performed

- Weekly Provider Billing Summary (`provider_weekly_summary_with_billing`)
- Weekly Provider Payroll Summary (`provider_weekly_payroll_status`)
- Monthly Coordinator Billing Summary (`coordinator_monthly_summary`)

### Running Manually

```bash
python src/workflows/daily_summary_update.py
```

### Key Features

- Processes only new/updated records
- Maintains data integrity during updates
- Includes error handling and logging to `logs/daily_summary_update.log`
- Preserves historical data with upsert logic
- Calculates week dates as Monday-Sunday for billing periods

## Billing System Architecture

**`src/billing/weekly_billing_processor.py`**: Handles automated weekly billing report generation with carryover logic.

### Key Components

- **Billing Week Calculation**: Weeks are Monday-Sunday, formatted as `YYYY-WW`
- **Carryover Logic**: Unbilled tasks from previous weeks are automatically carried over to current week
- **Billing Status Flow**: Not Billed → Billed → Invoiced → Claim Submitted → Insurance Processed → Approve to Pay → Paid
- **Status History Tracking**: All status changes logged in `billing_status_history` table

### Tables

- `task_billing_codes`: Master table for billing codes with location/patient type mappings, min/max minutes
- `provider_task_billing_status`: Main billing tracking table with flags for each status
- `billing_status_history`: Audit trail of all status changes
- `provider_weekly_summary_with_billing`: Aggregated weekly summaries by provider and billing code

### Billing Code Query Pattern

```python
# Simplified billing lookup - only location_type and patient_type needed
billing_options = database.get_billing_codes(
    location_type="Home",      # Home, Office, or Telehealth
    patient_type="Follow Up"   # Follow Up, New, Acute, Cognitive, TCM-7, TCM-14
)
```

**Note**: The `service_type` parameter was removed - `patient_type` is sufficient for lookups.

### Patient Type / Location Constraints

| Patient Type | Valid Locations | Notes |
|--------------|----------------|-------|
| Follow Up | Home, Office, Telehealth | Default |
| New | Home, Office, Telehealth | Default |
| Acute | Telehealth, Office | Home NOT allowed |
| Cognitive | Home, Office | Telehealth NOT allowed |
| TCM-7 | Home, Office, Telehealth | Code: 99496 |
| TCM-14 | Home, Office, Telehealth | Code: 99495 |

### Processing Flow

1. Carry over unbilled tasks from previous weeks
2. Mark original tasks as carried over
3. Mark eligible current week tasks as "Billed" (has billing code, minutes > 0, not "Not_Billable")
4. Log all status changes in history table

### Running Billing Processing

```python
from src.billing.weekly_billing_processor import WeeklyBillingProcessor

processor = WeeklyBillingProcessor()
processor.setup_billing_system()  # First time only
result = processor.process_weekly_billing()
```

### Reference Data for Min/Max Minutes

When updating billing codes, reference data is available in the backup database:
- Path: `db-sync/backups/production_backup_before_table_sync_20260113_124312.db`
- Table: `reference_task_billing_codes`
- Contains authoritative min_minutes and max_minutes for CPT codes

## UI Styling Conventions

**`src/config/ui_style_config.py`**: Centralized styling configuration for professional healthcare appearance.

### Key Principles

- **No Emojis**: `USE_EMOJIS = False` for professional healthcare environment
- **Professional Indicators**: Use text indicators like "[HIGH]", "[MEDIUM]", "[LOW]" instead of emojis
- **Consistent Headers**: Use `get_section_title()` for all section headers
- **Metric Labels**: Use `get_metric_label()` for all metric displays

### Usage Examples

```python
from src.config.ui_style_config import get_section_title, get_metric_label, TextStyle, apply_custom_css

# Apply professional styling
apply_custom_css()

# Section headers (no emojis)
st.header(get_section_title("Coordinator Performance"))

# Metric labels
col1.metric(get_metric_label("tasks", is_current_month=True), value)

# Status indicators
st.info(f"{TextStyle.INFO_INDICATOR}: Data updated successfully")
```

### Color Scheme

- Primary Blue: `#1f77b4` (current period data)
- Success Green: `#2ca02c`
- Warning Orange: `#ff7f0e`
- Error Red: `#d62728`
- Neutral Gray: `#7f7f7f` (historical data)

## VPS Deployment

### Quick Deploy to VPS2

```bash
# SSH to production server
ssh server2

# Navigate to application directory
cd /opt/myhealthteam

# Pull latest changes
git pull origin main

# Restart the service
sudo systemctl restart myhealthteam

# Verify service status
sudo systemctl status myhealthteam
```

### Applying Schema Changes on VPS2

When adding new columns or tables:

```bash
ssh server2 "cd /opt/myhealthteam && sqlite3 production.db < src/sql/add_new_columns.sql"
```

### Production Environment

- **Service**: `myhealthteam` (systemd)
- **Database**: `/opt/myhealthteam/production.db`
- **Logs**: `journalctl -u myhealthteam -f`
- **Redirect URI**: `https://care.myhealthteam.org`

## SQL Scripts

Historical and utility SQL scripts are in `src/sql/archive/`. Active SQL scripts include:

**Core ETL and Setup:**
- `post_import_processing.sql`: Rebuilds views, updates patient data, populates summaries after ETL
- `create_weekly_billing_system.sql`: Creates billing system tables
- `populate_weekly_billing_system.sql`: Migrates existing data to billing system
- `weekly_billing_report_generator.sql`: Generates billing reports

**Schema Migration Scripts:**
- `add_notes_columns.sql`: Adds labs_notes, imaging_notes, general_notes to patient tables
- `add_next_appointment_date.sql`: Adds next_appointment_date column
- `add_appointment_contact_columns.sql`: Adds appointment-related columns
- `add_is_active_to_task_billing_codes.sql`: Adds is_active flag to billing codes
- `migrate_add_billing_columns.sql`: Adds billing-related columns
- `migrate_billing_codes.sql`: Billing code migration
- `update_billing_codes_with_home_locations.sql`: Adds Home/Telehealth for TCM/Cognitive, updates min/max minutes

**Workflow Scripts:**
- `populate_workflow_templates_from_csv.sql`: Imports workflow templates
- `add_general_phone_inquiries_workflow.sql`: General phone workflow setup
- `fix_workflow_typos.sql`: Fixes workflow template issues

## Google OAuth Setup (PRODUCTION - VPS2)

### Configuration

**Google Client ID**: `298448117337-5eno2h0163etcl9vnqjjj524k48ae0d2.apps.googleusercontent.com`
**Production Redirect URI**: `https://care.myhealthteam.org`

### Environment Variables on VPS2

The systemd service file `/etc/systemd/system/myhealthteam.service` must have:
```
Environment=GOOGLE_REDIRECT_URI=https://care.myhealthteam.org
```

### Google Cloud Console Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Client ID: `298448117337-5eno2h0163etcl9vnqjjj524k48ae0d2.apps.googleusercontent.com`
3. Authorized redirect URIs must include EXACTLY:
   - `https://care.myhealthteam.org` (no trailing slash)
   - `http://localhost:8501` (local dev)
   - `http://localhost:8502` (local dev)

### KNOWN ISSUE - OAuth Callback Double-Execution

**Problem**: After Google OAuth redirect, the callback handler is being called twice due to Streamlit reruns. The first execution succeeds (gets token), but the second fails with `invalid_grant` because the authorization code is one-time use only.

**Files Involved**:
- `src/auth_module.py` - OAuth callback handling in `render_login_sidebar()` (lines ~709-732)
- `src/google_oauth.py` - Token exchange and user creation

**Root Cause**: Streamlit reruns the entire script on every interaction. After successful OAuth, the script reruns and the callback handler tries to process the same `code` parameter again.

**Fix Needed**:
1. After successful OAuth, immediately clear query params AND set a flag in session state to prevent re-processing
2. Or use a different approach (e.g., dedicated callback endpoint, state parameter validation)

**Current Workaround**: None - Google login is broken on production.

## Known Technical Debt

### Duplicate `get_users_by_role` Functions

**Issue**: There are 3 functions in `src/database.py` that perform similar user retrieval by role operations:
- Line 874: `get_users_by_role(role_identifier)` - Returns `user_id, username, full_name, role_name`
- Line 2973: `get_users_by_role_name(role_name)` - Returns `user_id, username, full_name` (only accepts role_name string)
- Line 3235: `get_users_by_role(role_identifier)` - Returns `user_id, username, full_name` (missing role_name)

**Current State**: Function at line 3235 is being used by all 22 callers across 8 dashboards. The function at line 874 includes an unused `role_name` column. The function at line 2973 is redundant.

**Documentation**: See `docs/technical_debt_duplicate_functions.md` for detailed analysis, usage patterns, and resolution plan.

**Impact**: System is stable but maintenance burden exists. Changes must be made in multiple places.

**Resolution Plan**: Consolidate to single function (line 3235), delete duplicates, update docstring. Estimated 2-4 hours including testing.

## Adding New Columns to Tables

This section documents the complete process for adding new columns to database tables without losing existing data during data refreshes.

### Overview

The system uses a DROP/CREATE cycle for the `patient_panel` table during data refreshes. To preserve data in new columns, they must be:
1. Added to the source `patients` table
2. Added to the `patient_panel` table
3. Mapped in the ETL transformation script (`transform_production_data_v3_fixed.py`)
4. **CRITICAL**: Mapped in the post-import processing script (`post_import_processing.sql`)
5. Made available in the UI components

### Complete File Paths

All files that must be updated when adding new columns:

| File | Purpose | Location |
|------|---------|----------|
| `d:\Git\myhealthteam2\Dev\src\sql\add_new_columns.sql` | SQL script to add columns to database tables | Create this file |
| `d:\Git\myhealthteam2\Dev\transform_production_data_v3_fixed.py` | ETL transformation script - maps columns during data refresh | Lines ~973 (CREATE TABLE), ~1054 (INSERT) |
| `d:\Git\myhealthteam2\Dev\src\sql\post_import_processing.sql` | Post-import processing - CRITICAL for data preservation | Line ~674 (CREATE TABLE patient_panel) |
| `d:\Git\myhealthteam2\Dev\src\dashboards\admin_dashboard.py` | Admin dashboard UI - Patient Info tab | Add to column_config |
| `d:\Git\myhealthteam2\Dev\src\zmo_module.py` | ZMO module UI - patient panel | Add to column_config |
| `d:\Git\myhealthteam2\Dev\src\database.py` | Database queries (if needed) | Add update functions |

### Step-by-Step Process

#### Step 1: Create SQL Script to Add Columns

**File**: `d:\Git\myhealthteam2\Dev\src\sql\add_new_columns.sql` (create if not exists)

```sql
-- Add new column to patients table
ALTER TABLE patients ADD COLUMN new_column_name TEXT DEFAULT NULL;

-- Add new column to patient_panel table
ALTER TABLE patient_panel ADD COLUMN new_column_name TEXT DEFAULT NULL;
```

**Execute on local database**:
```powershell
Get-Content src\sql\add_new_columns.sql | sqlite3 production.db
```

**Execute on VPS2 database** (after deployment):
```bash
ssh server2 "cd /opt/myhealthteam && sqlite3 production.db < src/sql/add_new_columns.sql"
```

#### Step 2: Update ETL Transformation Script - CREATE TABLE

**File**: `d:\Git\myhealthteam2\Dev\transform_production_data_v3_fixed.py`

**Location**: `CREATE TABLE patient_panel` statement (around line 973)

Add the new column to the table schema:
```python
CREATE TABLE patient_panel (
    -- ... existing columns ...
    new_column_name TEXT,
    -- ... existing columns ...
)
```

#### Step 3: Update ETL Transformation Script - INSERT

**File**: `d:\Git\myhealthteam2\Dev\transform_production_data_v3_fixed.py`

**Location**: `INSERT INTO patient_panel` SELECT statement (around line 1054)

Add the new column to the SELECT list:
```python
INSERT INTO patient_panel
SELECT
    -- ... existing columns ...
    p.new_column_name,
    -- ... existing columns ...
FROM patients p
-- ... joins ...
```

**Important**: The column must be selected from the `patients` table (aliased as `p`) to preserve existing data.

#### Step 4: Update Post-Import Processing Script (CRITICAL)

**File**: `d:\Git\myhealthteam2\Dev\src\sql\post_import_processing.sql`

**Location**: `CREATE TABLE patient_panel AS` statement (around line 674)

**This is the most critical step** - if you skip this, data will be lost after the ETL refresh!

Add the new column to the SELECT list:
```sql
CREATE TABLE patient_panel AS
SELECT DISTINCT
    -- ... existing columns ...
    p.new_column_name,
    -- ... existing columns ...
FROM patients p
LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id AND pa.status = 'active'
LEFT JOIN users u_prov ON pa.provider_id = u_prov.user_id
LEFT JOIN users u_coord ON pa.coordinator_id = u_coord.user_id;
```

#### Step 5: Update UI Components (if editable)

**For Admin Dashboard Patient Info tab**:
**File**: `d:\Git\myhealthteam2\Dev\src\dashboards\admin_dashboard.py`

Add the new column to the `st.data_editor` configuration:
```python
edited_df = st.data_editor(
    df,
    column_config={
        # ... existing columns ...
        "new_column_name": st.column_config.TextColumn(
            "New Column Label",
            help="Description of what this column is for"
        ),
    },
    # ... existing config ...
)
```

**For ZMO Module**:
**File**: `d:\Git\myhealthteam2\Dev\src\zmo_module.py`

Add the new column to the patient panel data editor configuration (similar to admin_dashboard.py).

#### Step 6: Test the Changes Locally

1. **Run the data refresh workflow**:
   ```powershell
   .\refresh_production_data.ps1 -SkipDownload -SkipBackup
   ```

2. **Verify column exists in both tables**:
   ```powershell
   # Check patients table
   sqlite3 production.db "PRAGMA table_info(patients);" | Select-String "new_column_name"

   # Check patient_panel table
   sqlite3 production.db "PRAGMA table_info(patient_panel);" | Select-String "new_column_name"
   ```

3. **Verify data preservation**:
   ```sql
   -- Check that data is preserved in patients table
   SELECT patient_id, new_column_name FROM patients WHERE new_column_name IS NOT NULL LIMIT 5;

   -- Check that data is copied to patient_panel
   SELECT patient_id, new_column_name FROM patient_panel WHERE new_column_name IS NOT NULL LIMIT 5;
   ```

4. **Test UI Editing**:
   - Launch the application: `streamlit run app.py`
   - Navigate to Admin Dashboard > Patient Info tab
   - Edit the new column for a patient
   - Verify the change persists after page refresh

#### Step 7: Deploy to Production

1. **Commit Changes**:
   ```bash
   git add transform_production_data_v3_fixed.py src/sql/post_import_processing.sql src/dashboards/admin_dashboard.py src/zmo_module.py src/database.py src/sql/add_new_columns.sql
   git commit -m "Add new_column_name to patient tables and UI"
   git push origin main
   ```

2. **Deploy to VPS2**:
   ```bash
   ssh server2 "cd /opt/myhealthteam && git pull origin main"
   ```

3. **Apply Schema Changes on VPS2**:
   ```bash
   ssh server2 "cd /opt/myhealthteam && sqlite3 production.db < src/sql/add_new_columns.sql"
   ```

4. **Restart Service**:
   ```bash
   ssh server2 "sudo systemctl restart myhealthteam"
   ```

5. **Verify on VPS2**:
   ```bash
   ssh server2 "cd /opt/myhealthteam && sqlite3 production.db 'PRAGMA table_info(patient_panel);' | grep new_column_name"
   ```

### Column Types and Defaults

When adding new columns, consider the appropriate data type:

| Data Type | Use Case | Example |
|-----------|----------|---------|
| `TEXT` | Free-form text, notes, descriptions | `notes TEXT` |
| `INTEGER` | Whole numbers, counts, flags | `count INTEGER DEFAULT 0` |
| `REAL` | Decimal numbers, percentages | `percentage REAL DEFAULT 0.0` |
| `DATE` | Date values | `created_date DATE` |
| `TIMESTAMP` | Date and time values | `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |

### Common Patterns

#### Pattern 1: Notes Columns (Free-form text)

```sql
ALTER TABLE patients ADD COLUMN clinical_notes TEXT DEFAULT NULL;
```

```python
# In transform_production_data_v3_fixed.py
CREATE TABLE patient_panel (
    # ... existing columns ...
    clinical_notes TEXT,
    # ... existing columns ...
)

INSERT INTO patient_panel
SELECT
    # ... existing columns ...
    p.clinical_notes,
    # ... existing columns ...
FROM patients p
```

#### Pattern 2: Count Columns (Integer with default)

```sql
ALTER TABLE patients ADD COLUMN visit_count INTEGER DEFAULT 0;
```

```python
# In transform_production_data_v3_fixed.py
CREATE TABLE patient_panel (
    # ... existing columns ...
    visit_count INTEGER DEFAULT 0,
    # ... existing columns ...
)

INSERT INTO patient_panel
SELECT
    # ... existing columns ...
    COALESCE(p.visit_count, 0) as visit_count,
    # ... existing columns ...
FROM patients p
```

#### Pattern 3: Status Columns (Enumerated values)

```sql
ALTER TABLE patients ADD COLUMN referral_status TEXT DEFAULT 'pending';
```

```python
# In transform_production_data_v3_fixed.py
CREATE TABLE patient_panel (
    # ... existing columns ...
    referral_status TEXT DEFAULT 'pending',
    # ... existing columns ...
)

INSERT INTO patient_panel
SELECT
    # ... existing columns ...
    COALESCE(p.referral_status, 'pending') as referral_status,
    # ... existing columns ...
FROM patients p
```

### Verification Checklist

Before deploying to production, verify:

- [ ] Column added to `patients` table locally
- [ ] Column added to `patient_panel` table locally
- [ ] Column added to `CREATE TABLE patient_panel` in `transform_production_data_v3_fixed.py`
- [ ] Column added to `INSERT INTO patient_panel` SELECT in `transform_production_data_v3_fixed.py`
- [ ] UI components updated (if editable)
- [ ] Data refresh workflow tested locally
- [ ] Data preservation verified in both tables
- [ ] Changes committed to Git
- [ ] Schema changes applied on VPS2
- [ ] Code deployed to VPS2
- [ ] Service restarted on VPS2
- [ ] Production verified

### Troubleshooting

**Issue**: Column not appearing in UI after refresh
- **Cause**: Column not added to `st.data_editor` column_config
- **Fix**: Add column configuration to the relevant dashboard file

**Issue**: Data lost after data refresh
- **Cause**: Column not mapped in `INSERT INTO patient_panel` SELECT statement
- **Fix**: Add `p.column_name` to the SELECT list in `transform_production_data_v3_fixed.py`

**Issue**: Schema error on VPS2
- **Cause**: Column not added to production database
- **Fix**: Run the ALTER TABLE script on VPS2: `sqlite3 /opt/myhealthteam/production.db < src/sql/add_new_columns.sql`

**Issue**: Type mismatch errors
- **Cause**: Column data type differs between tables
- **Fix**: Ensure consistent data types in both `patients` and `patient_panel` tables

### Existing Notes Columns (Reference)

The system currently has three notes columns that follow this pattern:
- `labs_notes`: Laboratory results and testing notes
- `imaging_notes`: Imaging studies notes (X-rays, CT scans, MRIs)
- `general_notes`: General clinical notes and observations

These columns are:
- Stored in both `patients` and `patient_panel` tables
- Mapped in `transform_production_data_v3_fixed.py` (lines 1021-1023, 1103-1105)
- Editable in Admin Dashboard (Patient Info tab)
- Editable in ZMO Module (all roles)
- Preserved during data refreshes
