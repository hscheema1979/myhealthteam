# Phase 2 Quick Start Guide

**Status:** ✅ COMPLETE  
**Last Updated:** January 2025  
**Test Coverage:** 5/5 Tests Passing  

---

## TL;DR - What Changed

### The Problem We Solved
- Billing dashboards were querying raw task tables (no audit trail)
- No workflow state tracking (billing status progression)
- No user accountability (who marked as billed/paid?)
- Impossible to track tasks through billing lifecycle

### The Solution Implemented
Four new database functions + completely rewritten Provider Billing Dashboard that:
- ✅ Uses workflow tables as single source of truth
- ✅ Tracks complete audit trail (user_id + timestamps)
- ✅ Manages state transitions (Pending → Billed → Invoiced → ... → Paid)
- ✅ Integrates with new helper functions for state updates

---

## Files Modified

### 1. `src/database.py` - Added 4 Functions
**Location:** Lines 4686-4932

```python
# Function 1: Mark provider tasks as billed
mark_provider_tasks_as_billed(billing_status_ids, user_id)
→ Returns: (success: bool, message: str, updated_count: int)

# Function 2: Mark coordinator tasks as billed
mark_coordinator_tasks_as_billed(summary_ids, user_id)
→ Returns: (success: bool, message: str, updated_count: int)

# Function 3: Approve provider payroll
approve_provider_payroll(payroll_ids, user_id)
→ Returns: (success: bool, message: str, updated_count: int)

# Function 4: Mark payroll as paid
mark_provider_payroll_as_paid(payroll_ids, user_id, payment_method, payment_reference)
→ Returns: (success: bool, message: str, updated_count: int)
```

**Key Features:**
- All functions use try/except/finally pattern
- Tuple returns for consistent error handling
- User tracking (billed_by, approved_by, paid_by)
- Automatic timestamps (CURRENT_TIMESTAMP)
- Transaction support (commit/rollback)

### 2. `src/dashboards/weekly_provider_billing_dashboard.py` - Complete Rewrite
**What Changed:**
- ❌ Old: Queried `provider_tasks_YYYY_MM` + `task_billing_codes` join
- ✅ New: Queries `provider_task_billing_status` workflow table

**New Features:**
- Billing week selection (dynamic from workflow table)
- Status filtering (Pending, Billed, Invoiced, Submitted, etc.)
- View modes (All Tasks, Pending Only, Billed Only)
- Sorting options (Task Date, Provider, Patient, Status)
- Audit trail toggle (shows billed_date, billed_by, updated_date)
- Workflow actions (mark selected as billed with verification)
- Smart export (includes "Download for Biller" that excludes internal columns)

**Access Control:**
```python
can_edit = can_mark_as_billed(user_role_ids)  # Only role 34 (Admin)
```

### 3. `tests/test_billing_workflow_phase2.py` - New Test Suite
**5 Comprehensive Tests:**
1. ✅ Mark Provider Tasks as Billed - PASS
2. ✅ Mark Coordinator Tasks as Billed - PASS
3. ✅ Approve Provider Payroll - PASS
4. ✅ Mark Payroll as Paid - PASS
5. ✅ Query Billing Workflow Status - PASS

**Run Tests:**
```bash
cd Dev
python tests/test_billing_workflow_phase2.py
```

---

## Database Schema Change

### Added Column
```sql
ALTER TABLE provider_task_billing_status ADD COLUMN billed_date DATETIME;
```

**Status:** ✅ Already applied to production.db

### Workflow Tables Ready
| Table | Records | Purpose |
|-------|---------|---------|
| provider_task_billing_status | 20,396 | Weekly provider billing workflow |
| coordinator_monthly_summary | 12,761 | Monthly coordinator billing workflow |
| provider_weekly_payroll_status | 627 | Weekly provider payroll workflow |

---

## How to Use

### For Dashboard Users

**Step 1: Access Dashboard**
- Go to Provider role section
- Select "Weekly Provider Billing Dashboard"

**Step 2: Select Billing Week**
- Dropdown shows all available weeks
- Shows date range (e.g., "2025-01-13 to 2025-01-19")

