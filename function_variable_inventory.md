# Function and Variable Inventory: database.py & Dashboards

This document lists all functions, variables, and key calls across `database.py` and the main dashboard scripts. Use this as a reference for code analysis and refactoring.

---

## 1. database.py

### Key Variables

- `DB_PATH`: Path to SQLite database (usually 'production.db')

### Functions (selected, see full file for all)

- `get_db_connection(db_path=None)`
- `normalize_patient_id(patient_id, conn=None)`
- `get_all_users()`
- `get_all_roles()`
- `get_user_roles_by_user_id(user_id)`
- `get_user_role_ids(user_id)`
- `add_user_role(user_id, role_id)`
- `remove_user_role(user_id, role_id)`
- `set_primary_role(user_id, role_id)`
- `get_user_roles()`
- `get_users()`
- `get_user_by_id(user_id)`
- `get_users_by_role(role_identifier)`
- `get_user_patient_assignments(user_id)`
- `get_all_patients()`
- `get_patient_details_by_id(patient_id)`
- `get_all_patient_status_types()`
- `update_patient_status(patient_id, status)`
- `get_coordinator_monthly_minutes_live()`
- `get_coordinator_performance_metrics(user_id)`
- `get_provider_performance_metrics()`
- `save_coordinator_task(coordinator_id, patient_id, task_date, task_description, duration_minutes, notes)`
- `save_daily_task(provider_id, patient_id, task_date, task_description, notes, billing_code=None)`
- `get_onboarding_queue_stats()`
- `get_onboarding_tasks_by_role(role_id, user_id=None)`
- `get_onboarding_patient_details(onboarding_id)`
- `get_onboarding_queue()`
- `create_onboarding_workflow_instance(patient_data, pot_user_id)`
- `transfer_onboarding_to_patient_table(onboarding_id)`

---

## 2. Dashboards (src/dashboards/\*.py)

### care_coordinator_dashboard_enhanced.py

- `def show(user_id, user_role_ids=None)`
  - Variables: `user_role_ids`, `has_lc_role`, `has_cm_role`, `has_management_role`, `role_text`, `tab1`, `tab2`, `tab3`, `tab4`
  - Calls: `show_coordinator_patient_list`, `display_coordinator_monthly_summary`, `display_coordinator_weekly_summary`, `database.get_users_by_role`, `database.get_onboarding_queue_stats`

### care_provider_dashboard_enhanced.py

- `def show(user_id, user_role_ids=None)`
  - Variables: `user_role_ids`, `has_cpm_role`, `onboarding_queue`, `tab1`, `tab2`, `tab3`
  - Calls: `database.get_provider_onboarding_queue`, (commented: `display_provider_monthly_summary`, `display_provider_weekly_summary_chart`)

### admin_dashboard.py

- `def show()`
  - Variables: `show_unfiltered_patient_summary`, `MITO_AVAILABLE`, `user_id`, `tab_role`, `tab1`, `tab_onboard`, `tab_coord_tasks`, `tab_prov_tasks`, `tab3`, `tab_test`, `summary_rows`, `total_minutes`, `df_summary`, `col_patient`, `col_coord`, `conn`, `now`, `year`, `month`, `table_name`, `table_exists`, `tasks_df`
  - Calls: `db.get_coordinator_monthly_minutes_live`, `db.get_db_connection`, `pd.read_sql_query`

### data_entry_dashboard.py

- `def show()`
  - Variables: `first_name`, `last_name`, `date_of_birth`, `submitted`
  - Calls: (likely patient creation/entry functions)

### lead_coordinator_dashboard.py

- `def show()`
  - Variables: `user_id`, `lead_coordinator_info`, `coordinators`, `coordinator_usernames`, `selected_coordinator_username`, `task_description`, `patient_name`, `submitted`
  - Calls: `get_user_by_id`, `get_users_by_role`

### onboarding_dashboard.py

- `ONBOARDING_STEPS` (list)
- `def show_workflow_stepper(patient_data)`
  - Variables: `current_step`, `stage_field`, `cols`, `step_num`, `title`, `description`, `is_completed`, `is_current`, `is_future`, `circle_style`, `icon`

---

## 3. Common Patterns

- All dashboards use a `show()` function as the entry point.
- Most dashboards use role checks and tabbed layouts.
- Database access is via the `database` module, with functions for user, patient, and task data.
- Patient panels are built from `user_patient_assignments` and `patients`.
- Task summaries use monthly partitioned tables.

---

_This inventory can be expanded with more detail (e.g., parameter types, return values, or full function signatures) as needed for deeper analysis or refactoring._
