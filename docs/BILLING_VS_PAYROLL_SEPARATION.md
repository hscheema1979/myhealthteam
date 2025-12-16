# Billing vs Payroll Separation - Critical Architecture Document

**Date:** December 15, 2025  
**Priority:** CRITICAL - Read before any billing/payroll work  
**Status:** Active - Living Document

---

## Executive Summary

ZEN Medical has **TWO COMPLETELY SEPARATE FINANCIAL WORKFLOWS** that operate on the SAME tasks:

1. **PAYROLL** - ZEN pays providers for work performed
2. **BILLING** - ZEN bills Medicare/insurance for reimbursement

These are independent processes on different timelines with different stakeholders.

### The Critical Distinction

```
TASK IS PERFORMED
    ↓
PAYROLL: Provider gets paid by ZEN (internal)
    ↓
BILLING: ZEN gets paid by Medicare (external)
```

Both happen, but they're managed separately. **The "paid by zen" flag tracks PAYROLL status, NOT billing eligibility.**

---

## Why This Matters

### Real-World Scenario

**June 1, 2025:** Provider Albert Diaz performs a Home Visit (240 minutes)

**Payroll:**
- ZEN pays Albert immediately (or on next payroll cycle)
- Marked in notes as "paid by zen"
- This is the provider's COMPENSATION for work

**Billing (happens separately):**
- Same task still needs to be billed to Medicare for reimbursement
- "Paid by zen" status is IRRELEVANT to billing eligibility
- ZEN needs Medicare to reimburse for this work to offset what was paid to Albert

**Timeline:**
```
June 1:  Task performed
June 5:  Provider paid by ZEN → "paid by zen" flag set
June 30: Provider task billed to Medicare (same task!)
July 30: Medicare processes and reimburses ZEN
August 15: ZEN receives reimbursement
```

ZEN paid out cash in June but didn't get reimbursed until August.

---

## Database Architecture - Correct Implementation

### `provider_task_billing_status` (Task-Level Billing Tracking)

**Purpose:** Track each task through Medicare billing lifecycle

**Key Columns:**
- `provider_id`, `provider_name`, `patient_name`
- `task_date`, `task_description`, `minutes_of_service`
- `billing_code`, `billing_code_description`
- `billing_week`, `week_start_date`, `week_end_date`
- `billing_status` - Current stage (Pending/Billed/Invoiced/Submitted/Processed/Approved/Paid)
- `is_billed`, `billed_date`, `billed_by` - Mark for 3rd party biller
- `is_invoiced`, `is_claim_submitted`, `is_insurance_processed`, `is_approved_to_pay`, `is_paid` - Workflow progression
- **`notes`** - Contains "paid by zen" text if provider was already compensated
- **`paid_by_zen`** - BOOLEAN flag (for internal tracking ONLY)

**WHO SEES THIS TABLE:**
- ✓ Justin (internal use)
- ✓ Harpreet (internal use)
- ✗ **3rd Party Billing Service (NEVER)**

**CRITICAL:** When exporting billing reports for 3rd party biller, **EXCLUDE the `paid_by_zen` column**. Biller only needs to see:
```sql
SELECT provider_id, provider_name, patient_name, task_date,
       task_description, minutes_of_service, billing_code,
       billing_code_description, billing_status, is_billed
FROM provider_task_billing_status
WHERE is_billed = TRUE AND billing_week = ?
-- NOTE: paid_by_zen column intentionally excluded from this report
```

---

### `provider_weekly_payroll_status` (Aggregated Payroll Tracking)

**Purpose:** Track payroll obligations and payments to providers

