# ZEN Medical Healthcare Management System - AI Coding Guide

## Architecture Overview

This is a **role-based healthcare management system** built with Streamlit, managing 8 distinct user roles with specialized dashboards. The system centers around patient care workflows, provider task management, and billing coordination.

### Core Structure

- **Main App**: `app.py` - Role selection and dashboard routing based on role_id (33=Provider, 34=Admin, 35=Onboarding, 36=Coordinator, 39=DataEntry)
- **Database Layer**: `src/database.py` - SQLite with `production.db` as primary database
- **Dashboards**: `src/dashboards/` - Role-specific interfaces (e.g., `care_provider_dashboard_enhanced.py`)
- **Utilities**: `src/utils/` - Reusable components like `performance_components.py`, `chart_components.py`
- **Config**: `src/config/ui_style_config.py` - Professional healthcare UI standards (NO emojis, professional indicators)

## Key Patterns & Conventions

### Role-Based Dashboard Pattern

```python
def show(user_id, user_role_ids=None):
    # Always check for multiple roles - users can have manager roles (38=CPM, 37=LC, 40=CM)
    has_manager_role = 38 in user_role_ids  # Care Provider Manager

    if has_manager_role:
        # Create tabs with additional management functionality
        tab1, tab2 = st.tabs(["My Work", "Team Management"])
```

### Database Connection Pattern

```python
# Always use this pattern for database operations
conn = database.get_db_connection()  # Returns SQLite connection with row_factory
try:
    result = conn.execute(query, params).fetchall()
finally:
    conn.close()
```

### Database Safety Rules (CRITICAL)

- **NEVER delete, restore, or overwrite database tables or files without explicit user permission**
- **NEVER run DROP TABLE, DELETE FROM entire tables, or database restoration commands**
- **NEVER copy over production.db or backup files without explicit user direction**
- **ALWAYS ask for explicit confirmation before any destructive database operations**
- Primary database file is `production.db` - treat with extreme caution

### Professional UI Standards (CRITICAL)

- **NO emojis** in healthcare interface - use `TextStyle.INFO_INDICATOR` instead of "ℹ️"
- Import from `src.config.ui_style_config` for consistent styling
- Use `get_section_title()` and `get_metric_label()` for standardized headers

### Streamlit Session State Management

```python
# Standard pattern for user context
st.session_state['user_id'] = selected_user['user_id']
st.session_state['role_id'] = selected_role_id
st.session_state['role_name'] = selected_role_name
st.session_state['user_full_name'] = selected_user['full_name']
```

## Data Workflows & Integration

### Primary Data Flow

1. **CSV Import**: Google Sheets → `downloads/` → PowerShell scripts consolidation
2. **Database Import**: `scripts/3_import_to_database.ps1` → `production.db`
3. **Transform**: `scripts/4_transform_data_enhanced.ps1` for data validation
4. **Dashboard Display**: Real-time queries from `production.db`

### Key Tables Architecture

- `users` + `user_roles` (many-to-many) - Role-based access control
- `onboarding_patients` - New patient workflow tracking (stage1_complete, stage2_complete, etc.)
- `patients` + `user_patient_assignments` - Care provider assignments
- `coordinator_monthly_summary` - Billing and performance tracking
- `providers` + `regions` - Geographic assignment logic

## Development Workflows

### Running the Application

```bash
streamlit run app.py  # Always run from root directory
```

### Data Import Workflow

```powershell
cd scripts
./run_complete_workflow.ps1  # Complete 4-step process
# Individual steps: 1_download → 2_consolidate → 3_import → 4_transform
```

### Database Management

- Primary DB: `production.db` (live data)
- Backups: `backups/` directory with timestamped files
- Schema: Reference `actual_schema.sql` or `database_schema.txt`

## Component Reuse Patterns

### Performance Components

Import shared dashboard components from `src.utils.performance_components`:

- `display_coordinator_patient_service_analysis()` - Patient service breakdowns
- `display_provider_monthly_summary()` - Provider performance metrics
- Always pass `coordinator_id` or `user_id` for role-based filtering

### Chart Components

Use `src.utils.chart_components` for consistent visualizations:

- Plotly-based charts with healthcare-appropriate styling
- Standardized color schemes and professional appearance

## Critical Implementation Notes

### Multi-Role User Support

Users can have multiple roles simultaneously - always check `user_role_ids` list:

- Base roles: 33 (Provider), 36 (Coordinator), etc.
- Manager roles: 38 (CPM), 37 (LC), 40 (CM)
- Use role combinations to unlock additional dashboard tabs/features

### Error Handling Pattern

```python
try:
    from optional_module import optional_function
    USE_FEATURE = True
except ImportError:
    USE_FEATURE = False
    # Provide fallback functionality
```

### Legacy Code Management

- `_do_not_use_old_scripts/` - Archived scripts, don't reference
- Always check for "enhanced" versions of dashboards first
- Prefer database functions over direct SQL in dashboard code

## Common Debugging Areas

1. **Role ID mismatches** - Verify role_id mapping in database vs. app.py routing
2. **Database connection leaks** - Always use try/finally with conn.close()
3. **Session state conflicts** - Clear session state when switching users/roles
4. **Import path issues** - Use relative imports from src/ directory
5. **UI styling inconsistencies** - Import and use ui_style_config constants
