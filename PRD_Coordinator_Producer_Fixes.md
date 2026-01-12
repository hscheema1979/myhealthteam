# PRD: Coordinator & Care Provider Dashboard Improvements

**Document Version:** 1.0
**Date:** 2026-01-08
**Status:** Draft

---

## Executive Summary

This PRD covers four functional requests for the Care Coordinator and Care Provider dashboards:
1. **Bug Fix:** Restore task editing capabilities for Care Providers in the Task Review tab
2. **Bug Fix:** Default workflow task minutes to 0 for coordinator workflow module
3. **Feature Addition:** Add "General Phone Inquiries" workflow for coordinators
4. **Future Feature:** Create a Workflow Editing Dashboard for Admin/Managers

---

## 1. Bug Fix: Restore CP Task Editing Capabilities

### 1.1 Problem Description
In a recent update (commit b8547b6), the Care Provider (CP) Task Review tab was simplified to show only basic columns (Patient Name, Date, Location of Visit). However, this change accidentally **removed the ability for Care Providers to edit/correct tasks** and save changes to the database.

### 1.2 Current State
- **File:** `src/dashboards/task_review_component.py`
- **Current Behavior:** All views (Daily, Weekly, Monthly) are read-only using `st.dataframe()`
- **Missing Columns:** Duration (Mins), Service Type, Notes
- **Missing Functionality:** No edit capability, no save button

### 1.3 Comparison with Coordinator Implementation
The Coordinator Task Review component (`src/dashboards/coordinator_task_review_component.py`) has full edit capabilities:
- Daily view uses `st.data_editor()` for inline editing
- Editable columns: Duration, Service Type, Notes
- Save button that updates the `coordinator_tasks_YYYY_MM` table
- Original data tracking for change detection

### 1.4 Requirements

#### Functional Requirements
1. **Restore Editable Columns in Daily View:**
   - Duration (Mins) - editable number input
   - Service Type - editable text field
   - Notes - editable text area
   - Task ID - hidden/disabled (used for database updates)

2. **Add Save Functionality:**
   - "Save Changes" button to persist edits to database
   - Update `provider_tasks_YYYY_MM` table with modified values
   - Show success/error messages after save
   - Clear session state and refresh data after successful save

3. **Maintain Read-Only Views for Weekly/Monthly:**
   - Weekly and Monthly views remain read-only (consistent with coordinator implementation)

#### Technical Requirements
- Use Streamlit's `st.data_editor()` component
- Store original data in `st.session_state` for change detection
- Update database using `provider_task_id` as the key
- Handle edge cases: null values, type conversion

### 1.5 Implementation Plan

#### Files to Modify
1. `src/dashboards/task_review_component.py` (primary changes)

#### Changes Required

**Query Enhancement (Daily View):**
```python
# Current query returns: provider_task_id, patient_name, task_date, task_description
# Need to also return: duration_minutes, task_type, notes
```

**Add Edit Capabilities (Daily View Only):**
```python
# Store original data before editing
original_key = f"original_provider_data_{user_id}_{display_period}"
if original_key not in st.session_state:
    st.session_state[original_key] = tasks_df.copy()

# Use data_editor instead of dataframe
edited_df = st.data_editor(
    tasks_df[['Patient Name', 'Date', 'Duration', 'Service Type', 'Notes']],
    use_container_width=True,
    hide_index=True,
    num_rows="fixed"
)

# Save button with database update logic
if st.button("Save Changes"):
    # Compare edited_df with original
    # Update database for changed rows
    # Clear session state and rerun
```

### 1.6 Database Impact
- **Tables Affected:** `provider_tasks_YYYY_MM` (monthly partitioned tables)
- **Update Columns:** `duration_minutes`, `task_type`, `notes`
- **No Schema Changes Required**

### 1.7 Testing Checklist
- [ ] Daily view shows editable columns
- [ ] Can edit Duration, Service Type, Notes
- [ ] Save button updates database correctly
- [ ] Success message displays after save
- [ ] Weekly/Monthly views remain read-only
- [ ] Cross-month date selection works
- [ ] Null values handled correctly

---

## 2. Bug Fix: Default Workflow Task Minutes to 0

### 2.1 Problem Description
When coordinators complete workflow steps in the workflow module, the duration input defaults to **30 minutes**. This is incorrect as workflow tasks should start at 0 minutes and only be filled when actual time is tracked.

### 2.2 Current State
- **File:** `src/dashboards/workflow_module.py`
- **Line 1170:** `value=duration_seconds // 60 if duration_seconds else 30`
- **Behavior:** Default is 30 minutes when no timer has been used

### 2.3 Requirements

#### Functional Requirements
1. Change default duration from 30 minutes to **0 minutes**
2. Only when the user hasn't used the timer
3. Preserve timer functionality (when Start/Stop is used, use that duration)

