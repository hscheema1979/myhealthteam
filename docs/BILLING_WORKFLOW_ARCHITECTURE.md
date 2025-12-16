# Billing & Payroll Workflow Architecture - Production Implementation

**Status:** Final Architecture Definition  
**Date:** January 2025  
**Priority:** P0 - Critical Revenue Cycle Management

⚠️ **CRITICAL DISTINCTION:** Read `BILLING_VS_PAYROLL_SEPARATION.md` FIRST before working on any billing or payroll features. Billing and Payroll are TWO COMPLETELY SEPARATE financial workflows on the SAME tasks.

---

## Executive Summary

The ZEN Medical system manages three distinct billing/payment workflows:

1. **Provider Billing (WEEKLY)** → Billed to Medicare via 3rd party billing service
2. **Coordinator Billing (MONTHLY)** → Billed to Medicare via 3rd party billing service  
3. **Provider Payroll (WEEKLY)** → Internal payment to providers (future: track amounts)

All workflows are tracked in dedicated workflow tables with audit trails and state machines.

---

## User Roles & Access Control

### Role Hierarchy
- **Harpreet (Admin/Bianchi)** - Full system access, all approvals
- **Justin** - Superuser: Can approve/update billing AND payroll
- **Future: 3rd Party Biller** - Can update billing workflow states (account setup pending)

### Current Access (Phase 1)
- **Billing Workflow Updates** (Provider & Coordinator)
  - ✅ Harpreet (Admin)
  - ✅ Justin (Superuser)
  - ⏳ 3rd Party Biller (Account setup pending)

- **Payroll Workflow Updates**
  - ✅ Justin only (Payroll Manager)
  - ❌ Harpreet cannot edit payroll (to maintain separation)

---

## Current State & Gap Analysis

### What Exists
- ✅ Raw task tables: `provider_tasks_YYYY_MM`, `coordinator_tasks` 
- ✅ Workflow table schemas: `provider_task_billing_status`, `coordinator_monthly_summary`
- ❌ **CRITICAL GAP**: Workflow tables are empty - transform process doesn't populate them
- ❌ Dashboards query raw tasks directly, bypassing workflow tracking
- ❌ No audit trail of billing state progression
- ❌ No separation between billing status and payroll status
- ❌ No payroll tracking table exists

### Why This Matters
- Without populated workflow tables, the 3rd party billing service cannot pull accurate reports
- No way to track which tasks have been billed, invoiced, or paid
- Compliance risk: cannot prove to Medicare which services were claimed
- Payment risk: providers paid before verification tasks are billed
- Audit risk: no timestamp trail of workflow state changes

---

## Architecture: Three Separate Workflows

### WORKFLOW 1: Provider Task Billing (Weekly to Medicare)

**Purpose:** Track provider task billing through lifecycle for weekly submission to 3rd party billing service

**Time Period:** Weekly (Monday-Sunday)

**Table:** `provider_task_billing_status` (task-level detail)

**Schema:**
```sql
CREATE TABLE provider_task_billing_status (
    -- Identity & References
    billing_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Task Reference
    provider_task_id INTEGER NOT NULL UNIQUE,  -- FK to source task
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    patient_id TEXT,
    
    -- Task Details
    task_date DATE NOT NULL,
    task_description TEXT,                  -- "Home Visit", "Telehealth", etc.
    minutes_of_service INTEGER,
    notes TEXT,
    
    -- Billing Coding
    billing_code TEXT,                      -- "99490", "99491", etc.
    billing_code_description TEXT,
    
    -- Week Information
    billing_week INTEGER NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- Workflow State Machine
    billing_status TEXT DEFAULT 'Pending',  -- Current workflow stage
    
    -- Workflow Progression (track each state with timestamp)
    is_billed BOOLEAN DEFAULT FALSE,
    billed_date DATETIME,
    billed_by TEXT,                         -- user_id who marked as billed
    
    is_invoiced BOOLEAN DEFAULT FALSE,
    invoiced_date DATETIME,
    
    is_claim_submitted BOOLEAN DEFAULT FALSE,
    claim_submitted_date DATETIME,
    
    is_insurance_processed BOOLEAN DEFAULT FALSE,
    insurance_processed_date DATETIME,
    
    is_approved_to_pay BOOLEAN DEFAULT FALSE,
    approved_to_pay_date DATETIME,
    
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATETIME,
    
    is_carried_over BOOLEAN DEFAULT FALSE,
    carried_over_reason TEXT,
    
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(provider_task_id),
    FOREIGN KEY (provider_task_id) REFERENCES provider_tasks_YYYY_MM(provider_task_id)
);

CREATE INDEX idx_provider_task_billing_week ON provider_task_billing_status(billing_week, provider_id);
CREATE INDEX idx_provider_task_billing_status ON provider_task_billing_status(billing_status);
CREATE INDEX idx_provider_task_billing_billed ON provider_task_billing_status(is_billed, billing_week);
CREATE INDEX idx_provider_task_billing_paid ON provider_task_billing_status(is_paid, billing_week);
```

