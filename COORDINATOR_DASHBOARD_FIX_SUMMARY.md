# Coordinator Dashboard Save Error - Fix Summary

**Date:** January 5, 2026
**Issue:** "Error saving changes - single positional indexer is out of bounds" in Coordinator Dashboard

---

## Root Cause Analysis

### TWO Separate Issues Identified:

#### Issue 1: Pandas Indexing Error ✅ FIXED
**NOT a permissions issue** - this was a technical bug in the code.

**Problem Location:** `src/dashboards/care_coordinator_dashboard_enhanced.py` - `_apply_patient_info_edits()` function

**Root Cause:**
The function had fragile error handling that could cause pandas indexing errors when:
- DataFrames had inconsistent `patient_id` formats (string vs int vs float)
- Empty DataFrames were not properly validated
- NaN values in patient_id columns caused comparison failures
- Dictionary lookups failed when patient_ids weren't properly normalized

**Error Message:** "single positional indexer is out of bounds" - This is a pandas exception indicating an attempt to access an array/DataFrame index that doesn't exist.

---

#### Issue 2: Coordinator Edit Permissions ℹ️ DOCUMENTED
**Your suspicion was CORRECT** - coordinators currently CANNOT edit patient information.

**Current Permission Structure:**

| Role ID | Role Name | Can Edit Patient Info? |
|----------|------------|------------------------|
| 34 | Admin | ✅ YES |
| 36 | Care Coordinator | ❌ NO |
| 37 | Lead Coordinator | ❌ NO |
| 40 | Coordinator Manager | ❌ NO |

**Code Reference:**
```python
def _has_admin_role(user_id):
    """Check if user has admin role (role_id 34) for edit permissions"""
    try:
        user_roles = database.get_user_roles_by_user_id(user_id)
        user_role_ids = [r["role_id"] for r in user_roles]
        return 34 in user_role_ids  # Only role_id 34 (Admin) can edit
    except Exception:
        return False
```

**Current User Experience:**
- Non-admin coordinators see: "🔒 **View-Only Mode**: Patient info editing is restricted to administrators"
- Only admins can toggle the "Enable editing" checkbox
- The error occurred because even admins encountered the pandas bug when trying to save

---

## Fixes Applied

### Fix 1: Robust Pandas Error Handling ✅
**File:** `src/dashboards/care_coordinator_dashboard_enhanced.py`
**Function:** `_apply_patient_info_edits()`

**Changes:**
1. ✅ Added comprehensive input validation (None checks, empty checks, column existence checks)
2. ✅ Proper handling of NaN values in patient_id columns
3. ✅ Consistent string normalization for all patient_id comparisons
4. ✅ Row-by-row error handling to prevent cascading failures
5. ✅ Added debug logging to track issues
6. ✅ Fixed parameter list issues (params were being reused incorrectly)

**Key Improvements:**
```python
# Before: Fragile comparison that could crash
if str(row.get(col)) != str(orig.get(col)):

# After: Robust NaN handling and comparison
if pd.isna(edited_val) and pd.isna(orig_val):
    continue
if str(edited_val) != str(orig_val):
    changed[col] = edited_val
```

---

## Recommendations

### Option 1: Grant Edit Access to Coordinators (If Needed)
If coordinators SHOULD be able to edit patient information, modify the permission check:

**File:** `src/dashboards/care_coordinator_dashboard_enhanced.py`
**Function:** `_has_admin_role()`

**Current Code:**
```python
def _has_admin_role(user_id):
    """Check if user has admin role (role_id 34) for edit permissions"""
    try:
        user_roles = database.get_user_roles_by_user_id(user_id)
        user_role_ids = [r["role_id"] for r in user_roles]
        return 34 in user_role_ids
    except Exception:
        return False
```

**Proposed Change - Add Coordinator Manager (40) and Lead Coordinator (37):**
```python
def _has_admin_role(user_id):
    """Check if user has edit permissions for patient info"""
    try:
        user_roles = database.get_user_roles_by_user_id(user_id)
        user_role_ids = [r["role_id"] for r in user_roles]
        # Allow Admin (34), Coordinator Manager (40), and Lead Coordinator (37) to edit
        return 34 in user_role_ids or 40 in user_role_ids or 37 in user_role_ids
    except Exception:
        return False
```

### Option 2: Keep Current Restrictions
If the current permission model is intentional (only admins can edit patient info), no changes are needed beyond the pandas fix. The error will no longer occur for admin users.

---

## Testing

### Test Scenario 1: Admin User Edit
1. Login as Admin (role_id 34)
2. Navigate to Coordinator Dashboard → Patient Info tab
3. Check "Enable editing" checkbox
4. Make changes to patient information
5. Save changes

**Expected Result:** ✅ Changes save successfully without "single positional indexer is out of bounds" error

### Test Scenario 2: Coordinator User View-Only
1. Login as Coordinator (role_id 36)
2. Navigate to Coordinator Dashboard → Patient Info tab
3. Observe the interface

**Expected Result:** ✅ View-only mode is clearly communicated with lock icon and message

---

## Summary

✅ **Immediate Issue Fixed:** The pandas indexing error is now resolved with robust error handling.

📋 **Permission Clarification:** Coordinators currently cannot edit patient info (by design). Only Admins have edit access.

🔧 **If coordinators need edit access:** Use the recommended code change above to add Coordinator Manager (40) and Lead Coordinator (37) roles to the edit permission list.

---

**Files Modified:**
- `src/dashboards/care_coordinator_dashboard_enhanced.py` - Fixed pandas indexing errors

**Files Created:**
- `COORDINATOR_DASHBOARD_FIX_SUMMARY.md` - This document
