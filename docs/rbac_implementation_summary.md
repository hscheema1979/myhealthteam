# RBAC Implementation Summary - Workflow Analytics & Unassigned Tab

## Overview

The "Workflow Analytics & Unassigned" tab has been successfully integrated across **multiple dashboards** using **Role-Based Access Control (RBAC)** to simplify the dashboard architecture while providing appropriate feature access based on user roles.

## Dashboard Strategy: Shared Dashboards with RBAC

Rather than creating separate dashboards for each role, the system uses **shared dashboards** where features are shown/hidden based on the user's roles. This approach:

- ✅ **Reduces Maintenance**: One codebase for multiple roles
- ✅ **Consistent UX**: All users see the same basic interface
- ✅ **Easier Updates**: Changes propagate to all roles automatically
- ✅ **Security**: Role checks prevent unauthorized access

## Role IDs and Permissions

| Role ID | Role Name | Dashboard | Access Level |
|---------|-----------|-----------|--------------|
| 34 | Admin | Admin Dashboard | Full access to all tabs including Workflow Analytics |
| 40 | Coordinator Manager (CM) | Care Coordinator Dashboard | Enhanced access with management tabs including Analytics |
| 38 | Care Provider Manager (CPM) | Care Provider Dashboard | Enhanced access with management tabs including Analytics |
| 37 | Lead Coordinator | Care Coordinator Dashboard | Enhanced access with management tabs including Analytics |
| 36 | Care Coordinator | Care Coordinator Dashboard | Basic access (no management tabs) |
| 33 | Care Provider | Care Provider Dashboard | Basic access (no management tabs) |

## Dashboard Implementation Details

### 1. Admin Dashboard

**File**: `src/dashboards/admin_dashboard.py`

**Access Criteria**:
- Users with **Admin role (34)** OR **Coordinator Manager role (40)**
- Both roles see the full admin dashboard with all tabs

**Tabs Available**:
1. User Role Management
2. Staff Onboarding
3. Coordinator Tasks
4. Provider Tasks
5. Patient Info
6. HHC View Template
7. Workflow Reassignment
8. ZMO
9. **Workflow Analytics & Unassigned** ← NEW
10. Billing Report (Justin/Harpreet only)

**Code Location**:
```python
# Lines 436-453: Tab names list
tab_names = [
    "User Role Management",
    "Staff Onboarding",
    "Coordinator Tasks",
    "Provider Tasks",
    "Patient Info",
    "HHC View Template",
    "Workflow Reassignment",
    "ZMO",
    "Workflow Analytics & Unassigned",  # NEW
]

# Lines 459-469: Tab variable assignment
tab_analytics_unassigned = tabs[8] if len(tab_names) > 8 else st.empty()

# Lines 3095-3108: Tab handler
with tab_analytics_unassigned:
    from src.dashboards.workflow_analytics_unassigned_module import show_workflow_analytics_unassigned_tab
    show_workflow_analytics_unassigned_tab(user_id=user_id, user_role_ids=user_role_ids)
```

---

### 2. Care Coordinator Dashboard

**File**: `src/dashboards/care_coordinator_dashboard_enhanced.py`

**Access Strategy**: RBAC-based conditional tabs

#### Management Role Users (Lead Coordinator or Coordinator Manager)

**Access Criteria**:
- Users with **Lead Coordinator role (37)** OR **Coordinator Manager role (40)**
- Both roles see enhanced tabs including Workflow Analytics

**Tabs Available**:
1. My Patients
2. Phone Reviews
3. Team Management
4. Workflow Reassignment
5. ZMO (Patient Data)
6. **Analytics & Unassigned** ← NEW
7. Help

**Code Location**:
```python
# Lines 169-195: Role check and tab creation
has_lc_role = 37 in user_role_ids
has_cm_role = 40 in user_role_ids
has_management_role = has_lc_role or has_cm_role

if has_management_role:
    tab1, tab2, tab3, tab_workflow, tab_zmo, tab_analytics, tab4 = st.tabs([
        "My Patients",
        "Phone Reviews",
        "Team Management",
        "Workflow Reassignment",
        "ZMO (Patient Data)",
        "Analytics & Unassigned",  # NEW
        "Help",
    ])

# Lines 343-357: Tab handler
with tab_analytics:
    from src.dashboards.workflow_analytics_unassigned_module import show_workflow_analytics_unassigned_tab
    show_workflow_analytics_unassigned_tab(user_id=user_id, user_role_ids=user_role_ids)
```