**Weekly Billing Report** (extracted by 3rd party billing service):
```sql
-- Query for 3rd party biller to pull weekly report
SELECT
    billing_status_id,
    week_start_date,
    week_end_date,
    provider_id,
    provider_name,
    patient_id,
    patient_name,
    task_date,
    task_description,
    minutes_of_service,
    billing_code,
    billing_code_description
FROM provider_task_billing_status
WHERE billing_week = ?
  AND is_billed = TRUE
  AND is_invoiced = FALSE  -- Not yet invoiced
ORDER BY provider_id, task_date
```

---

### WORKFLOW 2: Coordinator Task Billing (Monthly to Medicare)

**Purpose:** Track coordinator task billing through lifecycle for monthly submission to 3rd party billing service

**Time Period:** Monthly (1st - last day of month)

**Table:** `coordinator_monthly_summary` (aggregated by patient/month)

**Schema:**
```sql
CREATE TABLE coordinator_monthly_summary (
    -- Identity & References
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Coordinator & Patient Reference
    coordinator_id INTEGER NOT NULL,
    coordinator_name TEXT NOT NULL,
    patient_id INTEGER NOT NULL,
    patient_name TEXT NOT NULL,
    
    -- Time Period
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_start_date DATE NOT NULL,
    month_end_date DATE NOT NULL,
    
    -- Aggregated Task Data
    total_tasks INTEGER DEFAULT 0,
    total_duration_minutes INTEGER DEFAULT 0,
    
    -- Billing Code (auto-assigned based on total minutes)
    -- 1-19 min → 99490, 20-50 min → 99491, 50+ min → 99492
    billing_code TEXT,
    billing_code_description TEXT,
    
    -- Workflow State Machine
    billing_status TEXT DEFAULT 'Pending',  -- Current workflow stage
    
    -- Workflow Progression (track each state with timestamp)
    is_billed BOOLEAN DEFAULT FALSE,
    billed_date DATETIME,
    billed_by TEXT,                         -- user_id who marked as billed
    
    is_invoiced BOOLEAN DEFAULT FALSE,
    invoiced_date DATETIME,
    
    is_claim_submitted BOOLEAN DEFAULT FALSE,
    claim_submitted_date DATETIME,
    
    is_insurance_processed BOOLEAN DEFAULT FALSE,
    insurance_processed_date DATETIME,
    
    is_approved_to_pay BOOLEAN DEFAULT FALSE,
    approved_to_pay_date DATETIME,
    
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATETIME,
    
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(coordinator_id, patient_id, year, month),
    FOREIGN KEY (coordinator_id) REFERENCES users(user_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE INDEX idx_coordinator_monthly_month ON coordinator_monthly_summary(year, month);
CREATE INDEX idx_coordinator_monthly_status ON coordinator_monthly_summary(billing_status);
CREATE INDEX idx_coordinator_monthly_billed ON coordinator_monthly_summary(is_billed, year, month);
CREATE INDEX idx_coordinator_monthly_paid ON coordinator_monthly_summary(is_paid, year, month);
```