**Step 3: View Data**
- Summary metrics at top (total tasks, minutes, billed count, etc.)
- Detailed table with all billing records
- Filter by status: Pending, Billed, Invoiced, etc.
- Toggle view modes: All/Pending/Billed only

**Step 4: Mark Tasks as Billed** (Harpreet/Admin only)
- Enter billing status IDs: `1,5,10,23`
- Review confirmation table
- Click "Mark Selected as Billed"
- Dashboard auto-refreshes

**Step 5: Export**
- **Download for Biller** - Use this for 3rd party system (excludes internal columns)
- **Download Full Data** - Complete dataset with all columns
- **Download Pending** - Only unbilled tasks

### For Developers

**Import the Functions**
```python
from src import database

# Mark tasks as billed
success, msg, count = database.mark_provider_tasks_as_billed([1,2,3], user_id=1)
if success:
    print(f"Updated {count} records: {msg}")
else:
    print(f"Error: {msg}")

# Approve payroll
success, msg, count = database.approve_provider_payroll([100,101], user_id=1)

# Mark as paid
success, msg, count = database.mark_provider_payroll_as_paid(
    [100,101], 
    user_id=1,
    payment_method="ACH",
    payment_reference="ACH_20250115_001"
)
```

**Query Workflow Status**
```python
conn = database.get_db_connection()

# Get all pending provider billing
pending = conn.execute("""
    SELECT billing_status_id, provider_name, patient_name, task_date
    FROM provider_task_billing_status
    WHERE is_billed = FALSE
    ORDER BY task_date DESC
""").fetchall()

# Get all approved payroll
approved = conn.execute("""
    SELECT payroll_id, provider_name, total_payroll_amount
    FROM provider_weekly_payroll_status
    WHERE is_approved = TRUE AND is_paid = FALSE
""").fetchall()

conn.close()
```

---

## What Workflows Look Like Now

### Provider Billing Workflow
```
Task in provider_tasks_YYYY_MM (raw)
    ↓
↦ Insert into provider_task_billing_status
    - is_billed = FALSE
    - billing_status = 'Pending'
    ↓
↦ Harpreet/Justin marks as billed
    - UPDATE: is_billed = TRUE
    - UPDATE: billed_date = NOW
    - UPDATE: billed_by = user_id
    - UPDATE: billing_status = 'Billed'
    ↓
↦ Ready for 3rd party biller (query WHERE is_billed = TRUE AND is_invoiced = FALSE)
    - Biller invoices the claim
    - UPDATE: is_invoiced = TRUE
    ↓
↦ Rest of workflow: Submitted → Processed → Approved to Pay → Paid
```

### Payroll Workflow
```
Provider tasks aggregated into provider_weekly_payroll_status (weekly by provider + visit type)
    ↓
↦ Justin approves payroll
    - UPDATE: is_approved = TRUE
    - UPDATE: approved_date = NOW
    - UPDATE: approved_by = user_id
    - UPDATE: payroll_status = 'Approved'
    ↓
↦ Justin marks as paid (after ACH sent)
    - UPDATE: is_paid = TRUE
    - UPDATE: paid_date = NOW
    - UPDATE: paid_by = user_id
    - UPDATE: payment_method = 'ACH'
    - UPDATE: payment_reference = 'ACH_ID_123'
    - UPDATE: payroll_status = 'Paid'
```

---

## Key Concepts

### Audit Trail
Every action is logged:
```
billed_by: 1 (user_id of Harpreet/Justin)
billed_date: 2025-01-15 14:23:45
updated_date: 2025-01-15 14:23:45
```

### State Machine
Billing progresses through states:
```
Pending → Billed → Invoiced → Submitted → Processed → Approved to Pay → Paid
```

Each state has:
- Boolean flag (is_billed, is_invoiced, etc.)
- Date timestamp (billed_date, invoiced_date, etc.)
- For some states: user_id who made the transition