#### Regular Care Coordinators (No Management Role)

**Access Criteria**:
- Users with **Care Coordinator role (36)** but NOT Lead Coordinator or Coordinator Manager
- See basic coordinator tabs without management features

**Tabs Available**:
1. My Patients
2. Task Review
3. ZMO (Patient Data)
4. Help

**Note**: Regular coordinators do NOT see the Analytics & Unassigned tab.

---

### 3. Care Provider Dashboard

**File**: `src/dashboards/care_provider_dashboard_enhanced.py`

**Access Strategy**: RBAC-based conditional tabs

#### Care Provider Managers (CPM)

**Access Criteria**:
- Users with **Care Provider Manager role (38)**
- See enhanced tabs including Workflow Analytics

**Tabs Available** (with onboarding queue):
1. My Patients
2. Team Management
3. Onboarding Queue & Initial TV Visits
4. Phone Reviews
5. Task Review
6. **Analytics & Unassigned** ← NEW
7. ZMO (Patient Data)
8. Help

**Tabs Available** (without onboarding queue):
1. My Patients
2. Team Management
3. Phone Reviews
4. Task Review
5. **Analytics & Unassigned** ← NEW
6. ZMO (Patient Data)
7. Help

**Code Location**:
```python
# Lines 1850-1851: Role check
has_cpm_role = 38 in user_role_ids

# Lines 1862-1872: Tab creation with queue (UPDATED)
if onboarding_queue and len(onboarding_queue) > 0:
    tab1, tab2, tab3, tab4, tab5, tab_analytics, tab_zmo, tab_help = st.tabs([
        "My Patients",
        "Team Management",
        "Onboarding Queue & Initial TV Visits",
        "Phone Reviews",
        "Task Review",
        "Analytics & Unassigned",  # NEW
        "ZMO (Patient Data)",
        "Help",
    ])

# Lines 1900-1908: Tab creation without queue (UPDATED)
else:
    tab1, tab2, tab3, tab4, tab_analytics, tab_zmo, tab_help = st.tabs([
        "My Patients",
        "Team Management",
        "Phone Reviews",
        "Task Review",
        "Analytics & Unassigned",  # NEW
        "ZMO (Patient Data)",
        "Help",
    ])

# Lines 1895-1908: Tab handler with queue (UPDATED)
with tab_analytics:
    from src.dashboards.workflow_analytics_unassigned_module import show_workflow_analytics_unassigned_tab
    show_workflow_analytics_unassigned_tab(user_id=user_id, user_role_ids=user_role_ids)

# Lines 1925-1937: Tab handler without queue (UPDATED)
with tab_analytics:
    from src.dashboards.workflow_analytics_unassigned_module import show_workflow_analytics_unassigned_tab
    show_workflow_analytics_unassigned_tab(user_id=user_id, user_role_ids=user_role_ids)
```

#### Regular Care Providers (Non-CPM)

**Access Criteria**:
- Users with **Care Provider role (33)** but NOT Care Provider Manager
- See basic provider tabs without management features

**Tabs Available**:
1. My Patients
2. Onboarding Queue (if applicable)
3. Phone Reviews
4. Task Review
5. ZMO (Patient Data)
6. Help

**Note**: Regular providers do NOT see the Analytics & Unassigned tab.

---

### 4. Coordinator Manager Dashboard (Standalone - Optional)

**File**: `src/dashboards/coordinator_manager_dashboard.py` (NEW)

**Access Criteria**:
- Users with **Coordinator Manager role (40)**
- Dedicated dashboard for coordinator management functions

**Tabs Available**:
1. Coordinator Tasks
2. Patient Reassignment
3. Workflow Assignment
4. ZMO (Patient Data)
5. **Analytics & Unassigned** ← NEW