**Monthly Billing Report** (extracted by 3rd party billing service):
```sql
-- Query for 3rd party biller to pull monthly report
SELECT
    summary_id,
    month_start_date,
    month_end_date,
    coordinator_id,
    coordinator_name,
    patient_id,
    patient_name,
    total_tasks,
    total_duration_minutes,
    billing_code,
    billing_code_description
FROM coordinator_monthly_summary
WHERE year = ? 
  AND month = ?
  AND is_billed = TRUE
  AND is_invoiced = FALSE  -- Not yet invoiced
ORDER BY coordinator_id, patient_id
```

---

### WORKFLOW 3: Provider Payroll (Weekly Internal Payment)

**Purpose:** Track provider weekly payroll and payment (future: track amounts and rates)

**Time Period:** Weekly (Monday-Sunday)

**Table:** `provider_weekly_payroll_status` (aggregated by provider + visit type + week)

**Schema:**
```sql
CREATE TABLE provider_weekly_payroll_status (
    -- Identity
    payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Provider Reference
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    
    -- Week Information
    pay_week_start_date DATE NOT NULL,
    pay_week_end_date DATE NOT NULL,
    pay_week_number INTEGER NOT NULL,
    pay_year INTEGER NOT NULL,
    
    -- Visit Type (different pay rates per type - future feature)
    visit_type TEXT NOT NULL,               -- "Home Visit", "Telehealth", "Office", etc.
    
    -- Aggregated Task Data
    task_count INTEGER DEFAULT 0,
    total_minutes_of_service INTEGER DEFAULT 0,
    
    -- Payment Calculation (placeholder for future)
    -- Will store hourly_rate and total_payroll_amount when implemented
    hourly_rate DECIMAL(10,2),              -- NULL for now, will populate in Phase 2
    total_payroll_amount DECIMAL(12,2),     -- NULL for now, will populate in Phase 2
    
    -- Payroll Workflow (SIMPLE: just approve and pay)
    payroll_status TEXT DEFAULT 'Pending',  -- Pending, Approved, Paid, Held
    
    is_approved BOOLEAN DEFAULT FALSE,
    approved_date DATETIME,
    approved_by TEXT,                       -- user_id who approved (must be Justin)
    
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATETIME,
    paid_by TEXT,                           -- user_id who processed payment (must be Justin)
    payment_method TEXT,                    -- "ACH", "Check", "Direct Deposit" (future)
    payment_reference TEXT,                 -- Check #, ACH ID, etc. (future)
    
    notes TEXT,
    
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(provider_id, pay_week_start_date, visit_type),
    FOREIGN KEY (provider_id) REFERENCES users(user_id)
);

CREATE INDEX idx_provider_weekly_payroll_week ON provider_weekly_payroll_status(pay_week_number, provider_id);
CREATE INDEX idx_provider_weekly_payroll_status ON provider_weekly_payroll_status(payroll_status);
CREATE INDEX idx_provider_weekly_payroll_approved ON provider_weekly_payroll_status(is_approved, pay_week_number);
CREATE INDEX idx_provider_weekly_payroll_paid ON provider_weekly_payroll_status(is_paid, pay_week_number);
```

**Weekly Payroll Report** (for Justin):
```sql
-- Report for payroll coordinator (Justin) to review and process payment
SELECT
    payroll_id,
    pay_week_start_date,
    pay_week_end_date,
    provider_id,
    provider_name,
    visit_type,
    task_count,
    total_minutes_of_service,
    hourly_rate,                   -- NULL until Phase 2
    total_payroll_amount,          -- NULL until Phase 2
    payroll_status,
    is_approved,
    is_paid
FROM provider_weekly_payroll_status
WHERE pay_week_number = ?
  AND pay_year = ?
ORDER BY provider_name, visit_type
```

---

## Billing Workflow State Machine (Provider & Coordinator - IDENTICAL)

Both provider and coordinator billing follow the same workflow, only differ in time period (weekly vs monthly).

**IMPORTANT NOTE:** Tasks marked "paid by zen" are STILL included in billing. "Paid by zen" is a PAYROLL indicator (provider already compensated), NOT a billing exclusion. All tasks must be billed to Medicare.