**Key Columns:**
- `provider_id`, `provider_name`
- `pay_week_start_date`, `pay_week_end_date`, `pay_week_number`, `pay_year`
- `visit_type` - Different pay rates per type
- `task_count`, `total_minutes_of_service` - ALL tasks (including paid_by_zen)
- `payroll_status` - Pending/Approved/Paid/Held
- `is_approved`, `approved_date`, `approved_by` - Justin's approval
- `is_paid`, `paid_date`, `paid_by` - Payment execution
- **`paid_by_zen_count`** - Number of tasks already paid by ZEN (PREVENT DOUBLE-PAYMENT)
- **`paid_by_zen_minutes`** - Minutes already compensated (PREVENT DOUBLE-PAYMENT)

**INCLUDES ALL TASKS:**
- Tasks marked "paid by zen" ARE included (they still represent work that needs payment, just already paid)
- Tasks not marked "paid by zen" are included (regular payroll)
- Purpose: Show Justin the complete picture

**WHAT JUSTIN SEES:**
```
Provider: Albert Diaz
Visit Type: Home Visit
Week: 2025-06-30

Total Tasks: 4
Total Minutes: 240

Already Paid by ZEN: 4 tasks, 240 minutes
→ Justin knows: "Don't pay these again, they were already compensated"
```

**WHO SEES THIS TABLE:**
- ✓ Justin (approval and payment processing)
- ✗ Harpreet (separation of duties - billing only)
- ✗ Providers
- ✗ 3rd Party Biller

---

## The "Paid by ZEN" Flag - Complete Explanation

### Where It Comes From

In the PSL (Provider Service Log) CSV files, the **Notes column** contains literal text "paid by zen" to indicate:
- **Provider has already been compensated** for this specific task
- This was typically an upfront or emergency payment
- ZEN covered the cost immediately rather than waiting for normal payroll cycle

### Example Data
```
Provider: ZEN-ANE
Patient: ZEN-ROBLES ANAYA, RAMON 11/28/1942
DOS: 06/01/25
Service: PCP-Visit Home (HO)
Minutes: 60-69
Coding: 99350
Notes: paid by zen  ← THIS FLAG
```

### What It Does NOT Mean

❌ "Paid by zen" does NOT mean:
- Task doesn't need to be billed to Medicare
- Task is exempt from billing workflows
- Medicare shouldn't reimburse this work
- Task is internal-only and shouldn't appear in billing reports

### What It DOES Mean