**Purpose**:
- Provides a focused interface for Coordinator Managers
- Can be used as an alternative to the shared Care Coordinator Dashboard
- Contains the same Analytics & Unassigned functionality

**Note**: This dashboard is **optional** - Coordinator Managers can use either:
1. The **Care Coordinator Dashboard** (shared with Lead Coordinators)
2. The standalone **Coordinator Manager Dashboard** (dedicated)

Both provide the same Analytics & Unassigned functionality.

---

## Role Verification Logic

### Admin Dashboard
```python
# Lines 421-433 in admin_dashboard.py
try:
    user_roles = database.get_user_roles_by_user_id(user_id)
    user_role_ids = [r["role_id"] for r in user_roles]
    has_admin_roles = any(
        role_id in [34, 40]  # Admin or Coordinator Manager
        for role_id in user_role_ids
    )
except Exception:
    has_admin_roles = False
```

### Care Coordinator Dashboard
```python
# Lines 169-177 in care_coordinator_dashboard_enhanced.py
has_lc_role = 37 in user_role_ids  # Lead Coordinator
has_cm_role = 40 in user_role_ids  # Coordinator Manager
has_management_role = has_lc_role or has_cm_role
```

### Care Provider Dashboard
```python
# Lines 1850-1851 in care_provider_dashboard_enhanced.py
has_cpm_role = 38 in user_role_ids  # Care Provider Manager
```

---

## Feature Access Matrix

| Feature | Admin | CM | CPM | Lead Coord | Coord | Provider |
|---------|-------|----|----|-----------|-------|----------|
| Workflow Analytics (Step Metrics) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Delay/Late Tracking | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Stagnation Alerts | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Andrew's View (Unassigned Coordinators) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Jan's View (Unassigned Providers) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Patient Assignment | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

---

## Security Considerations

### 1. Authentication
- All dashboards require user authentication via `app.py`
- User session validated on each page load
- `user_id` and `user_role_ids` from secure session state

### 2. Authorization
- Role checks prevent unauthorized tab access
- Backend database queries respect role boundaries
- Admin-only features protected by multiple role checks

### 3. Data Isolation
- Coordinators see only their assigned patients (unless management role)
- Providers see only their assigned patients (unless CPM role)
- Management roles can see team-wide data

### 4. Audit Trail
- All patient assignments logged to `audit_log` table
- Workflow changes tracked with user_id and timestamp
- Patient data changes logged with old/new values

---

## Testing Checklist

### Admin Dashboard
- [ ] Login as Admin (role 34) → Verify tab appears
- [ ] Login as Coordinator Manager (role 40) → Verify tab appears
- [ ] Login as regular user → Verify tab does NOT appear
- [ ] Test Workflow Analytics sub-tab features
- [ ] Test Unassigned Patients sub-tab features
- [ ] Verify Andrew's View and Jan's View work correctly

### Care Coordinator Dashboard
- [ ] Login as Lead Coordinator (role 37) → Verify tab appears
- [ ] Login as Coordinator Manager (role 40) → Verify tab appears
- [ ] Login as regular Care Coordinator (role 36) → Verify tab does NOT appear
- [ ] Test all features work correctly
- [ ] Verify data isolation (coordinators see appropriate data)

### Care Provider Dashboard
- [ ] Login as Care Provider Manager (role 38) → Verify tab appears
- [ ] Login as regular Care Provider (role 33) → Verify tab does NOT appear
- [ ] Test with onboarding queue present
- [ ] Test without onboarding queue
- [ ] Verify all features work correctly

### Coordinator Manager Dashboard (Optional)
- [ ] Login as Coordinator Manager (role 40)
- [ ] Verify dedicated dashboard loads
- [ ] Verify all tabs including Analytics & Unassigned
- [ ] Test all features work correctly

---

## Deployment Checklist

### Pre-Deployment
- [ ] All code changes committed to Git
- [ ] Feature branch created and tested
- [ ] Code review completed
- [ ] Documentation updated

### Deployment Steps
1. **Backup Database**
   ```bash
   cp production.db production.db.backup_$(date +%Y%m%d)
   ```

