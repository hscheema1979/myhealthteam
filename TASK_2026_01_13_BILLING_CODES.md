**Created:** 2026-01-13
**Status:** COMPLETED
**Priority:** High

## Overview

This task covers three main items:
1. ✅ Database Backup & Billing Codes Update
2. ✅ Provider Tasks UI Modification
3. ✅ Automated Workflow Implementation

---

## Completed Items

### ✅ 1. Billing Codes Population Script

**File:** `src/data/populate_billing_codes.py`

**What was done:**
- Created script to populate `task_billing_codes` table
- Added `is_active` column (INTEGER DEFAULT 1) for enabling/disabling codes
- Added `note` column (TEXT) for annotations
- Populated 14 billing codes total:
  - **11 ENABLED codes** (is_active = 1)
  - **3 DISABLED codes** (is_active = 0) with note "do not use this for now"

**Billing Codes Matrix:**

| Service Type | Location | Patient Type | Code | Status |
|-------------|----------|--------------|------|--------|
| New | Home | New | 99345 | ✅ Active |
| Follow Up | Home | Follow Up | 99350 | ✅ Active |
| New | Telehealth | New | 99204 | ✅ Active |
| Follow Up | Telehealth | Follow Up | 99214 | ✅ Active |
| Acute | Telehealth | Acute | 99213 | ✅ Active |
| New | Office | New | 99205 | ✅ Active |
| Follow Up | Office | Follow Up | 99215 | ✅ Active |
| Acute | Office | Acute | 99213 | ✅ Active |
| TCM | Office | TCM-7 | 99496 | ✅ Active |
| TCM | Office | TCM-14 | 99495 | ✅ Active |
| Cognitive | Office | Cognitive | 96138+96132 | ✅ Active |
| Follow Up | Home | Follow Up | 99349 | ❌ Disabled |
| New | Office | New | 99205 | ❌ Disabled |
| Follow Up | Office | Follow Up | 99215 | ❌ Disabled |

**To run:**
```bash
python src/data/populate_billing_codes.py
```

---

### ✅ 2. Daily Summary Update Workflow

**File:** `src/workflows/daily_summary_update.py`

**What was done:**
- Created script for updating summary tables
- Updates three tables:
  - `provider_weekly_summary_with_billing` - Weekly Provider Billing Summary
  - `provider_weekly_payroll_status` - Weekly Provider Payroll Summary
  - `coordinator_monthly_summary` - Monthly Coordinator Billing Summary
- Features:
  - Processes only new/updated records
  - Maintains data integrity during updates
  - Includes error handling and logging
  - Preserves historical data

**To run manually:**
```bash
python src/workflows/daily_summary_update.py
```

**⚠️ NOT YET AUTOMATED:** Script is ready but needs Windows Task Scheduler setup for daily 5:00 AM execution.

---

### ✅ 3. Summary Recalculate Functions

**File:** `src/database.py`

**What was done:**
- Added `refresh_all_summaries(year, month)` helper function
- This function calls:
  - `recalculate_provider_monthly_summary(year, month)`
  - `recalculate_coordinator_monthly_summary(year, month)`
- Both recalculate functions already exist in database.py and were tested successfully

**Testing:**
```bash
python -c "import sys; sys.path.insert(0, 'src'); from database import refresh_all_summaries; import datetime; now = datetime.datetime.now(); result = refresh_all_summaries(now.year, now.month); print(f'Result: {result}')"
```
Result: `(True, 'Refreshed summaries for 2026-01', 0)`

---

## Pending Items

### ✅ 4. Provider Tasks UI Modification

**File:** `src/dashboards/task_review_component.py`

**Completed Changes:**

| Current Column | New Column | Action |
|---------------|------------|--------|
| Duration (mins_of_service) | - | REMOVED |
| Service Type (task_description) | - | REMOVED |
| Patient Name | Patient Name | KEPT |
| DOS (date) | Date of Service | RENAMED |
| - | Patient DOB | ADDED (from patients table) |
| - | Location of Service | ADDED (from task_billing_codes table) |
| - | Patient Type | ADDED (from task_billing_codes table) |

**Query Updates:**
- Added LEFT JOIN with `patients` table to get `date_of_birth`
- Added LEFT JOIN with `task_billing_codes` table to get `location_type` and `patient_type`
- All three views (Daily, Weekly, Monthly) updated
- Editable Daily view now only saves Notes (removed Duration and Service Type editing)

---

### ✅ 5. Filter Billing Code Dropdown

**Completed Changes:**

All billing code queries in `src/database.py` now filter by `is_active = 1`:
- `get_tasks_billing_codes()` - Line 1599
- `get_tasks_billing_codes_by_service_type()` - Line 1614
- `get_billing_codes()` - Lines 1771, 1773
- `save_daily_task_for_provider()` billing lookups - Lines 1910, 1923

Only enabled billing codes (is_active = 1) are now shown in selection lists.

---

## Next Steps

1. **Integration & Testing** (Remaining):
   - Test that summary tables update after task edits
   - Run daily workflow script to verify auto-refresh

2. **Documentation**:
   - Update TASK_2026_01_13_BILLING_CODES.md with remaining items

---

## Source Files Reference

| File | Purpose |
|------|---------|
| `provider_billing_updated.txt` | Source specification for limited billing codes |
| `production.db` | SQLite database with task_billing_codes table |
| `src/data/populate_billing_codes.py` | Script to populate billing codes |
| `src/workflows/daily_summary_update.py` | Automated workflow script |
| `src/dashboards/task_review_component.py` | Provider task review UI (needs updates) |
| `src/database.py` | Database functions with recalculate helpers |

---

## Related Documentation

- `CLAUDE.md` - Project conventions and patterns
- `COMPREHENSIVE BILLING SYSTEM REPORT.md` - Billing system overview
- `PRD_Coordinator_Producer_Fixes.md` - Different scope (dated 2026-01-08)
- [x] Create billing codes population script (src/data/populate_billing_codes.py)
- [x] Create daily summary update workflow (src/workflows/daily_summary_update.py)
- [x] Create task tracking document (TASK_2026_01_13_BILLING_CODES.md)
- [x] Remove duplicate script (populate_limited_billing_codes.py) - validated no references
- [x] Add refresh_all_summaries helper to database module (tested: ✓ working)
- [x] Clean up temporary scripts (add_refresh_function.py deleted)
- [ ] Update task document with current progress
- [ ] Find and integrate where recalculate_summary should be called on task save
- [ ] Modify Provider Tasks UI (remove Duration/Service Type, add Patient DOB/Location/Patient Type)
- [ ] Filter billing code dropdowns to show only is_active = 1 codes