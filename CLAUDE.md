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

## SQL Scripts

Historical and utility SQL scripts are in `src/sql/archive/`. These include:
- Monthly table creation scripts
- Data transformation and migration scripts
- Population scripts for summary tables
- Schema enhancement scripts

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

This section documents the process for adding new columns to database tables without losing existing data during data refreshes.

### Overview

The system uses a DROP/CREATE cycle for the `patient_panel` table during data refreshes. To preserve data in new columns, they must be:
1. Added to the source `patients` table
2. Mapped in the ETL transformation script
3. Made available in the UI components

### Step-by-Step Process

#### Step 1: Add Column to `patients` Table

**File**: `src/sql/add_new_columns.sql` (create if not exists)

```sql
-- Add new column to patients table
ALTER TABLE patients ADD COLUMN new_column_name TEXT DEFAULT NULL;

-- Add new column to patient_panel table
ALTER TABLE patient_panel ADD COLUMN new_column_name TEXT DEFAULT NULL;
```

**Execute on both environments**:
- Local: `sqlite3 production.db < src/sql/add_new_columns.sql`
- VPS2: `sqlite3 /opt/myhealthteam/production.db < src/sql/add_new_columns.sql`

#### Step 2: Update ETL Transformation Script

**File**: `transform_production_data_v3_fixed.py`

**Location 1**: `CREATE TABLE patient_panel` statement (around line 973)

Add the new column to the table schema:
```python
CREATE TABLE patient_panel (
    -- ... existing columns ...
    new_column_name TEXT,
    -- ... existing columns ...
)
```

**Location 2**: `INSERT INTO patient_panel` SELECT statement (around line 1054)

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

#### Step 3: Update UI Components (if editable)

**For Admin Dashboard Patient Info tab**:
**File**: `src/dashboards/admin_dashboard.py`

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
**File**: `src/zmo_module.py`

Add the new column to the patient panel data editor configuration (similar to admin_dashboard.py).

#### Step 4: Update Database Queries (if needed)

**File**: `src/database.py`

If the new column needs to be queried or updated, add appropriate functions:
```python
def update_patient_new_column(patient_id, new_value):
    """Update the new column for a patient"""
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE patients SET new_column_name = ? WHERE patient_id = ?",
            (new_value, patient_id)
        )
        conn.commit()
    finally:
        conn.close()
```

#### Step 5: Test the Changes

1. **Local Testing**:
   ```powershell
   # Run the data refresh workflow
   .\refresh_production_data.ps1 -SkipDownload -SkipBackup
   ```

2. **Verify Data Preservation**:
   ```sql
   -- Check that data is preserved in patients table
   SELECT patient_id, new_column_name FROM patients WHERE new_column_name IS NOT NULL LIMIT 5;

   -- Check that data is copied to patient_panel
   SELECT patient_id, new_column_name FROM patient_panel WHERE new_column_name IS NOT NULL LIMIT 5;
   ```

3. **Test UI Editing**:
   - Launch the application: `streamlit run app.py`
   - Navigate to Admin Dashboard > Patient Info tab
   - Edit the new column for a patient
   - Verify the change persists after page refresh

#### Step 6: Deploy to Production

1. **Commit Changes**:
   ```bash
   git add transform_production_data_v3_fixed.py src/dashboards/admin_dashboard.py src/zmo_module.py src/database.py src/sql/add_new_columns.sql
   git commit -m "Add new_column_name to patient tables and UI"
   git push
   ```

2. **Deploy to VPS2**:
   ```bash
   ssh server2 "cd /opt/myhealthteam && git pull"
   ```

3. **Apply Schema Changes on VPS2**:
   ```bash
   ssh server2 "cd /opt/myhealthteam && sqlite3 production.db < src/sql/add_new_columns.sql"
   ```

4. **Restart Service**:
   ```bash
   ssh server2 "sudo systemctl restart myhealthteam"
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