2. **Deploy Code to VPS2**
   ```bash
   ssh server2 "cd /opt/myhealthteam && git pull origin main"
   ```

3. **Apply Schema Changes (if any)**
   - No schema changes required for this feature
   - Uses existing tables only

4. **Restart Service**
   ```bash
   ssh server2 "sudo systemctl restart myhealthteam"
   ```

5. **Verify Deployment**
   ```bash
   ssh server2 "sudo systemctl status myhealthteam"
   ```

6. **Smoke Testing**
   - Login as each role type
   - Verify tab appears/disappears correctly
   - Test basic functionality

### Post-Deployment
- [ ] Monitor error logs for issues
- [ ] Gather user feedback
- [ ] Document any issues found
- [ ] Plan next iteration if needed

---

## Troubleshooting

### Issue: Tab not appearing for authorized role

**Possible Causes**:
1. Role ID incorrect in database
2. User session not refreshed
3. Code not deployed correctly

**Solutions**:
```sql
-- Check user's roles
SELECT user_id, full_name, role_id
FROM user_roles ur
JOIN users u ON ur.user_id = u.user_id
WHERE u.user_id = <user_id>;
```

```python
# Clear session and re-login
st.session_state.clear()
```

### Issue: Permission denied errors

**Possible Causes**:
1. Database permissions not set
2. File permissions incorrect

**Solutions**:
```bash
# Check file permissions
ls -la src/dashboards/workflow_analytics_unassigned_module.py

# Fix permissions if needed
chmod 644 src/dashboards/workflow_analytics_unassigned_module.py
```

### Issue: Data not showing

**Possible Causes**:
1. No active workflows in system
2. No unassigned patients
3. Database connection issue

**Solutions**:
```sql
-- Check for active workflows
SELECT COUNT(*) FROM workflow_instances WHERE workflow_status = 'Active';

-- Check for unassigned patients
SELECT COUNT(*) FROM patients
WHERE status = 'Active'
  AND (coordinator_id IS NULL OR provider_id IS NULL);
```

---

## Files Modified/Created

### Modified Files
1. `src/dashboards/admin_dashboard.py`
   - Added "Workflow Analytics & Unassigned" to tab_names (line 444)
   - Added tab_analytics_unassigned variable assignment (line 468)
   - Added tab handler (lines 3095-3108)

2. `src/dashboards/care_coordinator_dashboard_enhanced.py`
   - Added tab_analytics to tabs (line 186)
   - Added tab handler (lines 343-357)

3. `src/dashboards/care_provider_dashboard_enhanced.py`
   - Added tab_analytics to CPM tabs with queue (line 1862)
   - Added tab_analytics to CPM tabs without queue (line 1900)
   - Added tab handlers (lines 1895-1908, 1925-1937)

### Created Files
1. `src/dashboards/workflow_analytics_unassigned_module.py` (NEW)
   - Main module containing all functionality
   - ~680 lines of code
   - Includes database query functions and UI components

2. `src/dashboards/coordinator_manager_dashboard.py` (NEW - Optional)
   - Standalone Coordinator Manager Dashboard
   - ~490 lines of code
   - Alternative to shared Care Coordinator Dashboard

3. `docs/workflow_analytics_unassigned_guide.md` (NEW)
   - Comprehensive user guide
   - ~400 lines
   - Usage instructions and best practices

4. `docs/rbac_implementation_summary.md` (NEW)
   - This document
   - RBAC implementation details
   - Deployment and testing checklists

---

## Summary

The "Workflow Analytics & Unassigned" feature has been successfully integrated using RBAC across multiple dashboards:

✅ **Admin Dashboard** - Admin and Coordinator Manager roles
✅ **Care Coordinator Dashboard** - Lead Coordinator and Coordinator Manager roles
✅ **Care Provider Dashboard** - Care Provider Manager role
✅ **Coordinator Manager Dashboard** (Optional) - Dedicated dashboard for CMs

All role checks are implemented at the dashboard level, ensuring appropriate access control while maintaining a simplified, maintainable codebase.

---

**Document Version**: 1.0
**Last Updated**: March 5, 2026
**Author**: AI Agent (Claude)