```
┌─────────────────────────────────────────────────────────────────┐
│ INITIAL STATE: Task imported to source table                     │
│ provider_tasks_YYYY_MM OR coordinator_tasks                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: PENDING                                                  │
│ Task inserted into workflow table during transform               │
│ - Status: 'Pending'                                              │
│ - All boolean flags: FALSE                                       │
│ - Ready for billing review                                       │
│ - NOTE: paid_by_zen flag is set if "paid by zen" in notes       │
│   (for payroll use only, does NOT affect billing)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: BILLED (is_billed = TRUE)                               │
│ - Harpreet or Justin marks for billing                          │
│ - Status: 'Billed'                                               │
│ - billed_date & billed_by recorded                               │
│ - Ready to send to 3rd party billing service                    │
│ WHO: Harpreet (Admin) or Justin (Superuser)                      │
│ WHERE: Billing dashboard                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: INVOICED (is_invoiced = TRUE)                           │
│ - 3rd party billing service creates invoice/claim                │
│ - Status: 'Invoiced'                                             │
│ - invoiced_date: CURRENT_TIMESTAMP                               │
│ - (Automated by 3rd party service or manual update)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: SUBMITTED (is_claim_submitted = TRUE)                   │
│ - Claim/invoice submitted to Medicare                            │
│ - Status: 'Submitted'                                            │
│ - claim_submitted_date: CURRENT_TIMESTAMP                        │
│ - (Automated by 3rd party service)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: PROCESSED (is_insurance_processed = TRUE)               │
│ - Medicare processed and responded to claim                      │
│ - Status: 'Processed'                                            │
│ - insurance_processed_date: CURRENT_TIMESTAMP                    │
│ - (Automated by 3rd party service or manual)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: APPROVED (is_approved_to_pay = TRUE)                    │
│ - Medicare approved payment                                      │
│ - Status: 'Approved'                                             │
│ - approved_to_pay_date: CURRENT_TIMESTAMP                        │
│ - (Automated by 3rd party service or manual review)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: PAID (is_paid = TRUE)                                   │
│ - Payment received from Medicare                                 │
│ - Status: 'Paid'                                                 │
│ - paid_date: CURRENT_TIMESTAMP                                   │
│ - Revenue cycle complete                                         │
│ WHO: Harpreet or Justin verifies payment received                │
└─────────────────────────────────────────────────────────────────┘

ALTERNATIVE PATHS:

Carried Over:
  - If not processed by period end, mark is_carried_over = TRUE
  - Task remains in next period's report

Corrected:
  - If billing code is wrong, revert to 'Pending'
  - Update billing_code
  - Move back through workflow

Denied:
  - If Medicare denies claim, mark as failed
  - Create new task with corrected information
```

---

## Payroll Workflow State Machine (Provider - SIMPLER)

Provider payroll is separate from billing and has its own simple state machine.

```
┌─────────────────────────────────────────────────────────────────┐
│ INITIAL STATE: Week completed                                    │
│ Tasks recorded in provider_task_billing_status                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGGREGATION: Transform populates provider_weekly_payroll_status   │
│ - SUM(tasks) and SUM(minutes) by provider + visit_type + week    │
│ - Status: 'Pending'                                              │
│ - Rates/amounts: NULL (for Phase 2 implementation)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: PENDING                                                  │
│ - Payroll coordinator (Justin) reviews weekly summary            │
│ - Verifies providers, visit types, task counts                   │
│ - Checks for anomalies                                           │
│ - Ready for approval                                             │
│ WHO: Justin only (Payroll Manager)                               │
│ WHERE: Payroll dashboard                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: APPROVED (is_approved = TRUE)                           │
│ - Status: 'Approved'                                             │
│ - approved_date: CURRENT_TIMESTAMP                               │
│ - approved_by: Justin's user_id                                  │
│ - Ready for payment processing                                   │
│ WHO: Justin only                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: PAID (is_paid = TRUE)                                   │
│ - Status: 'Paid'                                                 │
│ - paid_date: CURRENT_TIMESTAMP                                   │
│ - paid_by: Justin's user_id                                      │
│ - Provider payment complete                                      │
│ WHO: Justin or accounting processes payment                      │
└─────────────────────────────────────────────────────────────────┘

OPTIONAL STATES (Future):

Held:
  - If there's a payroll dispute
  - Status: 'Held'
  - For investigation

NOTES:
- No complex workflow steps like billing has
- Payroll is INDEPENDENT from billing status
- Provider can be paid before insurance pays ZEN (intentional)
- Visit type enables different pay rates per task type (Phase 2)
- Kept simple for weekly processing
- Only Justin can approve and process
```

