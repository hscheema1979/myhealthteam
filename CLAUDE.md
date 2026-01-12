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
- `admin_dashboard.py`: System oversight, user management
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

### Database Layer

**`src/database.py`** is the central database module with:
- `DB_PATH`: Database path (production.db or prototype.db)
- `get_db_connection(db_path=None)`: Returns SQLite connection with `row_factory=sqlite3.Row`
- `ensure_monthly_coordinator_tasks_table()`: Creates/validates monthly coordinator_tasks_YYYY_MM tables
- `ensure_monthly_provider_tasks_table()`: Creates/validates monthly provider_tasks_YYYY_MM tables
- Patient, coordinator, provider, and task CRUD functions
- Session management: `create_user_session()`, `get_user_by_session()`, `delete_user_session()`

**Monthly partitioned tables**: Tasks are stored in monthly tables (`coordinator_tasks_YYYY_MM`, `provider_tasks_YYYY_MM`) for performance and data organization. These tables include `source_system` column to track data origin (CSV_IMPORT, MANUAL, DASHBOARD, WORKFLOW).

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