✓ "Paid by zen" MEANS:
- **Payroll:** Provider was already paid (don't pay again on regular payroll)
- **Audit:** This provider received upfront/emergency compensation
- **Tracking:** Know which providers got paid outside normal cycle
- **Internal:** Prevent double-payment to same provider

### Statistics (as of Dec 15, 2025)

```
Total Provider Tasks: 20,396
Marked "paid by zen": 3,824 (18.7%)
Regular payroll: 16,572 (81.3%)

Minutes:
Paid by ZEN: 143,560 minutes
Regular payroll: 681,080 minutes
Total: 824,640 minutes
```

---

## Workflow Comparison

### Billing Workflow (Medicare Reimbursement)

| Aspect | Detail |
|--------|--------|
| **Initiator** | Justin / Harpreet |
| **Tasks Included** | ALL 20,396 (includes paid_by_zen) |
| **Excludes** | NOTHING - all tasks must be billed |
| **Table** | provider_task_billing_status |
| **Status Flow** | Pending → Billed → Invoiced → Submitted → Processed → Approved → Paid |
| **External Handoff** | 3rd Party Billing Service (sees NO paid_by_zen flag) |
| **Payment Source** | Medicare / Insurance |
| **"Paid by zen" Impact** | NONE - doesn't affect billing eligibility |
| **Key Question** | "What do we bill Medicare for?" |

### Payroll Workflow (Provider Compensation)

| Aspect | Detail |
|--------|--------|
| **Initiator** | Justin |
| **Tasks Included** | ALL 20,396 (includes paid_by_zen) |
| **Excludes** | NOTHING - all tasks represent work done |
| **Table** | provider_weekly_payroll_status |
| **Status Flow** | Pending → Approved → Paid |
| **External Handoff** | Accounting/Bank (for payment processing) |
| **Payment Source** | ZEN Medical (internal) |
| **"Paid by zen" Impact** | CRITICAL - Shows which providers already paid (prevent double-payment) |
| **Key Question** | "Which providers still need to be paid?" |

---

## Dashboard & Report Views

### Reports Going to 3rd Party Biller
```
MUST INCLUDE:
- provider_id, provider_name
- patient_name, task_date
- task_description, minutes_of_service
- billing_code, billing_code_description
- billing_status, is_billed

MUST EXCLUDE:
- paid_by_zen column
- paid_by_zen_count
- paid_by_zen_minutes
- Any internal ZEN payment notes
- Notes field (if it contains "paid by zen")

REASON:
Biller only cares about what to invoice to Medicare,
not internal ZEN payment history
```

### Justin's Payroll Dashboard
```
MUST INCLUDE:
- provider_id, provider_name
- visit_type, pay_week_start_date, pay_week_end_date
- task_count, total_minutes_of_service
- paid_by_zen_count ← CRITICAL (prevent double-payment)
- paid_by_zen_minutes ← CRITICAL (prevent double-payment)
- payroll_status, is_approved, is_paid

REASON:
Justin needs complete visibility to:
1. Know which providers need payment
2. Know which were already paid (don't pay again)
3. Make informed approval/payment decisions
```

---

## Data Population Rules

### When Populating `provider_task_billing_status`

1. **Include ALL tasks** from provider_tasks_YYYY_MM tables
2. **Parse notes field** for "paid by zen" text
3. **Set paid_by_zen flag** if text found
4. **Do NOT exclude based on paid_by_zen** - all tasks included
5. **Billing report exports** must exclude this column

### When Populating `provider_weekly_payroll_status`

1. **Include ALL tasks** from provider_task_billing_status
2. **Aggregate by:** provider_id + visit_type + week
3. **Calculate paid_by_zen counts** - sum tasks already compensated
4. **Show both:** total tasks AND paid_by_zen breakdown
5. **Justin uses paid_by_zen to identify:** which rows don't need payment

### When Exporting Billing Reports

1. **Query provider_task_billing_status**
2. **Filter:** WHERE is_billed = TRUE AND billing_week = ?
3. **Select columns:** Exclude paid_by_zen entirely
4. **Format:** CSV or per 3rd party biller specs
5. **Deliver to:** 3rd party billing service only

---

## Key Rules - NEVER FORGET

### Rule 1: Billing and Payroll Are Independent
```
Billing Status ≠ Payroll Status
Task marked "paid by zen" still gets billed to Medicare
Task with billing_status="Paid" doesn't affect payroll status
```

### Rule 2: "Paid by zen" Is Payroll-Only
```
paid_by_zen column → Payroll table ONLY
NEVER expose paid_by_zen to 3rd party biller
ALWAYS include it in Justin's payroll view
```

### Rule 3: All Tasks Included in Both Workflows
```
provider_task_billing_status: 20,396 tasks
provider_weekly_payroll_status: Same 20,396 tasks aggregated

No exclusions based on paid_by_zen
No filtering based on payment status
```

### Rule 4: "Paid by zen" Prevents Double-Payment
```
When Justin sees:
  paid_by_zen_count = 4 tasks, paid_by_zen_minutes = 240
  
He knows: "These were already compensated, don't approve for payment"
This is the ONLY purpose of the paid_by_zen flag
```

### Rule 5: Reports to External Parties
```
3rd Party Biller: NO paid_by_zen info (billing only)
Justin: YES paid_by_zen info (payroll safety)
Providers: NO paid_by_zen info (internal tracking)
Medicare: NO paid_by_zen info (not their concern)
```

---

## Common Mistakes - What NOT To Do

### ❌ MISTAKE 1: Excluding "paid by zen" from billing
```
WRONG:
SELECT * FROM provider_task_billing_status
WHERE paid_by_zen = FALSE  ← WRONG! This excludes legitimate billing

CORRECT:
SELECT * FROM provider_task_billing_status
WHERE is_billed = TRUE     ← Include all, paid_by_zen doesn't matter for billing
```

### ❌ MISTAKE 2: Hiding "paid by zen" from Justin
```
WRONG:
SELECT provider_id, task_count, total_minutes
FROM provider_weekly_payroll_status
-- paid_by_zen columns hidden ← WRONG! Justin needs to see to prevent double-pay

CORRECT:
SELECT provider_id, task_count, total_minutes,
       paid_by_zen_count, paid_by_zen_minutes
FROM provider_weekly_payroll_status
-- paid_by_zen columns visible ← CORRECT for safety
```

### ❌ MISTAKE 3: Exposing "paid by zen" to biller
```
WRONG:
SELECT *, paid_by_zen FROM provider_task_billing_status
-- Biller sees internal payment info ← WRONG! Not their concern

CORRECT:
SELECT provider_id, patient_name, task_date, minutes_of_service, billing_code
FROM provider_task_billing_status
-- No paid_by_zen column ← CORRECT for external reporting
```

### ❌ MISTAKE 4: Conflating the workflows
```
WRONG:
"Paid by zen tasks don't need billing"
"If provider is paid, don't pay them again from billing"

CORRECT:
"Paid by zen tasks still need billing to Medicare"
"Payroll and billing are separate processes"
"Provider payment and ZEN reimbursement are different"
```

---

## Implementation Checklist

- [x] `provider_task_billing_status` includes `paid_by_zen` column
- [x] `provider_task_billing_status` includes ALL 20,396 tasks
- [x] `provider_weekly_payroll_status` includes ALL tasks (aggregated)
- [x] `provider_weekly_payroll_status` includes `paid_by_zen_count` and `paid_by_zen_minutes`
- [x] Transform script populates both tables correctly
- [ ] Billing dashboard query excludes `paid_by_zen` column
- [ ] Billing export to 3rd party excludes `paid_by_zen` column
- [ ] Justin's payroll dashboard shows `paid_by_zen` columns
- [ ] Documentation in all dashboards explains the separation
- [ ] Team trained on this critical distinction

---

## Questions to Ask When Uncertain

1. **"Should this task be billed to Medicare?"**
   - Answer: YES if task_date is valid and billing_code exists (regardless of paid_by_zen)

2. **"Should this provider be paid from payroll?"**
   - Answer: Check paid_by_zen_count - if > 0, already paid; if 0, needs payment

3. **"Should the 3rd party biller see paid_by_zen?"**
   - Answer: NO - exclude it completely from exports

4. **"Are these the same 20,396 tasks in both tables?"**
   - Answer: YES - billing and payroll track the same work, just different purposes

5. **"Can a task be paid to provider but not yet billed to Medicare?"**
   - Answer: YES - this is exactly what "paid by zen" means (paid provider, still billing Medicare)

---

## Change History

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-15 | Created this document | Critical misunderstanding of billing vs payroll separation needed documentation |
| 2025-12-15 | Added paid_by_zen to payroll table | Prevent Justin from double-paying providers |
| 2025-12-15 | Removed paid_by_zen from billing exports | 3rd party biller doesn't need internal payment info |

---

## Related Documents

- `BILLING_WORKFLOW_ARCHITECTURE.md` - System design
- `PHASE_1_COMPLETION_SUMMARY.md` - Implementation status
- `BILLING_IMPLEMENTATION_PLAN.md` - Detailed implementation roadmap
- `PAYROLL_TAB_REQUIREMENTS.md` - Payroll-specific requirements

---

**CRITICAL REMINDER:** Billing and Payroll are independent financial workflows. The "paid by zen" flag is ONLY for preventing double-payment to providers. It has NO impact on billing eligibility or Medicare reimbursement.
