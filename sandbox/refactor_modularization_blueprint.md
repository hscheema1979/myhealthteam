## 8. Consolidate Onboarding-to-Patient Sync Logic

**Current Problem:**
There are two functions (`insert_patient_from_onboarding` and `transfer_onboarding_to_patient_table`) that both sync onboarding data to the main patients table, with only minor differences (mainly whether onboarding is marked as completed).

**Recommendation:**

- Replace both with a single function, e.g. `sync_onboarding_to_patient(onboarding_id, mark_complete=False)`.
- This function should:
  - Insert or update the patient in the main table from onboarding data.
  - Always update the onboarding record’s `updated_date`.
  - If `mark_complete` is `True`, also set the `completed_date`.
- Remove the redundant functions.

**Example:**

```python
def sync_onboarding_to_patient(onboarding_id, mark_complete=False):
		# ...existing logic to insert/update patient...
		# Always update onboarding's updated_date
		conn.execute("UPDATE onboarding_patients SET updated_date = CURRENT_TIMESTAMP WHERE onboarding_id = ?", (onboarding_id,))
		if mark_complete:
				conn.execute("UPDATE onboarding_patients SET completed_date = CURRENT_TIMESTAMP WHERE onboarding_id = ?", (onboarding_id,))
		# ...commit, return, etc...
```

**Benefits:**

- No code duplication
- Centralized onboarding-to-patient logic
- Easy to maintain and extend

---

# Refactoring & Modularization Blueprint

This document outlines a systematic approach to refactoring the codebase for maintainability, modularity, and ease of debugging. It identifies consolidation opportunities, proposes new utility modules, and recommends best practices for table and code design.

---

## 1. Guiding Principles

- **No hardcoded values:** All IDs, table names, and config values should be constants or loaded from config files.
- **Single source of truth:** Each type of logic (user, patient, task, onboarding) should have a single utility module.
- **Composable functions:** Utility functions should be parameterized and reusable across dashboards.
- **Simple, normalized tables:** Database tables should avoid redundancy and use clear, consistent naming.

---

## 2. Proposed Utility Modules

| Module                | Purpose/Responsibility                                | Example Functions                                                                       |
| --------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `config.py`           | Central config, DB path, role IDs, table names        | `get_db_path()`, `ROLE_CARE_COORDINATOR`                                                |
| `user_utils.py`       | User and role management                              | `get_users()`, `get_roles()`, `get_user_roles()`                                        |
| `panel_utils.py`      | Patient panel and assignment logic                    | `get_user_panel(user_id, role_id=None)`                                                 |
| `task_utils.py`       | Task management for coordinators/providers            | `get_task_table_name(role, year, month)`, `get_task_summary(role, user_id, date_range)` |
| `onboarding_utils.py` | Onboarding workflow and patient onboarding management | `create_onboarding_patient()`, `advance_onboarding_stage()`                             |
| `dashboard_utils.py`  | Common dashboard helpers (tabs, role checks, etc.)    | `create_tabs(tab_names)`, `require_role(role_id)`                                       |
| `constants.py`        | All role IDs, table names, and other constants        | `ROLE_CARE_PROVIDER`, `TABLE_PATIENTS`                                                  |

---

## 3. Eliminate Hardcoded Values

- Move all role IDs (e.g., 36, 37, 38, 40) to `constants.py`.
- Move all table names to `constants.py` or generate dynamically in utility functions.
- Store DB path and other config in `config.py` or `.env`.

---

## 4. Example: Refactored Function Calls

**Before:**

```python
coordinators = database.get_users_by_role(36)
```

**After:**

```python
from constants import ROLE_CARE_COORDINATOR
from user_utils import get_users_by_role
coordinators = get_users_by_role(ROLE_CARE_COORDINATOR)
```

**Before:**

```python
table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
```

**After:**

```python
from task_utils import get_task_table_name
table_name = get_task_table_name('coordinator', year, month)
```

---

## 5. Table Design Recommendations

- Use normalized tables (no redundant columns).
- Use foreign keys for relationships (user_id, patient_id, etc.).
- Use clear, consistent naming (e.g., `user_patient_assignments`, `provider_tasks_YYYY_MM`).
- Partition large tables by month only if necessary for performance.

---

## 6. Implementation Checklist

- [ ] Create `config.py` and `.env` for all environment/config values.
- [ ] Create `constants.py` for all IDs and table names.
- [ ] Refactor user/role logic into `user_utils.py`.
- [ ] Refactor patient panel logic into `panel_utils.py`.
- [ ] Refactor task logic into `task_utils.py`.
- [ ] Refactor onboarding logic into `onboarding_utils.py`.
- [ ] Refactor dashboard helpers into `dashboard_utils.py`.
- [ ] Update all dashboard scripts to use new utility modules.
- [ ] Remove all hardcoded values from codebase.

---

## 7. Benefits

- **Maintainability:** One place to update logic or IDs.
- **Debuggability:** Fewer unique code paths, easier to trace bugs.
- **Reusability:** Utility functions can be used across dashboards and scripts.
- **Scalability:** Adding new roles, panels, or task types is straightforward.

---

_This blueprint is intended as a living document to guide future refactoring and ensure a robust, maintainable codebase._
