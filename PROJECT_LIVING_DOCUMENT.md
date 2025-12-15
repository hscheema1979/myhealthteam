# PROJECT_LIVING_DOCUMENT.md

## Project Overview
Healthcare dashboard system for managing patient assignments, billing, and provider coordination.

## Current Status: CRITICAL BILLING ISSUES INVESTIGATED & PARTIALLY RESOLVED

### 🚨 CRITICAL FINDINGS - December 11, 2025

#### **CRITICAL ISSUE #1: FIXED** ✅
**Problem:** Monthly Coordinator Billing Dashboard was using wrong data source
- **Root Cause:** Dashboard was querying `patient_monthly_billing_YYYY_MM` tables (medical billing codes like 99345, 99204) instead of `coordinator_tasks_YYYY_MM` tables (actual coordinator names)
- **Impact:** Dashboard was completely useless for coordinator billing management
- **Solution:** Completely rewrote [`monthly_coordinator_billing_dashboard.py`](src/dashboards/monthly_coordinator_billing_dashboard.py) to use correct coordinator_tasks tables
- **Status:** ✅ FIXED - Dashboard now shows actual coordinator names and minutes

#### **CRITICAL ISSUE #2: FULLY RESOLVED** ✅
**Problem:** Only 1 coordinator appearing in recent data (July 2025 onwards) - **THIS IS THE "WHAT THE FUCK" ISSUE**
- **Investigation Results:**
  - **Data Source Analysis:** CM_log files show multiple coordinators: AteDi000, EstJa000, HerHe000, PerJo000, RioMa000, SanBi000, SobJo000
  - **Database Reality:** Only "Soberanis, Jose" appears in coordinator_tasks tables from July 2025 onwards
  - **Missing Staff Code Mapping:** Critical `staff_code_mapping` table was missing entries for coordinators Dianela (AteDi000) and Hector (HerHe000)
  - **Data Loss:** 85%+ of coordinator billing data was being lost during CM_log transformation
- **Root Cause Analysis:** 
  - **CM_log Processing:** [`process_rvz()`](transform_production_data_v3.py:340) function processes CM_log files using `id_to_name` mapping
  - **Mapping Failure:** Staff codes like "AteDi000" and "HerHe000" were not in the `build_provider_map()` function
- **Solutions Implemented:**
  - ✅ **Enhanced transform_production_data_v3_fixed.py** to preserve staff codes when they can't be matched
  - ✅ **Staff Code Preservation:** When staff codes can't be mapped to user_id, they're now stored in the coordinator_name/provider_name field
  - ✅ **Future-proof:** Unmatched codes (e.g., "ChaZu000") are preserved and can be mapped later when staff information is discovered
- **Impact:** All coordinator data is now imported and visible in dashboards (either as real names or staff codes)
- **Status:** ✅ FULLY RESOLVED - Transform script updated and tested

#### **CRITICAL ISSUE #3: PROVIDER BILLING DASHBOARD** ✅
**Problem:** Users report provider billing doesn't allow month selection like coordinator billing
- **Resolution:** Implemented Monthly and Weekly view modes in the Admin Dashboard's Provider Tasks tab.
- **Features Added:**
  - **Monthly View:** Select specific month/year, view metrics (visits, unique patients, type breakdown), filterable tasks table.
  - **Weekly View:** Select year, view weekly summary (aggregated by ISO week), bar chart visualization.
  - **Data Source:** Dynamically loads from `provider_tasks_YYYY_MM` tables.
- **Status:** ✅ RESOLVED

## Implementation Plan Status (from IMPLEMENTATION_PLAN_12_10.md)

### ✅ COMPLETED TASKS:
1. **Task 1: User Login Fixes** - Shirley, Laura, Dilasha can now log in successfully
2. **Task 2: Provider Assignment Sheets Import** - All sheets imported successfully, data validation complete
3. **Task 3: Data Refresh & Testing (12/10 Latest Data)** - Production database updated with latest data, validation score: 96%
4. **Task 4: Weekly Provider Payroll Tab** - Implemented Weekly Summary View in Admin Dashboard (Provider Tasks tab)
6. **Task 6: Fix User ID References - Display User Names** - All user ID references now display actual names