---

## Data Flow: Import & Transform Process
## Data Transform Process (Detailed)

### Current Broken Flow
```
CSV → provider_tasks_YYYY_MM ✅ (populated)
   → provider_task_billing_status ❌ (stays empty)
   → coordinator_tasks ✅ (populated)
   → coordinator_monthly_summary ❌ (stays empty)
   
Dashboards query raw tables directly ❌
```

### CRITICAL: "Paid by zen" Flag During Transform
When populating workflows from CSV:
- **Parse notes field** for text "paid by zen"
- **Set paid_by_zen = TRUE** in provider_task_billing_status if found
- **Include these tasks in billing** (same as regular tasks)
- **Include these tasks in payroll** with `paid_by_zen_count` tracking (prevent double-payment to provider)
- **Do NOT exclude** based on paid_by_zen status

### Corrected Flow (IMPLEMENTED)

**Step 1: Import Raw Data (Existing)**
```
CSV Data 
  → provider_tasks_YYYY_MM (weekly data, all providers)
  → coordinator_tasks (all coordinator tasks)
  → patients, users, etc. (reference data)
```

**Step 2: Transform - Populate Provider Billing Workflow (NEW)**
```powershell
# For each provider_tasks_YYYY_MM table:
FOR EACH task in provider_tasks_YYYY_MM:
    IF billing_code IS NOT NULL:
        INSERT INTO provider_task_billing_status (
            provider_task_id,
            provider_id, provider_name, patient_name, patient_id,
            task_date, task_description, minutes_of_service,
            billing_code, billing_code_description,
            billing_week = strftime('%W', task_date),
            week_start_date = date(task_date, 'weekday 0', '-6 days'),
            week_end_date = date(task_date, 'weekday 0'),
            billing_status = 'Pending',
            is_billed = FALSE,
            created_date = CURRENT_TIMESTAMP
        )
    ELSE:
        INSERT INTO billing_errors (
            table_name, provider_task_id, error_reason
        ) VALUES ('provider_tasks_YYYY_MM', task.id, 'NULL billing_code')
```

**Step 3: Transform - Populate Coordinator Billing Workflow (NEW)**
```powershell
# For each month in coordinator_tasks:
FOR EACH (coordinator_id, patient_id, month):
    total_minutes = SUM(duration_minutes) 
                    WHERE coordinator_id = ? 
                    AND patient_id = ? 
                    AND MONTH(task_date) = ?
    
    billing_code = ASSIGN_BY_MINUTES(total_minutes)
        # 1-19 min → 99490
        # 20-50 min → 99491
        # 50+ min → 99492
    
    INSERT INTO coordinator_monthly_summary (
        coordinator_id, coordinator_name,
        patient_id, patient_name,
        year, month,
        month_start_date = DATE(year || '-' || month || '-01'),
        month_end_date = LAST_DAY(month),
        total_tasks = COUNT(*),
        total_duration_minutes = SUM(duration_minutes),
        billing_code,
        billing_code_description,
        billing_status = 'Pending',
        is_billed = FALSE,
        created_date = CURRENT_TIMESTAMP
    )
```

**Step 4: Transform - Populate Provider Payroll Aggregation (NEW)**
```powershell
# For each week completed:
FOR EACH (provider_id, week, visit_type):
    SELECT
        COUNT(*) as task_count,
        SUM(minutes_of_service) as total_minutes
    FROM provider_task_billing_status
    WHERE provider_id = ?
    AND billing_week = ?
    AND task_description = ?
    
    INSERT INTO provider_weekly_payroll_status (
        provider_id, provider_name,
        pay_week_start_date,
        pay_week_end_date,
        pay_week_number,
        pay_year,
        visit_type,
        task_count,
        total_minutes_of_service = total_minutes,
        hourly_rate = NULL,                     # Phase 2
        total_payroll_amount = NULL,            # Phase 2
        payroll_status = 'Pending',
        is_approved = FALSE,
        is_paid = FALSE,
        created_date = CURRENT_TIMESTAMP
    )
```