### Workflow Tables (Single Source of Truth)
```
provider_task_billing_status
  ├─ is_billed, billed_date, billed_by
  ├─ is_invoiced, invoiced_date
  ├─ is_claim_submitted, claim_submitted_date
  ├─ is_insurance_processed, insurance_processed_date
  ├─ is_approved_to_pay, approved_to_pay_date
  ├─ is_paid, paid_date
  └─ billing_status (text description of current state)

coordinator_monthly_summary (same structure)

provider_weekly_payroll_status
  ├─ is_approved, approved_date, approved_by
  ├─ is_paid, paid_date, paid_by
  ├─ payment_method ('ACH', 'Check', etc.)
  ├─ payment_reference (check #, ACH ID, etc.)
  └─ payroll_status (text description)
```

---

## Critical Rules

### ✅ DO
- ✅ Query workflow tables for billing/payroll status
- ✅ Track user_id for all state changes
- ✅ Use CURRENT_TIMESTAMP for all dates
- ✅ Export to 3rd party biller WITHOUT internal columns
- ✅ Include ALL tasks in billing (even "paid by zen")
- ✅ Keep billing and payroll separate (different workflows)

### ❌ DON'T
- ❌ Query raw task tables for billing reports
- ❌ Exclude "paid by zen" tasks from billing
- ❌ Skip user_id validation before updates
- ❌ Mix billing status with payroll status
- ❌ Export "paid by zen" to 3rd party biller (internal only)

---

## Testing

### Run All Tests
```bash
cd Dev
python tests/test_billing_workflow_phase2.py
```

**Expected Output:**
```
TEST 1: Mark Provider Tasks as Billed
  ✓ PASS - Successfully marked 3 provider tasks as billed

TEST 2: Mark Coordinator Tasks as Billed
  ✓ PASS - Successfully marked 2 coordinator tasks as billed

TEST 3: Approve Provider Payroll
  ✓ PASS - Successfully approved 2 payroll records

TEST 4: Mark Provider Payroll as Paid
  ✓ PASS - Successfully marked 2 payroll records as paid

TEST 5: Query Billing Workflow Status
  ✓ PASS - All workflow tables have data

RESULTS: 5/5 Tests Passed
```

### Code Quality
```bash
cd Dev
python -m pylint src/database.py
python -m pylint src/dashboards/weekly_provider_billing_dashboard.py
```

**Expected:** 0 errors, 0 warnings ✅

---

## Troubleshooting

### Dashboard Shows "No billing data available"
**Solution:** Check if `provider_task_billing_status` table exists and has records
```python
import sqlite3
conn = sqlite3.connect('production.db')
count = conn.execute("SELECT COUNT(*) FROM provider_task_billing_status").fetchone()[0]
print(f"Total records: {count}")
conn.close()
```

### "You don't have permission to modify billing status"
**Cause:** User doesn't have role 34 (Admin)
**Solution:** Contact administrator to add Admin role to user account

### "Mark as Billed" button doesn't appear
**Cause:** User's `user_role_ids` doesn't include role 34
**Solution:** Verify `user_role_ids` is being passed correctly from auth system

### Test fails with "no such column: billed_date"
**Solution:** Apply schema fix
```bash
python -c "
import sqlite3
conn = sqlite3.connect('production.db')
conn.execute('ALTER TABLE provider_task_billing_status ADD COLUMN billed_date DATETIME;')
conn.commit()
conn.close()
print('✓ Added billed_date column')
"
```

---

## What's Next (Phase 3)

1. **Monthly Coordinator Billing Dashboard** (similar to provider dashboard)
2. **Provider Payroll Dashboard** (with paid_by_zen indicators for Justin)
3. **3rd Party Biller Integration** (API endpoint for automated pulls)

---

## Questions?

Refer to:
- **Full Details:** `docs/PHASE_2_IMPLEMENTATION_SUMMARY.md`
- **Architecture:** `docs/BILLING_WORKFLOW_ARCHITECTURE.md`
- **Billing vs Payroll:** `docs/BILLING_VS_PAYROLL_SEPARATION.md`
- **Test Code:** `tests/test_billing_workflow_phase2.py`
- **Database Code:** `src/database.py` (lines 4686-4932)
- **Dashboard Code:** `src/dashboards/weekly_provider_billing_dashboard.py`

---

**Phase 2 Status: ✅ COMPLETE AND READY FOR PRODUCTION**