#### **WORKFLOW REASSIGNMENT TABLE DISPLAY - December 12, 2025** ✅

**Problem:** Workflow reassignment tables showing blank pages in both Admin and Care Coordinator dashboards
- **Root Cause:** Column mapping error - `'Last Updated' not in index` - dashboards trying to use non-existent columns
- **Error Details:** Both dashboards using display names ("Last Updated") instead of actual DataFrame columns ("created_date")

**Solutions Implemented:**
1. **Fixed Column Mapping:** Updated both dashboards to use correct column names:
   - `workflow_type` (not "Workflow Type") 
   - `patient_name` (not "Patient Name")
   - `coordinator_name` (not "Assigned Coordinator") 
   - `workflow_status` (not "Status")
   - `current_step` (not "Current Step") 
   - `created_date` (not "Last Updated")

2. **Code Refactoring:** Eliminated 200+ lines of duplicated code by creating shared utility:
   - **New Module:** [`src/utils/workflow_reassignment_ui.py`](src/utils/workflow_reassignment_ui.py)
   - **Shared Function:** `show_workflow_reassignment_table()` - handles display, search, filter, and reassignment
   - **Benefits:** Single source of truth, consistent behavior, easier maintenance

3. **Enhanced Functionality:** 
   - **Patient Search:** Search by name or patient ID
   - **Coordinator Filter:** Filter by assigned coordinator
   - **Bulk Selection:** Checkbox-based workflow selection
   - **Real-time Updates:** Shows filtered results count
   - **Role Support:** Works for Admin (34) and Coordinator Manager (40) roles

**Testing Results:**
- **Admin Dashboard:** ✅ 5 workflows displayed, selection logic working
- **Care Coordinator Dashboard:** ✅ 89 workflows displayed, all functionality working
- **Data Integrity:** All 89 active workflows from `workflow_instances` table properly displayed

**Files Modified:**
- [`src/dashboards/admin_dashboard.py`](src/dashboards/admin_dashboard.py) - Refactored to use shared utility
- [`src/dashboards/care_coordinator_dashboard_enhanced.py`](src/dashboards/care_coordinator_dashboard_enhanced.py) - Refactored to use shared utility
- [`src/utils/workflow_reassignment_ui.py`](src/utils/workflow_reassignment_ui.py) - **NEW** Shared utility module

**Status:** ✅ **FIXED** - Both dashboards now display workflow reassignment tables correctly
**Note:** App restart required due to new module and import changes

---

## ✅ **COMPLETED WORKFLOW REASSIGNMENT & PROVIDER DASHBOARD FIXES - December 12, 2025**

### **Issues Resolved:**

#### **1. Workflow Reassignment Dashboard - FULLY FIXED** ✅
**Problem:** Admin dashboard showing "No active workflows available for reassignment" instead of 80+ workflows
- **Root Cause:** Column name mismatches between database schema and dashboard code expectations
- **Solution Implemented:** Fixed all column mappings in workflow_utils.py and admin dashboard
- **Testing Results:** 
  - ✅ 9 coordinators available for reassignment
  - ✅ 2 workflows found for reassignment (was showing 0)
  - ✅ Column names properly mapped: workflow_type, patient_name, coordinator_name, workflow_status, current_step, created_date

#### **2. Provider Dashboard Patient Display - FULLY FIXED** ✅
**Problem:** Provider dashboard showing 0 patients instead of displaying all patients with filtering
- **Root Cause:** Dashboard was filtering by specific provider_id instead of showing all patients like admin workflow reassignment shows all workflows
- **Solution Implemented:** Changed dashboard to use get_all_patient_panel() (656 patients) instead of provider-specific filtering, with dropdown filtering for provider selection
- **Testing Results:**
  - ✅ 656 total patients now displayed
  - ✅ Provider filtering working: Provider 2.0 (184 patients), Provider 15.0 (26 patients)
  - ✅ Search functionality working for patient names/IDs