#### Technical Requirements
- Change the default value in `st.number_input()` from 30 to 0
- Ensure backward compatibility with existing workflows

### 2.4 Implementation Plan

#### Files to Modify
1. `src/dashboards/workflow_module.py`

#### Changes Required

**Line 1170 - Change Default Value:**
```python
# Before:
value=duration_seconds // 60 if duration_seconds else 30,

# After:
value=duration_seconds // 60 if duration_seconds else 0,
```

**Also Update References:**
- Line 1229: `duration_minutes=duration` - when reading from session state, ensure 0 is valid
- Line 1262: Same as above

### 2.5 Database Impact
- **Tables Affected:** `coordinator_tasks_YYYY_MM` (via `complete_workflow_step()` and `save_progress_step()`)
- **Column:** `duration_minutes` can be 0 (already allowed)
- **No Schema Changes Required**

### 2.6 Testing Checklist
- [ ] Default duration shows 0 when no timer used
- [ ] Timer functionality still works
- [ ] Can manually enter duration
- [ ] Save Progress works with 0 minutes
- [ ] Complete Step works with 0 minutes

---

## 3. Feature Addition: "General Phone Inquiries" Workflow

### 3.1 Problem Description
Coordinators need a workflow for handling general phone calls that don't fall under existing workflow categories. This workflow should be simple - allowing CCs to add progress notes if needed.

### 3.2 Requirements

#### Functional Requirements
1. **Workflow Name:** "General Phone Inquiries"
2. **Characteristics:**
   - Single-step workflow
   - CCs will just add progress notes if needed
   - Used for phone calls that don't fall under other existing workflows
3. **Owner:** Care Coordinator (CC)

#### Technical Requirements
1. Add workflow template to `workflow_templates` table
2. Add single step to `workflow_steps` table
3. Should appear in workflow dropdown for coordinators

### 3.3 Implementation Plan

#### Database Changes

**Option 1: SQL Script (Recommended for Production)**
Create SQL file: `src/sql/add_general_phone_inquiries_workflow.sql`

```sql
-- Insert workflow template
INSERT INTO workflow_templates (template_name)
VALUES ('General Phone Inquiries');

-- Insert the single step
INSERT INTO workflow_steps (template_id, step_order, task_name, owner, deliverable, cycle_time)
SELECT
    template_id,
    1 as step_order,
    'General Phone Inquiries' as task_name,
    'CC' as owner,
    'Progress notes added if needed' as deliverable,
    NULL as cycle_time
FROM workflow_templates
WHERE template_name = 'General Phone Inquiries';
```

**Option 2: Python Migration Script**
Create migration file: `src/migrations/add_general_phone_inquiries_workflow.py`

```python
def add_general_phone_inquiries_workflow():
    conn = get_db_connection()
    try:
        # Check if workflow already exists
        existing = conn.execute(
            "SELECT template_id FROM workflow_templates WHERE template_name = 'General Phone Inquiries'"
        ).fetchone()

        if existing:
            print("Workflow 'General Phone Inquiries' already exists")
            return

        # Insert template
        cursor = conn.execute(
            "INSERT INTO workflow_templates (template_name) VALUES ('General Phone Inquiries')"
        )
        template_id = cursor.lastrowid

        # Insert step
        conn.execute(
            """INSERT INTO workflow_steps (template_id, step_order, task_name, owner, deliverable, cycle_time)
            VALUES (?, 1, 'General Phone Inquiries', 'CC', 'Progress notes added if needed', NULL)""",
            (template_id,)
        )
        conn.commit()
        print("Added 'General Phone Inquiries' workflow")
    finally:
        conn.close()
```

### 3.4 Files to Create/Modify
1. **Create:** `src/sql/add_general_phone_inquiries_workflow.sql` (recommended)
2. **Verify:** No changes to `workflow_module.py` needed - it reads from database

### 3.5 Database Impact
- **Tables Affected:**
  - `workflow_templates` - 1 new row
  - `workflow_steps` - 1 new row
- **No Schema Changes Required**

### 3.6 Testing Checklist
- [ ] Workflow appears in dropdown
- [ ] Can start workflow for a patient
- [ ] Shows as single-step workflow
- [ ] Can add progress notes
- [ ] Can complete the step
- [ ] Workflow marks as completed after step completion

---

## 4. Future Feature: Workflow Editing Dashboard

### 4.1 Problem Description
Currently, workflows are managed through direct database inserts or SQL scripts. Admin and Managers need a UI dashboard to create, edit, and manage workflows without database access.

### 4.2 Scope
This is a **longer-term feature request** to be designed and implemented separately from the bug fixes above.

### 4.3 High-Level Requirements