**Step 5: Dashboards Query Workflow Tables (NOT Raw)**
```python
# Weekly Provider Billing Dashboard
SELECT * FROM provider_task_billing_status 
WHERE billing_week = ?

# Monthly Coordinator Billing Dashboard
SELECT * FROM coordinator_monthly_summary 
WHERE year = ? AND month = ?

# Weekly Provider Payroll Dashboard
SELECT * FROM provider_weekly_payroll_status 
WHERE pay_week_number = ? AND pay_year = ?
```

---

## Dashboard Changes Required

### 1. Weekly Provider Billing Dashboard

**File:** `src/dashboards/weekly_provider_billing_dashboard.py`

**Current:** Queries `provider_tasks_YYYY_MM` (raw)  
**New:** Queries `provider_task_billing_status` (workflow)

**New Features:**
```python
# Display workflow status
st.dataframe([
    'provider_name', 'patient_name', 'visit_type',
    'minutes_of_service', 'billing_code',
    'billing_status',           # NEW: Pending/Billed/Invoiced/etc.
    'is_billed', 'is_invoiced', 'is_paid'  # NEW: workflow checkpoints
])

# Add workflow action buttons (ONLY for Harpreet & Justin)
if current_user_id in [HARPREET_ID, JUSTIN_ID]:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mark Selected as Billed"):
            UPDATE provider_task_billing_status
            SET is_billed = TRUE, 
                billing_status = 'Billed', 
                billed_date = NOW,
                billed_by = current_user_id
            WHERE billing_status_id IN (selected_ids)

    with col2:
        if st.button("Export Weekly Report for Biller"):
            # Download CSV of is_billed=TRUE for this week
            # For 3rd party billing service to import

# Filter by status
status_filter = st.selectbox("Filter by Status", 
    ['All', 'Pending', 'Billed', 'Invoiced', 'Submitted', 
     'Processed', 'Approved', 'Paid'])
```

---

### 2. Monthly Coordinator Billing Dashboard

**File:** `src/dashboards/monthly_coordinator_billing_dashboard.py`

**Current:** Doesn't exist  
**New:** Queries `coordinator_monthly_summary` (workflow)

**Features:**
```python
# Display by patient/month with workflow status
st.dataframe([
    'patient_name', 'coordinator_name', 'total_tasks',
    'total_duration_minutes', 'billing_code',
    'billing_status',           # NEW
    'is_billed', 'is_invoiced', 'is_paid'  # NEW
])

# Add workflow action buttons (ONLY for Harpreet & Justin)
if current_user_id in [HARPREET_ID, JUSTIN_ID]:
    if st.button("Mark All as Billed"):
        UPDATE coordinator_monthly_summary
        SET is_billed = TRUE, 
            billing_status = 'Billed', 
            billed_date = NOW,
            billed_by = current_user_id
        WHERE year = ? AND month = ? AND billing_status = 'Pending'

    if st.button("Export Monthly Report for Biller"):
        # Download CSV of is_billed=TRUE for this month
```

---

### 3. Weekly Provider Payroll Dashboard

**File:** `src/dashboards/weekly_provider_payroll_dashboard.py`

**Current:** Queries `provider_tasks_YYYY_MM` (raw)  
**New:** Queries `provider_weekly_payroll_status` (workflow)

