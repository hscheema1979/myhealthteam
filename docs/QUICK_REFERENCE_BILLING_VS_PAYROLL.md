# Quick Reference: Billing vs Payroll Separation

**CRITICAL:** Read this before any billing/payroll work. This is the most important architectural distinction in the system.

---

## The Core Truth

```
SAME TASK → TWO DIFFERENT FINANCIAL PROCESSES
```

| Aspect | Billing | Payroll |
|--------|---------|---------|
| **What** | ZEN gets reimbursed by Medicare | Provider gets paid by ZEN |
| **Who** | 3rd party billing service + Medicare | Justin approves payments |
| **When** | June 30: Task billed to Medicare | June 5: Provider paid by ZEN |
| **Timeline** | Takes 2-3 months for reimbursement | Immediate or next payroll cycle |
| **Status** | Pending→Billed→Invoiced→Submitted→Processed→Approved→Paid | Pending→Approved→Paid |
| **"Paid by zen"** | IGNORE IT | CRITICAL - Prevent double-payment |

---

## "Paid by zen" Flag Explained

### What It Means
- ✓ Provider was already compensated for this task
- ✓ Don't pay provider again on regular payroll
- ✓ Track this for audit trail

### What It Does NOT Mean
- ❌ Task shouldn't be billed to Medicare
- ❌ Task is exempt from billing workflow
- ❌ Task can be excluded from reports
- ❌ Biller should know about it

### Statistics
- **3,824 tasks (18.7%)** marked "paid by zen"
- **16,572 tasks (81.3%)** regular payroll
- **ALL 20,396 tasks MUST be billed to Medicare**

---

## Database Tables

### `provider_task_billing_status` (Billing Workflow)

**What goes in:** ALL 20,396 tasks

**What comes out (to 3rd party biller):**
```sql
SELECT provider_id, provider_name, patient_name, task_date,
       task_description, minutes_of_service, billing_code,
       billing_code_description, billing_status, is_billed
FROM provider_task_billing_status
WHERE is_billed = TRUE AND billing_week = ?
-- NOTE: paid_by_zen column EXCLUDED from this report
```

**Do NOT include:**
- `paid_by_zen` column
- `notes` field (if it contains "paid by zen")
- Any internal ZEN payment history

---

### `provider_weekly_payroll_status` (Payroll Workflow)

**What goes in:** ALL 20,396 tasks (aggregated by provider+visit_type+week)

**What Justin sees:**
```
Provider: Albert Diaz
Visit Type: Home Visit
Week: 2025-06-30

Total Tasks: 4
Total Minutes: 240

Already Paid by ZEN: 4 tasks, 240 minutes ← CRITICAL LINE
→ Justin knows: "Don't pay these again!"
```

**DO include:**
- `paid_by_zen_count` - Number of tasks already compensated
- `paid_by_zen_minutes` - Minutes already compensated
- Full transparency for Justin's decision-making

---

## Dashboard Visibility

### 3rd Party Billing Service
✗ NO `paid_by_zen` info
✗ NO internal payment details
✓ Just what to bill to Medicare

### Justin's Payroll Dashboard
✓ YES `paid_by_zen_count` (prevent double-payment)
✓ YES `paid_by_zen_minutes` (prevent double-payment)
✓ Full visibility for informed approvals

### Harpreet (Billing Management)
✓ YES `paid_by_zen` flag (for audits)
✗ Cannot approve payroll (separation of duties)

---

## Common Mistakes (DO NOT DO)

### ❌ MISTAKE 1
```python
# WRONG: Excluding paid_by_zen from billing
SELECT * FROM provider_task_billing_status
WHERE paid_by_zen = FALSE  # ❌ This excludes legitimate billing!

# CORRECT: Include all
SELECT * FROM provider_task_billing_status
WHERE is_billed = TRUE     # ✓ All tasks, paid_by_zen doesn't matter
```