#### Target Users
- Admin (role 50)
- Case Managers (role 40)
- Supervisors/Managers

#### Functional Requirements
1. **View All Workflows:** List all workflow templates with their steps
2. **Create New Workflow:**
   - Enter workflow name
   - Add multiple steps with:
     - Step order
     - Task name
     - Owner (CC, CM, Admin, etc.)
     - Deliverable description
     - Cycle time (optional)
3. **Edit Existing Workflow:**
   - Add/remove/reorder steps
   - Modify step details
   - Archive/delete workflows
4. **Preview Workflow:** See workflow structure before saving
5. **Activity Log:** Track who created/modified workflows

#### UI/UX Requirements
1. **Access:** Admin/Manager dashboard section
2. **Layout:** Two-column layout (workflow list on left, editor on right)
3. **Validation:** Prevent duplicate workflow names, missing required fields

### 4.4 Technical Considerations

#### Database Design
```sql
-- Potential new table for workflow audit log
CREATE TABLE workflow_changes (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER,
    changed_by_user_id INTEGER,
    change_type TEXT, -- 'CREATE', 'UPDATE', 'DELETE', 'ARCHIVE'
    change_details TEXT, -- JSON of what changed
    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES workflow_templates(template_id),
    FOREIGN KEY (changed_by_user_id) REFERENCES users(user_id)
);
```

#### Proposed File Structure
```
src/dashboards/
├── workflow_management_dashboard.py  # New file for the admin dashboard
src/utils/
├── workflow_management_utils.py      # Helper functions for CRUD operations
```

### 4.5 Implementation Phases (Future)

**Phase 1: Read-Only View**
- Display all workflows and their steps
- No editing capability

**Phase 2: Create Workflow**
- Form to create new workflows
- Add steps dynamically
- Save to database

**Phase 3: Edit Workflow**
- Edit existing workflow details
- Add/remove steps
- Reorder steps

**Phase 4: Advanced Features**
- Workflow versioning
- Audit log
- Archive/delete workflows
- Clone workflow template

### 4.6 Security Considerations
- Restrict access to Admin and Manager roles only
- Log all workflow changes with user attribution
- Validate all inputs before database writes
- Consider workflow "locking" to prevent concurrent edits

---

## Execution Plan

### Immediate Priority (This PRD)

| Task | File | Risk | Effort |
|------|------|------|--------|
| 1. Restore CP Task Editing | `task_review_component.py` | Low | Medium |
| 2. Default Workflow Minutes to 0 | `workflow_module.py` | Low | Low |
| 3. Add General Phone Inquiries | SQL script | Low | Low |

### Execution Order (Minimizing Risk)

1. **First:** Fix #2 (Default minutes to 0) - Single line change, isolated
2. **Second:** Fix #3 (General Phone Inquiries) - Simple INSERT, independent
3. **Third:** Fix #1 (CP Task Editing) - More complex, requires careful testing

### Testing Strategy

1. **Unit Testing:**
   - Verify database update logic
   - Test session state management

2. **Integration Testing:**
   - Test with real data in prototype database first
   - Verify all three views (Daily/Weekly/Monthly)

3. **User Acceptance Testing:**
   - Have CP user test the edit functionality
   - Have Coordinator test the 0-minute default
   - Have Coordinator test the new workflow

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing CP task review | Low | Medium | Test in prototype first, preserve read-only views |
| Database update errors | Low | Medium | Use transactions, validate before commit |
| Workflow template conflicts | Low | Low | Check for duplicates before insert |
| Session state issues | Medium | Low | Clear state appropriately on save |
| Cross-month table queries | Low | Low | Already handled by existing logic |

---

## Rollback Plan

If issues arise after deployment:

1. **Revert Code Changes:** Git revert to previous commit
2. **Database Rollback:**
   - For #3: Delete "General Phone Inquiries" from workflow_templates and workflow_steps
   - For #1/#2: No schema changes, simple code revert

---

## Appendix: Code Reference

### Key Files
- `src/dashboards/task_review_component.py` - CP task review (needs editing)
- `src/dashboards/coordinator_task_review_component.py` - Coordinator task review (reference)
- `src/dashboards/workflow_module.py` - Workflow management (needs default change)
- `src/dashboards/care_coordinator_dashboard_enhanced.py` - CC dashboard
- `src/dashboards/care_provider_dashboard_enhanced.py` - CP dashboard

### Database Tables
- `provider_tasks_YYYY_MM` - Monthly partitioned provider task tables
- `coordinator_tasks_YYYY_MM` - Monthly partitioned coordinator task tables
- `workflow_templates` - Workflow type definitions
- `workflow_steps` - Individual steps within workflow templates
- `workflow_instances` - Active workflow instances

---

**End of PRD**