**Features:**
```python
# Display aggregated payroll (by provider + visit_type)
st.dataframe([
    'provider_name', 'visit_type', 'task_count',
    'total_minutes_of_service',
    'hourly_rate',              # NULL until Phase 2
    'total_payroll_amount',     # NULL until Phase 2
    'payroll_status'            # NEW: Pending/Approved/Paid
])

# Add workflow action buttons (ONLY for Justin)
if current_user_id == JUSTIN_ID:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Approve Selected Payroll"):
            UPDATE provider_weekly_payroll_status
            SET is_approved = TRUE, 
                payroll_status = 'Approved', 
                approved_date = NOW,
                approved_by = current_user_id
            WHERE payroll_id IN (selected_ids)

    with col2:
        if st.button("Mark as Paid"):
            UPDATE provider_weekly_payroll_status
            SET is_paid = TRUE, 
                payroll_status = 'Paid', 
                paid_date = NOW,
                paid_by = current_user_id
            WHERE payroll_id IN (selected_ids)

# Show payment history
st.subheader("Payment History (Last 12 Weeks)")
payment_history = get_provider_payment_history(provider_id, num_weeks=12)
st.dataframe(payment_history)
```

**Filter:**
```python
# Only show for Justin
if current_user_id != JUSTIN_ID:
    st.error("Only Justin can access the Payroll Dashboard")
    return
```

---

## Database Schema Changes

### New Tables
```sql
CREATE TABLE provider_weekly_payroll_status (
    payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    pay_week_start_date DATE NOT NULL,
    pay_week_end_date DATE NOT NULL,
    pay_week_number INTEGER NOT NULL,
    pay_year INTEGER NOT NULL,
    visit_type TEXT NOT NULL,
    task_count INTEGER DEFAULT 0,
    total_minutes_of_service INTEGER DEFAULT 0,
    hourly_rate DECIMAL(10,2),
    total_payroll_amount DECIMAL(12,2),
    payroll_status TEXT DEFAULT 'Pending',
    is_approved BOOLEAN DEFAULT FALSE,
    approved_date DATETIME,
    approved_by TEXT,
    is_paid BOOLEAN DEFAULT FALSE,
    paid_date DATETIME,
    paid_by TEXT,
    payment_method TEXT,
    payment_reference TEXT,
    notes TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, pay_week_start_date, visit_type),
    FOREIGN KEY (provider_id) REFERENCES users(user_id)
);

CREATE INDEX idx_provider_weekly_payroll_week ON provider_weekly_payroll_status(pay_week_number, provider_id);
CREATE INDEX idx_provider_weekly_payroll_status ON provider_weekly_payroll_status(payroll_status);
CREATE INDEX idx_provider_weekly_payroll_approved ON provider_weekly_payroll_status(is_approved, pay_week_number);
CREATE INDEX idx_provider_weekly_payroll_paid ON provider_weekly_payroll_status(is_paid, pay_week_number);
```