### ❌ MISTAKE 2
```python
# WRONG: Hiding paid_by_zen from Justin
SELECT provider_id, task_count, total_minutes
FROM provider_weekly_payroll_status
# ❌ Justin doesn't see paid_by_zen_count - might double-pay!

# CORRECT: Show everything
SELECT provider_id, task_count, total_minutes,
       paid_by_zen_count, paid_by_zen_minutes
FROM provider_weekly_payroll_status
# ✓ Justin has complete picture
```

### ❌ MISTAKE 3
```python
# WRONG: Exposing paid_by_zen to biller
SELECT *, paid_by_zen FROM provider_task_billing_status
# ❌ Biller sees internal payment history - not their concern!

# CORRECT: Exclude internal columns
SELECT provider_id, patient_name, billing_code, minutes_of_service
FROM provider_task_billing_status
# ✓ Biller gets only what they need
```

### ❌ MISTAKE 4
"If provider is marked 'paid by zen', don't bill Medicare"

**WRONG!** Same task, different processes:
- Payroll: Provider already paid (don't pay again) ✓
- Billing: Still need to bill Medicare (get reimbursed) ✓

---

## Implementation Checklist

- [ ] Billing dashboard excludes `paid_by_zen` column in reports
- [ ] Billing export to 3rd party has NO `paid_by_zen` info
- [ ] Justin's payroll view INCLUDES `paid_by_zen_count` and `paid_by_zen_minutes`
- [ ] All 20,396 tasks included in both billing AND payroll
- [ ] Transform script correctly populates `paid_by_zen` flag
- [ ] Team understands: Billing and Payroll are independent
- [ ] Documentation updated whenever processes change

---

## Questions Before You Code

1. **"Should this task be billed to Medicare?"**
   → YES if valid task_date + billing_code (regardless of paid_by_zen)

2. **"Should this provider be paid from payroll?"**
   → Check paid_by_zen_count - if >0, already paid; if 0, needs payment

3. **"Should the biller see paid_by_zen?"**
   → NO - exclude it completely

4. **"Are billing and payroll the same workflow?"**
   → NO - different processes, different timelines, same tasks

5. **"Can a task be paid to provider but not billed to Medicare?"**
   → NO - both must happen eventually (task is performed → provider paid → Medicare billed)

---

## Key Rules (NEVER FORGET)

### Rule 1: Separate Workflows
Billing status ≠ Payroll status. They track different things independently.

### Rule 2: Payroll-Only Flag
`paid_by_zen` is ONLY for preventing double-payment to providers. Not for billing.

### Rule 3: Complete Coverage
- Billing: 20,396 tasks
- Payroll: 20,396 tasks (aggregated)
- Zero exclusions based on paid_by_zen

### Rule 4: Visibility Control
- Biller: NO paid_by_zen
- Justin: YES paid_by_zen (safety critical)
- Providers: NO paid_by_zen
- Medicare: NO paid_by_zen

### Rule 5: Business Logic
"Paid by zen" means:
- Payroll: Provider already compensated (prevent re-payment) ✓
- Billing: Still must bill Medicare (get reimbursement) ✓

---

## Data Statistics (as of Dec 15, 2025)

```
Total Provider Tasks: 20,396
├─ Marked "paid by zen": 3,824 (18.7%)
└─ Regular payroll: 16,572 (81.3%)

Total Minutes: 824,640
├─ Paid by ZEN: 143,560 minutes (17.4%)
└─ Regular payroll: 681,080 minutes (82.6%)

ALL 20,396 TASKS MUST BE BILLED TO MEDICARE
```

---

## See Also
- `BILLING_VS_PAYROLL_SEPARATION.md` - Complete explanation
- `BILLING_WORKFLOW_ARCHITECTURE.md` - System design
- `PHASE_1_COMPLETION_SUMMARY.md` - Implementation status

---

**Last Updated:** December 15, 2025  
**Status:** Active - Living Document  
**Priority:** CRITICAL - Read before any coding