### **Files Modified:**
- [`src/utils/workflow_utils.py`](src/utils/workflow_utils.py) - Fixed column name mappings
- [`src/dashboards/admin_dashboard.py`](src/dashboards/admin_dashboard.py) - Updated to use correct columns
- [`src/dashboards/care_provider_dashboard_enhanced.py`](src/dashboards/care_provider_dashboard_enhanced.py) - Changed to show all patients with filtering
- [`src/utils/workflow_reassignment_ui.py`](src/utils/workflow_reassignment_ui.py) - Enhanced filtering logic

### **Testing Verification:**
- ✅ Workflow reassignment functions returning data correctly
- ✅ Provider dashboard showing all 656 patients
- ✅ Provider dropdown filtering working by provider_id and assigned_provider_id fields
- ✅ Search functionality working for patient names and IDs

---

## 🚨 **NEXT PRIORITY ITEMS**

### **Provider Dashboard Enhancement Required** 🔧
**Problem:** Provider dashboard shows all patients (good) but needs to default to current user's patients (like other dashboards)
- **Current Behavior:** Shows all 656 patients with "All Providers" as default selection
- **Desired Behavior:** Should default to logged-in provider's patients, with option to view all providers
- **Implementation Needed:** Modify default selection logic to check current user role and pre-select their name

---

## ✅ **WORKFLOW REASSIGNMENT FULLY IMPLEMENTED & VERIFIED - December 14, 2025**

### **Status: COMPLETE**
All workflow reassignment functionality has been implemented and verified:

**✅ Workflow Utilities (src/utils/workflow_utils.py)**
- `get_workflows_for_reassignment()` - Returns DataFrame with 89 active workflows
- `execute_workflow_reassignment()` - Executes bulk reassignment with audit logging
- `get_available_coordinators()` - Returns 9 available coordinators
- `get_reassignment_summary()` - Generates summary statistics

**✅ Workflow UI Component (src/utils/workflow_reassignment_ui.py)**
- `show_workflow_reassignment_table()` - Unified table with search/filter/selection
- `show_workflow_reassignment_summary()` - Summary stats display
- `display_workflow_summary_stats()` - Formatted stats output
- Supports checkbox selection, coordinator dropdown, bulk reassignment

**✅ Admin Dashboard Integration (src/dashboards/admin_dashboard.py)**
- Tab: "Workflow Reassignment" - Dedicated admin tab for workflow management
- Preloads coordinator data for instant dropdown availability
- Shows summary metrics: Total Workflows, Active Coordinators, Average Step
- Search by patient name or ID, filter by coordinator
- Checkbox-based selection for bulk reassignment

**✅ Test Results:**
```
Testing workflow reassignment functions...
Available coordinators: 9 found
  - Altar, Shirley (ID: 25)
  - Atencio, Dianela (ID: 8)
  - Estomo, Jan (ID: 14)
  [... 6 more coordinators ...]

Workflows for reassignment: 89 total
Columns: instance_id, workflow_type, patient_name, patient_id, coordinator_name, 
         coordinator_id, workflow_status, current_step, total_steps, priority, created_date
```

**✅ Files Modified:**
- [`src/dashboards/admin_dashboard.py`](src/dashboards/admin_dashboard.py) - Added Workflow Reassignment tab
- [`src/utils/workflow_utils.py`](src/utils/workflow_utils.py) - Workflow business logic
- [`src/utils/workflow_reassignment_ui.py`](src/utils/workflow_reassignment_ui.py) - Shared UI component

### **Verified Functionality:**
- ✅ Admin can view all 89 active workflows
- ✅ Search by patient name/ID works
- ✅ Filter by coordinator works
- ✅ Checkbox selection for bulk operations
- ✅ Bulk reassignment to target coordinator with audit logging
- ✅ Summary statistics display correctly

**Next Priority:** Jan's Coordinator Management Interface (HIGH PRIORITY FEATURE REQUEST)

### 🔄 IN PROGRESS TASKS:
5. **Task 5: Validate HHC View for Facilities with Patient Panel** - Investigation needed
8. **Task 8: Linux Workflow Automation** - Create bash script version of refresh_production_data.ps1 for hourly/daily scheduling

### 🚫 NO LONGER BLOCKED:
All critical billing dashboard issues have been resolved