### Modify Existing Tables
```sql
-- Add audit columns to provider_task_billing_status
ALTER TABLE provider_task_billing_status ADD COLUMN billed_by TEXT;
ALTER TABLE provider_task_billing_status ADD COLUMN invoiced_date DATETIME;
ALTER TABLE provider_task_billing_status ADD COLUMN claim_submitted_date DATETIME;
ALTER TABLE provider_task_billing_status ADD COLUMN insurance_processed_date DATETIME;
ALTER TABLE provider_task_billing_status ADD COLUMN approved_to_pay_date DATETIME;

-- Add audit columns to coordinator_monthly_summary
ALTER TABLE coordinator_monthly_summary ADD COLUMN month_start_date DATE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN month_end_date DATE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN billed_by TEXT;
ALTER TABLE coordinator_monthly_summary ADD COLUMN invoiced_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN claim_submitted_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN insurance_processed_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN approved_to_pay_date DATETIME;
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Create `provider_weekly_payroll_status` table
- [ ] Add audit columns to `provider_task_billing_status` & `coordinator_monthly_summary`
- [ ] Create indexes for performance
- [ ] Create transform script to populate all three workflows
- [ ] Set up user role checks for Harpreet/Justin (billing) and Justin-only (payroll)

### Phase 2: Historical Data Population (Week 1)
- [ ] Run transform script on all existing provider_tasks_YYYY_MM data
- [ ] Run transform script on all existing coordinator_tasks data
- [ ] Verify row counts match source tables
- [ ] Spot-check data accuracy

### Phase 3: Dashboard Migration (Week 2)
- [ ] Rewrite weekly provider billing dashboard to query workflow table
- [ ] Create monthly coordinator billing dashboard to query workflow table
- [ ] Rewrite weekly provider payroll dashboard to query workflow table
- [ ] Add workflow status action buttons with role checks
- [ ] Add filtering by status/payment
- [ ] Add exports for 3rd party billing service

### Phase 4: Integration & Testing (Week 3)
- [ ] Test end-to-end data flow from import to dashboard
- [ ] Test workflow state transitions
- [ ] Verify timestamps recorded correctly
- [ ] Test export/report functionality
- [ ] Verify role-based access control works
- [ ] Load testing with concurrent users

### Phase 5: Production Cutover (Week 4)
- [ ] Update import scripts to populate workflows automatically
- [ ] Deploy new dashboards
- [ ] Train Harpreet on billing workflow UI
- [ ] Train Justin on payroll approval UI
- [ ] Monitor data integrity in first week

---

## Access Control Matrix

| Role | Provider Billing | Coordinator Billing | Payroll |
|------|-----------------|-------------------|---------|
| **Harpreet (Admin)** | ✅ View & Edit | ✅ View & Edit | ❌ View Only |
| **Justin (Superuser)** | ✅ View & Edit | ✅ View & Edit | ✅ View & Edit |
| **3rd Party Biller** | ⏳ Future | ⏳ Future | ❌ No Access |
| **Providers** | ❌ No Access | N/A | ✅ View Only (self) |
| **Coordinators** | ❌ No Access | ✅ View Only (self) | N/A |

---

## Future Implementation (Phase 2)

The following are designed into the schema but NOT implemented now:

1. **Payroll Rates & Amounts**
   - `hourly_rate` column exists in `provider_weekly_payroll_status`
   - `total_payroll_amount` column exists
   - When ready: populate from visit_type_rates table
   - Calculate as: (total_minutes_of_service / 60) * hourly_rate

2. **Payment Methods & References**
   - `payment_method` column exists (ACH, Check, Direct Deposit)
   - `payment_reference` column exists (Check #, ACH ID)
   - When ready: implement payment processing integration

3. **3rd Party Biller Integration**
   - Separate user role for 3rd party billing service
   - API access to pull billing reports
   - Webhook notifications for workflow updates
   - Currently: Harpreet/Justin manage manually

---

## Success Criteria

✅ All provider tasks in `provider_task_billing_status` (100% coverage)  
✅ All coordinator tasks in `coordinator_monthly_summary` (100% coverage)  
✅ All provider weeks in `provider_weekly_payroll_status` (100% coverage)  
✅ Billing dashboards show workflow status accurately  
✅ Payroll dashboard shows aggregation by visit type  
✅ Workflow state transitions recorded with timestamps  
✅ Can trace any task from Pending → Paid  
✅ Reports export correctly for 3rd party billing service  
✅ Role-based access control enforced (Harpreet/Justin for billing, Justin-only for payroll)  
✅ Dashboard load time < 2 seconds  

---

## Summary

**The fix is comprehensive but straightforward:**

1. **Three separate workflow tables** for three separate processes
2. **Transform script populates workflows** during import (not dashboards)
3. **Dashboards query workflows** (not raw tasks)
4. **Audit trail** with timestamps for compliance
5. **Role-based access control** (Harpreet/Justin for billing, Justin-only for payroll)
6. **Future-ready** for payment tracking and 3rd party integration

**Result:** Complete visibility and control over billing and payroll, ensuring compliance, proper role separation, and timely payment.

---

## CRITICAL REFERENCE: Billing vs Payroll Separation

**See dedicated document:** `BILLING_VS_PAYROLL_SEPARATION.md`

Key points (do not forget):
- Billing and Payroll are TWO separate financial workflows
- Both operate on the SAME 20,396 tasks
- "Paid by zen" = Provider was already compensated (payroll issue)
- "Paid by zen" ≠ Task shouldn't be billed to Medicare (NOT a billing issue)
- 3rd party biller NEVER sees "paid by zen" info (internal only)
- Justin MUST see "paid by zen" counts to prevent double-payment
- ALL tasks included in both billing AND payroll workflows