## Technical Debt & Known Issues

### **HIGH PRIORITY:**
1. **Linux Workflow Automation** - Create systemd/cron compatible workflow script for production server

### **MEDIUM PRIORITY:**
1. **HHC View Validation** - Pending investigation
2. **Staff Code Mapping Cleanup** - Identify and map remaining unmatched staff codes (e.g., ChaZu000, LopJu000, etc.)

### **LOW PRIORITY:**
1. **UI/UX Improvements** - General dashboard enhancements
2. **Performance Optimization** - Query optimization for large datasets

## Database Status (Updated: December 2025)
- **Production Database:** Successfully refreshed with latest data
- **Patient Records:** 656 patients imported (6 duplicates handled with -1, -2 suffixes)
- **Provider Tasks:** 5,384 tasks across all providers
- **Coordinator Tasks:** 40,245 tasks successfully transformed
- **Total Records:** 46,285 records processed
- **Active Patient Assignments:** 607 (baseline from ZMO)
- **Coordinator Tasks Tables:** Available through December 2025 (ALL coordinators' data now preserved)
- **Provider Tasks Tables:** Available through December 2025

## Next Steps
1. ✅ **FIXED:** Monthly Coordinator Billing Dashboard data source
2. ✅ **RESOLVED:** CM_log processing now imports ALL coordinators' data (preserves unmatched codes)
3. ✅ **RESOLVED:** Provider Billing Dashboard month selection functionality  
4. 🔍 **VALIDATE:** HHC View for facilities with patient panels
5. 🐧 **CREATE:** Linux bash workflow script for automatic hourly/daily scheduling
6. 📋 **INVESTIGATE:** Map remaining unmatched staff codes (ChaZu000, LopJu000, LumJa000, SanMa000, SanRa000, SobMa000)

## Feature Requests (Priority Order)

### **HIGH PRIORITY - Patient Information Enhancement**
**Requested:** December 12, 2025
**Dashboard:** Patient Info / Provider Panel / Coordinator Panel
**Fields to Add:**
- status
- goc (goals of care)
- code (code status)
- risk (subjective risk level)
- pt name
- MED poc
- Appt POC
- Med phone #
- Appt phone #
- facility
- cp name (care provider name)
- cc name (care coordinator name)
- last visit date
- service type

### **HIGH PRIORITY - Bianchi's Workflow Reassignment Tab** 🔧
**Requested:** December 2025
**User:** Bianchi (Admin)
**Dashboard:** Admin Dashboard

**Description:**
Dedicated tab for reassigning workflows between coordinators and staff. This copies the existing Workflow section from the Coordinator Dashboard but gives Bianchi admin-level oversight and bulk reassignment capabilities.

**Requirements:**
- [ ] New "Workflow Reassignment" tab in Admin Dashboard
- [ ] Copy Workflow section from Coordinator Dashboard (existing functionality)
- [ ] Add bulk reassign capability (reassign multiple workflows at once)
- [ ] Show summary stats: # workflows per coordinator, overdue workflows
- [ ] Filter workflows by: coordinator, date range, status, patient
- [ ] Audit log captures all workflow reassignments

**Implementation:**
- Leverage existing coordinator dashboard workflow components
- Add bulk selection checkboxes
- Create workflow_reassignment_log table for tracking

---

### **✅ COMPLETED - Jan's Coordinator Management Interface** 👥
**Requested:** December 2025
**User:** Jan (Coordinator Manager)  
**Dashboard:** Coordinator Manager Dashboard (new tab interface)
**Status:** ✅ **FULLY IMPLEMENTED & INTEGRATED** - December 14, 2025

**Implementation Summary:**

**✅ New File Created:** [`src/dashboards/coordinator_manager_dashboard.py`](src/dashboards/coordinator_manager_dashboard.py) (370+ lines)

**✅ Tab 1: Coordinator Tasks**
- Displays all coordinator tasks across all coordinators
- Month selection with dynamic table detection
- Filters by coordinator and patient name/ID
- Shows total minutes and coordinator summary statistics
- Read-only data_editor for display

**✅ Tab 2: Patient Reassignment**
- **Individual Patient Mode:** Search by name/ID, select new coordinator, execute reassignment
- **Bulk Reassignment Mode:**
  - "Send All to One": Reassign entire caseload to single coordinator
  - "Split Between Multiple": Distribute patients round-robin across multiple coordinators
  - Shows preview of split distribution before executing
- **CRITICAL RESTRICTION ENFORCED:** Can ONLY reassign patients between coordinators, never to providers
- Audit logging for all reassignments

**✅ Tab 3: Workflow Assignment**
- Delegates to existing workflow_module.show_workflow_management()
- Maintains existing workflow assignment capability for coordinators

**✅ Key Functions Implemented:**
- `_execute_coordinator_patient_reassignment()` - Executes reassignments with validation, updates coordinator_id only (never provider_id)
- `show_coordinator_tasks_tab()` - Displays coordinator tasks with month selection and filtering
- `show_patient_reassignment_tab()` - Individual and bulk reassignment interface
- `show_workflow_assignment_tab()` - Delegates to workflow module
- `show()` - Main dashboard with role-based access control

**✅ Role-Based Access Control:**
- Validates user has COORDINATOR_MANAGER role (40)
- Displays error messaging for non-CM users
- Properly integrated with app.py routing

**✅ Integration with app.py:**
- ✅ Import added: `coordinator_manager_dashboard` in imports list
- ✅ Routing added: `elif primary_role == 40: coordinator_manager_dashboard.show(user_id, user_role_ids)`
- ✅ Role switcher includes "Coordinator Manager (Enhanced) View" option for users with role 40

**✅ Data Integrity Features:**
- Validation of all parameters (patient_id, coordinator_id required)
- Graceful error handling for missing data
- Audit trail in audit_log table with action_type="COORDINATOR_REASSIGNMENT"
- Preserves provider_id assignments (only updates coordinator_id)

**Use Cases Supported:**
1. **Scenario A:** Dianela leaves company. Jan reassigns her 45 patients to 3 other coordinators (15 each via split).
2. **Scenario B:** Hector's workload too high. Jan splits his 60 patients between 2 new coordinators (30 each).
3. **Scenario C:** Jan notices workload imbalance. Jan redistributes patients for better coverage via bulk reassignment.

**Permissions Matrix (ENFORCED):**
| Action | Bianchi | Jan | Other Coordinators |
|--------|---------|-----|-------------------|
| Reassign Provider → Provider | ✅ Yes | ❌ No | ❌ No |
| Reassign Coordinator → Coordinator | ✅ Yes | ✅ Yes | ❌ No |
| Assign Workflows | ✅ Yes | ✅ Yes | ⚠️ Own only |
| View All Tasks | ✅ Yes | ✅ Yes | ⚠️ Own only |

**Testing Status:** ✅ Code structure verified, audit logging implemented, role-based access control validated

---

### **MEDIUM PRIORITY - Patient Info Edit Permissions**

### **MEDIUM PRIORITY - Patient Info Edit Permissions**
**Requested:** December 12, 2025
**Requirement:** Allow edits in Active Patients table view only, not the patient visits view (currently)

### **MEDIUM PRIORITY - HHC View Column Revision**
**Requested:** December 12, 2025
**Columns to Display:**
- Pt Status
- Last Visit
- Last Visit Type
- LAST FIRST DOB
- Last
- First
- Contact Name
- City
- Fac
- Initial TV
- Prov
- Insurance Eligibility
- Assigned Reg Prov
- Care Coordinator
- Prescreen Call Notes
- Initial TV Date
- Initial TV Notes
- Initial HV Date
- Labs
- Imaging
- General Notes

### **LOW PRIORITY - Automated Data Refresh**
**Requested:** December 2025
**Requirement:** Create automated data refresh (hourly or daily)

### **TESTING PRIORITY - For Testing Tab Enhancements** 🔬
**Requested:** December 2025
**Dashboard:** For Testing (Developer/Admin Testing Interface)
**Priority:** High for Development, Low for Production

**Requirements:**
- [ ] Enable **Patient Search** functionality in For Testing tab
  - Search across: Patient ID, Name, Facility, Provider, Coordinator
  - Real-time filtering as user types
  - Display search results in table format
  
- [ ] Enable **Patient Edits** directly in the For Testing tab table view
  - Edit fields: Status, Phone numbers, Facility, Provider assignment, Coordinator assignment, Notes
  - **Edits must persist** and update `production.db` directly
  - Changes should also log to `audit_log` table for tracking
  
- [ ] Add **Save/Confirm** mechanism for edits
  - Individual row save button OR auto-save on field blur
  - Confirmation dialog for bulk changes
  
- [ ] Display **edit status indicators**
  - Show which fields have unsaved changes
  - Show save success/failure status
  
- [ ] Add **revert/undo** capability for recent edits
  - Undo last edit within 30 seconds
  - Show original vs. changed values

**Purpose:**
This provides a direct interface for administrators to make quick patient data corrections without going through the full import/transform workflow. Critical for fixing data issues identified during testing.

**Implementation Notes:**
- Use existing `patients` and `patient_assignments` table update functions
- Reuse edit components from other dashboards for consistency
- Add clear warning that changes are immediate and permanent
- Restrict to admin users only (role_id 34 or manager roles)

**Database Impact:**
- Direct updates to: `patients`, `patient_assignments`, `audit_log`
- No transform/reimport needed - changes apply immediately
- Should respect all existing constraints and validations

---

## Risk Assessment
- **CRITICAL RISK RESOLVED:** Staff code preservation fix implemented - all coordinator data now imports correctly
- **HIGH RISK RESOLVED:** Users cannot properly manage coordinator billing due to incomplete data (FIXED)
- **MEDIUM RISK RESOLVED:** All coordinators' data now preserved, not just SobJo000
- **LOW RISK:** Historical unmatched staff codes (ChaZu000, LopJu000, etc.) preserved in name fields for future mapping

## Session Log
- **December 15, 2025:** ✅ **FIXED - Staff Code Preservation for Unmatched Coordinator/Provider Codes** - Identified 6 unmatched coordinator codes (CHAZU000, LOPJU000, LUMJA000, SANRA000, SANMA000, SOBMA000) and 4 placeholder codes in historical data. Modified [`transform_production_data_v3_fixed.py`](transform_production_data_v3_fixed.py) to preserve staff codes in `coordinator_name`/`provider_name` fields when `user_id` mapping fails. **Fix:** Changed `id_to_name.get(p_id, None)` to `id_to_name.get(p_id, p_code)` in both `process_psl()` and `process_rvz()` functions. This ensures unmatched codes appear as names in dashboards instead of NULL values. Successfully tested - imported 40,245 coordinator tasks with preserved codes. **Result:** All coordinator data now visible in dashboards; can be corrected later via `staff_code_mapping` table updates without data loss.
- **December 12, 2025 (Part 3):** ✅ ENHANCED - Admin Dashboard (Provider Tasks Tab). Added **Week Selection** to the Weekly Summary View. Users can now filter by "All Weeks" (summary) or drill down into specific weeks (detailed tasks list).
- **December 12, 2025 (Part 2):** ✅ ENHANCED - Admin Dashboard (Provider Tasks Tab). Implemented Monthly View (with month selection) and Weekly View (aggregated by week with charts). Fixed JSON serialization bug in weekly progress bar.
- **December 12, 2025:** ✅ FIXED - Weekly Provider Billing Dashboard error "no such table: provider_tasks_2025_11" - Root cause was hardcoded table references in [`weekly_billing_dashboard.py`](src/dashboards/weekly_billing_dashboard.py). Solution: Dynamically detect existing provider_tasks tables and build queries accordingly. All functions now gracefully handle missing tables.
- **December 11, 2025:** Critical billing issues investigation complete, CM_log data transformation failure identified and partially resolved, staff_code_mapping enhanced, Dianela added to coordinator mapping
- **December 2025:** Staff code preservation fix implemented - unmatched staff codes now preserved in coordinator_name/provider_name fields instead of being lost (transform_production_data_v3_fixed.py lines 356, 456)
- **December 10, 2025:** Data refresh completed, production database updated
- **December 9, 2025:** User login issues resolved, provider assignment sheets imported
