# Billing & Payroll Workflow Implementation Plan

**Status:** Ready for Implementation  
**Date:** January 2025  
**Priority:** P0

---

## Current State Analysis

### What Exists in Database

#### Provider Billing
- ✅ `provider_tasks_YYYY_MM` tables (47 months, 5000+ tasks)
  - Columns: provider_id, provider_name, patient_id, patient_name, task_date, task_description, minutes_of_service, billing_code, billing_code_description
  - Data populated from PSL_ZEN-*.csv files

- ✅ `provider_task_billing_status` table (exists but schema incomplete)
  - Currently populated by `populate_provider_billing_status()` function in transform script
  - Has core columns: provider_task_id, provider_id, provider_name, patient_name, task_date, task_description, minutes_of_service, billing_code, billing_status, is_billed, is_invoiced, is_claim_submitted, is_insurance_processed, is_approved_to_pay, is_paid
  - Missing audit columns: billed_by, invoiced_date, claim_submitted_date, insurance_processed_date, approved_to_pay_date, paid_date

#### Coordinator Billing
- ✅ `coordinator_tasks_YYYY_MM` tables (15 months, 81,000+ tasks)
  - Columns: coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes
  - Data populated from CMLog_*.csv files

- ✅ `coordinator_monthly_summary` table (57 records, but missing workflow columns)
  - Current columns: summary_id, coordinator_id, coordinator_name, year, month, month_start_date, month_end_date, total_tasks_completed, total_time_spent_minutes, created_date, updated_date
  - Missing: patient_id, patient_name, billing_code, billing_code_description, billing_status, is_billed, is_invoiced, is_claim_submitted, is_insurance_processed, is_approved_to_pay, is_paid, billed_by

#### Provider Payroll
- ❌ `provider_weekly_payroll_status` table (does NOT exist, needs creation)

#### Supporting Tables
- ✅ `task_billing_codes` - Billing code definitions
- ✅ `coordinator_billing_codes` - Coordinator billing codes
- ✅ Users and provider/coordinator mappings

---

## Implementation Phases

### PHASE 1: Schema Enhancement (Week 1)

**Objective:** Create missing table and add missing audit columns

#### 1.1 Add Audit Columns to provider_task_billing_status

```sql
ALTER TABLE provider_task_billing_status ADD COLUMN billed_by TEXT;
ALTER TABLE provider_task_billing_status ADD COLUMN invoiced_date DATETIME;
ALTER TABLE provider_task_billing_status ADD COLUMN claim_submitted_date DATETIME;
ALTER TABLE provider_task_billing_status ADD COLUMN insurance_processed_date DATETIME;
ALTER TABLE provider_task_billing_status ADD COLUMN approved_to_pay_date DATETIME;
ALTER TABLE provider_task_billing_status ADD COLUMN paid_date DATETIME;

-- Backfill billed_date for existing records that are already marked as billed
UPDATE provider_task_billing_status 
SET billed_by = 'system_import' 
WHERE is_billed = TRUE AND billed_by IS NULL;
```

#### 1.2 Enhance coordinator_monthly_summary

```sql
-- Drop and recreate to add missing columns
ALTER TABLE coordinator_monthly_summary ADD COLUMN patient_id TEXT;
ALTER TABLE coordinator_monthly_summary ADD COLUMN patient_name TEXT;
ALTER TABLE coordinator_monthly_summary ADD COLUMN billing_code TEXT;
ALTER TABLE coordinator_monthly_summary ADD COLUMN billing_code_description TEXT;
ALTER TABLE coordinator_monthly_summary ADD COLUMN billing_status TEXT DEFAULT 'Pending';
ALTER TABLE coordinator_monthly_summary ADD COLUMN is_billed BOOLEAN DEFAULT FALSE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN billed_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN billed_by TEXT;
ALTER TABLE coordinator_monthly_summary ADD COLUMN is_invoiced BOOLEAN DEFAULT FALSE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN invoiced_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN is_claim_submitted BOOLEAN DEFAULT FALSE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN claim_submitted_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN is_insurance_processed BOOLEAN DEFAULT FALSE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN insurance_processed_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN is_approved_to_pay BOOLEAN DEFAULT FALSE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN approved_to_pay_date DATETIME;
ALTER TABLE coordinator_monthly_summary ADD COLUMN is_paid BOOLEAN DEFAULT FALSE;
ALTER TABLE coordinator_monthly_summary ADD COLUMN paid_date DATETIME;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_coordinator_monthly_billed ON coordinator_monthly_summary(is_billed, year, month);
CREATE INDEX IF NOT EXISTS idx_coordinator_monthly_status ON coordinator_monthly_summary(billing_status);
```

#### 1.3 Create provider_weekly_payroll_status Table

```sql
CREATE TABLE IF NOT EXISTS provider_weekly_payroll_status (
    payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Provider Reference
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    
    -- Week Information
    pay_week_start_date DATE NOT NULL,
    pay_week_end_date DATE NOT NULL,
    pay_week_number INTEGER NOT NULL,
    pay_year INTEGER NOT NULL,
    
    -- Visit Type (different pay rates per type - future)
    visit_type TEXT NOT NULL,
    
    -- Aggregated Task Data
    task_count INTEGER DEFAULT 0,
    total_minutes_of_service INTEGER DEFAULT 0,
    
    -- Payment Calculation (placeholder for future Phase 2)
    hourly_rate DECIMAL(10,2),
    total_payroll_amount DECIMAL(12,2),
    
    -- Payroll Workflow
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_provider_weekly_payroll_week ON provider_weekly_payroll_status(pay_week_number, provider_id);
CREATE INDEX IF NOT EXISTS idx_provider_weekly_payroll_status ON provider_weekly_payroll_status(payroll_status);
CREATE INDEX IF NOT EXISTS idx_provider_weekly_payroll_approved ON provider_weekly_payroll_status(is_approved, pay_week_number);
CREATE INDEX IF NOT EXISTS idx_provider_weekly_payroll_paid ON provider_weekly_payroll_status(is_paid, pay_week_number);
```

---

### PHASE 2: Transform Script Enhancement (Week 1)

**Objective:** Update transform_production_data_v3_fixed.py to populate all three workflow tables

#### 2.1 Enhance populate_provider_billing_status()

The existing function already populates provider_task_billing_status. It needs:
- Add `patient_id` column extraction (currently missing)
- Add logic to handle NULL billing codes (create error log)

```python
def populate_provider_billing_status(conn, year, month):
    """Populate provider_task_billing_status from provider_tasks_YYYY_MM"""
    try:
        provider_table = f"provider_tasks_{year}_{str(month).zfill(2)}"
        billing_status_table = "provider_task_billing_status"
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (provider_table,))
        if not cursor.fetchone():
            print(f"  Provider table {provider_table} does not exist, skipping")
            return 0
        
        print(f"  Populating billing status from {provider_table}...")
        
        # Log tasks with missing billing codes
        cursor.execute(f"""
            SELECT COUNT(*) FROM {provider_table} 
            WHERE (billing_code IS NULL OR billing_code = '' OR billing_code = 'PENDING')
                AND minutes_of_service > 0
        """)
        missing_codes_count = cursor.fetchone()[0]
        if missing_codes_count > 0:
            print(f"    WARNING: {missing_codes_count} tasks have missing/pending billing codes")
        
        # Insert billing status records
        cursor.execute(f"""
            INSERT OR IGNORE INTO {billing_status_table} (
                provider_task_id, provider_id, provider_name, patient_name,
                task_date, billing_week, week_start_date, week_end_date,
                task_description, minutes_of_service, billing_code,
                billing_code_description, billing_status, is_billed,
                created_date, billed_by
            )
            SELECT pt.provider_task_id, pt.provider_id, pt.provider_name,
                pt.patient_name, pt.task_date,
                CAST(strftime('%W', pt.task_date) AS INTEGER) as billing_week,
                DATE(pt.task_date, 'weekday 0', '-6 days') as week_start_date,
                DATE(pt.task_date, 'weekday 0') as week_end_date,
                pt.task_description, pt.minutes_of_service, pt.billing_code,
                COALESCE(tbc.description, 'Unknown') as billing_code_description,
                'Pending' as billing_status, FALSE as is_billed,
                CURRENT_TIMESTAMP as created_date,
                'system_import' as billed_by
            FROM {provider_table} pt
            LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
            WHERE pt.billing_code IS NOT NULL
                AND pt.billing_code NOT IN ('Not_Billable', '', 'PENDING', 'nan')
                AND pt.minutes_of_service > 0
        """)
        
        inserted_count = cursor.rowcount
        return inserted_count
        
    except Exception as e:
        print(f"  Error populating billing status: {e}")
        return 0
```

#### 2.2 NEW: Populate Coordinator Monthly Summary from coordinator_tasks

```python
def populate_coordinator_monthly_summary(conn, year, month):
    """Populate coordinator_monthly_summary from coordinator_tasks_YYYY_MM"""
    try:
        coord_table = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
        summary_table = "coordinator_monthly_summary"
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (coord_table,))
        if not cursor.fetchone():
            print(f"  Coordinator table {coord_table} does not exist, skipping")
            return 0
        
        print(f"  Populating coordinator monthly summary from {coord_table}...")
        
        # Check if records already exist for this month
        cursor.execute(f"""
            SELECT COUNT(*) FROM {summary_table}
            WHERE year = ? AND month = ?
        """, (year, month))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"    Clearing {existing_count} existing records for {year}-{month:02d}")
            cursor.execute(f"""
                DELETE FROM {summary_table}
                WHERE year = ? AND month = ?
            """, (year, month))
        
        # Aggregate coordinator tasks by patient/month
        cursor.execute(f"""
            INSERT INTO {summary_table} (
                coordinator_id, coordinator_name, patient_id, patient_name,
                year, month, month_start_date, month_end_date,
                total_tasks_completed, total_time_spent_minutes,
                billing_code, billing_code_description,
                billing_status, is_billed, billed_by,
                created_date, updated_date
            )
            SELECT
                ct.coordinator_id,
                ct.coordinator_name,
                ct.patient_id,
                ct.patient_id as patient_name,  -- Using patient_id as name for now
                ? as year,
                ? as month,
                DATE(? || '-' || PRINTF('%02d', ?) || '-01') as month_start_date,
                DATE(? || '-' || PRINTF('%02d', ?) || '-01', '+1 month', '-1 day') as month_end_date,
                COUNT(*) as total_tasks_completed,
                CAST(SUM(ct.duration_minutes) AS INTEGER) as total_time_spent_minutes,
                CASE
                    WHEN SUM(ct.duration_minutes) >= 50 THEN '99492'
                    WHEN SUM(ct.duration_minutes) >= 20 THEN '99491'
                    ELSE '99490'
                END as billing_code,
                CASE
                    WHEN SUM(ct.duration_minutes) >= 50 THEN 'Care Management - Complex'
                    WHEN SUM(ct.duration_minutes) >= 20 THEN 'Care Management - Moderate'
                    ELSE 'Care Management - Basic'
                END as billing_code_description,
                'Pending' as billing_status,
                FALSE as is_billed,
                NULL as billed_by,
                CURRENT_TIMESTAMP as created_date,
                CURRENT_TIMESTAMP as updated_date
            FROM {coord_table} ct
            WHERE ct.coordinator_id IS NOT NULL
                AND ct.patient_id IS NOT NULL
                AND TRIM(ct.patient_id) != ''
                AND ct.duration_minutes > 0
            GROUP BY ct.coordinator_id, ct.coordinator_name, ct.patient_id
        """, (year, month, year, month, year, month))
        
        inserted_count = cursor.rowcount
        print(f"    Inserted/updated {inserted_count} coordinator billing records")
        
        return inserted_count
        
    except Exception as e:
        print(f"  Error populating coordinator monthly summary: {e}")
        return 0
```

#### 2.3 NEW: Populate Provider Weekly Payroll from provider_task_billing_status

```python
def populate_provider_weekly_payroll(conn, year, month):
    """Populate provider_weekly_payroll_status from provider_task_billing_status"""
    try:
        payroll_table = "provider_weekly_payroll_status"
        
        cursor = conn.cursor()
        
        print(f"  Populating provider weekly payroll for {year}-{month:02d}...")
        
        # Aggregate provider tasks by week and visit type
        cursor.execute(f"""
            INSERT OR IGNORE INTO {payroll_table} (
                provider_id, provider_name,
                pay_week_start_date, pay_week_end_date,
                pay_week_number, pay_year, visit_type,
                task_count, total_minutes_of_service,
                payroll_status, created_date
            )
            SELECT
                ptbs.provider_id,
                ptbs.provider_name,
                ptbs.week_start_date,
                ptbs.week_end_date,
                ptbs.billing_week,
                CAST(strftime('%Y', ptbs.task_date) AS INTEGER),
                ptbs.task_description as visit_type,
                COUNT(*) as task_count,
                SUM(ptbs.minutes_of_service) as total_minutes,
                'Pending' as payroll_status,
                CURRENT_TIMESTAMP as created_date
            FROM provider_task_billing_status ptbs
            WHERE CAST(strftime('%Y', ptbs.task_date) AS INTEGER) = ?
                AND CAST(strftime('%m', ptbs.task_date) AS INTEGER) = ?
                AND ptbs.provider_id IS NOT NULL
                AND ptbs.minutes_of_service > 0
            GROUP BY ptbs.provider_id, ptbs.provider_name,
                ptbs.week_start_date, ptbs.week_end_date,
                ptbs.task_description
        """, (year, month))
        
        inserted_count = cursor.rowcount
        print(f"    Inserted {inserted_count} payroll records")
        
        return inserted_count
        
    except Exception as e:
        print(f"  Error populating payroll: {e}")
        return 0
```

#### 2.4 Update main() to Call New Functions

Add to main() after STEP 4:

```python
# STEP 5: Populate coordinator monthly summary
print("\n" + "=" * 60)
print("STEP 5: Populating Coordinator Monthly Summary")
print("=" * 60)

cursor = conn.cursor()
cursor.execute("""
    SELECT DISTINCT substr(name, 19, 4) as year_month
    FROM sqlite_master 
    WHERE type='table' 
    AND name LIKE 'coordinator_tasks_20%'
    ORDER BY year_month DESC
""")

processed_coord_months = cursor.fetchall()
total_coordinator_summary = 0

for (year_month,) in processed_coord_months:
    try:
        if not year_month or len(year_month) != 6:
            continue
        year = int(year_month[:4])
        month = int(year_month[4:6])
        if month < 1 or month > 12:
            continue
        print(f"  Processing {calendar.month_name[month]} {year}...")
        summary_count = populate_coordinator_monthly_summary(conn, year, month)
        total_coordinator_summary += summary_count
    except (ValueError, IndexError) as e:
        print(f"  Warning: Skipping invalid year_month: {year_month}")
        continue

if total_coordinator_summary > 0:
    print(f"  Total coordinator summary records: {total_coordinator_summary}")

# STEP 6: Populate provider weekly payroll
print("\n" + "=" * 60)
print("STEP 6: Populating Provider Weekly Payroll")
print("=" * 60)

total_payroll_records = 0

for (year_month,) in processed_months:
    try:
        if not year_month or len(year_month) != 6:
            continue
        year = int(year_month[:4])
        month = int(year_month[4:6])
        if month < 1 or month > 12:
            continue
        print(f"  Processing {calendar.month_name[month]} {year}...")
        payroll_count = populate_provider_weekly_payroll(conn, year, month)
        total_payroll_records += payroll_count
    except (ValueError, IndexError) as e:
        print(f"  Warning: Skipping invalid year_month: {year_month}")
        continue

if total_payroll_records > 0:
    print(f"  Total payroll records created: {total_payroll_records}")
```

Update final summary output:

```python
print(f"  Coordinator Billing Summary: {total_coordinator_summary}")
print(f"  Payroll Status Records:      {total_payroll_records}")
print(f"  Total Records: {total_assignments + total_patients + total_psl + total_rvz + total_billing_records + total_coordinator_summary + total_payroll_records}")
```

---

### PHASE 3: Dashboard Updates (Week 2)

#### 3.1 Weekly Provider Billing Dashboard

**File:** `src/dashboards/weekly_provider_billing_dashboard.py`

**Changes:**
1. Change query source from `provider_tasks_YYYY_MM` to `provider_task_billing_status`
2. Add workflow status display columns
3. Add "Mark as Billed" button (Justin/Harpreet only)
4. Add filtering by workflow status
5. Add export functionality for 3rd party biller

**Key Query:**
```python
def get_provider_billing_data(year, month, week_key=None):
    query = """
    SELECT
        ptbs.billing_status_id,
        ptbs.provider_id,
        ptbs.provider_name,
        ptbs.patient_name,
        ptbs.task_date,
        ptbs.task_description,
        ptbs.minutes_of_service,
        ptbs.billing_code,
        ptbs.billing_status,
        ptbs.is_billed,
        ptbs.is_invoiced,
        ptbs.is_paid,
        ptbs.billed_by,
        ptbs.billed_date
    FROM provider_task_billing_status ptbs
    WHERE ptbs.billing_week = ?
        AND CAST(strftime('%Y', ptbs.task_date) AS INTEGER) = ?
        AND CAST(strftime('%m', ptbs.task_date) AS INTEGER) = ?
    ORDER BY ptbs.provider_name, ptbs.task_date
    """
    # Execute and return
```

**Action Buttons:**
```python
# Only Justin (user_id=1) and Harpreet (user_id=2) can update
allowed_users = [1, 2]

if st.session_state['user_id'] in allowed_users:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Mark Selected as Billed"):
            # UPDATE provider_task_billing_status
            # SET is_billed = TRUE, billing_status = 'Billed',
            #     billed_date = NOW, billed_by = current_user
```

#### 3.2 Monthly Coordinator Billing Dashboard

**File:** `src/dashboards/monthly_coordinator_billing_dashboard.py` (NEW or rewrite)

**Purpose:** Display coordinator work by patient with billing workflow tracking

**Key Query:**
```python
def get_coordinator_billing_data(year, month):
    query = """
    SELECT
        cms.summary_id,
        cms.coordinator_id,
        cms.coordinator_name,
        cms.patient_id,
        cms.patient_name,
        cms.total_tasks_completed,
        cms.total_time_spent_minutes,
        cms.billing_code,
        cms.billing_code_description,
        cms.billing_status,
        cms.is_billed,
        cms.billed_by,
        cms.billed_date
    FROM coordinator_monthly_summary cms
    WHERE cms.year = ?
        AND cms.month = ?
    ORDER BY cms.coordinator_name, cms.patient_id
    """
```

**Action Buttons:**
```python
# Only Justin and Harpreet can update
if st.session_state['user_id'] in [1, 2]:
    if st.button("Mark All as Billed"):
        # UPDATE coordinator_monthly_summary
        # SET is_billed = TRUE, billing_status = 'Billed',
        #     billed_date = NOW, billed_by = current_user
```

#### 3.3 Weekly Provider Payroll Dashboard

**File:** `src/dashboards/weekly_provider_payroll_dashboard.py` (rewrite)

**Purpose:** Display provider payroll by visit type with approval workflow

**Key Query:**
```python
def get_provider_payroll_data(week_start_date):
    query = """
    SELECT
        pwps.payroll_id,
        pwps.provider_id,
        pwps.provider_name,
        pwps.visit_type,
        pwps.task_count,
        pwps.total_minutes_of_service,
        pwps.hourly_rate,
        pwps.total_payroll_amount,
        pwps.payroll_status,
        pwps.is_approved,
        pwps.is_paid,
        pwps.approved_by,
        pwps.paid_date
    FROM provider_weekly_payroll_status pwps
    WHERE pwps.pay_week_start_date = ?
    ORDER BY pwps.provider_name, pwps.visit_type
    """
```

**Action Buttons (JUSTIN ONLY):**
```python
# ONLY Justin (user_id=1) can approve and pay
if st.session_state['user_id'] != 1:
    st.error("Only Justin can access payroll approval")
    # Show view-only dashboard
    display_payroll_view_only()
    return

# Show interactive dashboard
col1, col2 = st.columns(2)

with col1:
    if st.button("Approve Selected"):
        # UPDATE provider_weekly_payroll_status
        # SET is_approved = TRUE, payroll_status = 'Approved',
        #     approved_date = NOW, approved_by = 1

with col2:
    if st.button("Mark as Paid"):
        # UPDATE provider_weekly_payroll_status
        # SET is_paid = TRUE, payroll_status = 'Paid',
        #     paid_date = NOW, paid_by = 1
```

---

### PHASE 4: Database Functions (Week 2)

Update `src/database.py` to add workflow update functions:

```python
def mark_provider_tasks_as_billed(billing_status_ids, user_id):
    """Mark provider tasks as billed"""
    conn = get_db_connection()
    try:
        placeholders = ','.join('?' * len(billing_status_ids))
        conn.execute(f"""
            UPDATE provider_task_billing_status
            SET is_billed = TRUE,
                billing_status = 'Billed',
                billed_date = CURRENT_TIMESTAMP,
                billed_by = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE billing_status_id IN ({placeholders})
                AND is_billed = FALSE
        """, [user_id] + billing_status_ids)
        conn.commit()
        return conn.total_changes
    finally:
        conn.close()

def mark_coordinator_tasks_as_billed(summary_ids, user_id):
    """Mark coordinator tasks as billed"""
    conn = get_db_connection()
    try:
        placeholders = ','.join('?' * len(summary_ids))
        conn.execute(f"""
            UPDATE coordinator_monthly_summary
            SET is_billed = TRUE,
                billing_status = 'Billed',
                billed_date = CURRENT_TIMESTAMP,
                billed_by = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE summary_id IN ({placeholders})
                AND is_billed = FALSE
        """, [user_id] + summary_ids)
        conn.commit()
        return conn.total_changes
    finally:
        conn.close()

def approve_provider_payroll(payroll_ids, user_id):
    """Approve provider payroll (Justin only)"""
    conn = get_db_connection()
    try:
        placeholders = ','.join('?' * len(payroll_ids))
        conn.execute(f"""
            UPDATE provider_weekly_payroll_status
            SET is_approved = TRUE,
                payroll_status = 'Approved',
                approved_date = CURRENT_TIMESTAMP,
                approved_by = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE payroll_id IN ({placeholders})
                AND is_approved = FALSE
        """, [user_id] + payroll_ids)
        conn.commit()
        return conn.total_changes
    finally:
        conn.close()

def mark_provider_payroll_as_paid(payroll_ids, user_id):
    """Mark provider payroll as paid (Justin only)"""
    conn = get_db_connection()
    try:
        placeholders = ','.join('?' * len(payroll_ids))
        conn.execute(f"""
            UPDATE provider_weekly_payroll_status
            SET is_paid = TRUE,
                payroll_status = 'Paid',
                paid_date = CURRENT_TIMESTAMP,
                paid_by = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE payroll_id IN ({placeholders})
                AND is_paid = FALSE
        """, [user_id] + payroll_ids)
        conn.commit()
        return conn.total_changes
    finally:
        conn.close()
```

---

## Implementation Checklist

### Phase 1: Schema (Week 1)
- [ ] Add audit columns to provider_task_billing_status
- [ ] Add patient_id and workflow columns to coordinator_monthly_summary
- [ ] Create provider_weekly_payroll_status table
- [ ] Create indexes for performance
- [ ] Verify schema changes completed

### Phase 2: Transform Script (Week 1)
- [ ] Add populate_coordinator_monthly_summary() function
- [ ] Add populate_provider_weekly_payroll() function
- [ ] Enhance populate_provider_billing_status() with patient_id
- [ ] Update main() to call new functions
- [ ] Test with sample data
- [ ] Run on all historical data

### Phase 3: Dashboards (Week 2)
- [ ] Rewrite weekly_provider_billing_dashboard.py
- [ ] Create monthly_coordinator_billing_dashboard.py
- [ ] Rewrite weekly_provider_payroll_dashboard.py
- [ ] Add role-based access control
- [ ] Add workflow action buttons
- [ ] Test with real data

### Phase 4: Database Functions (Week 2)
- [ ] Add mark_provider_tasks_as_billed() to src/database.py
- [ ] Add mark_coordinator_tasks_as_billed() to src/database.py
- [ ] Add approve_provider_payroll() to src/database.py
- [ ] Add mark_provider_payroll_as_paid() to src/database.py
- [ ] Test all functions

### Phase 5: Testing & Validation (Week 3)
- [ ] End-to-end data flow test
- [ ] Workflow state transition test
- [ ] Role-based access control test
- [ ] Export functionality test
- [ ] Performance test (load time < 2 seconds)
- [ ] Data integrity validation

### Phase 6: Deployment (Week 4)
- [ ] Backup production database
- [ ] Run schema migration
- [ ] Run transform script on all data
- [ ] Verify data counts match source
- [ ] Deploy new dashboards
- [ ] Train Justin on payroll workflow
- [ ] Train Harpreet on billing workflow
- [ ] Monitor for issues

---

## Data Mapping Reference

### Provider Billing Data Flow
```
CSV (PSL_ZEN-*.csv)
  ↓
provider_tasks_YYYY_MM (CREATE TABLE + INSERT)
  ↓
provider_task_billing_status (populate_provider_billing_status)
  ↓
Weekly Provider Billing Dashboard (query + display + update)
```

### Coordinator Billing Data Flow
```
CSV (CMLog_*.csv)
  ↓
coordinator_tasks_YYYY_MM (CREATE TABLE + INSERT)
  ↓
coordinator_monthly_summary (populate_coordinator_monthly_summary)
  ↓
Monthly Coordinator Billing Dashboard (query + display + update)
```

### Provider Payroll Data Flow
```
provider_task_billing_status (aggregated)
  ↓
provider_weekly_payroll_status (populate_provider_weekly_payroll)
  ↓
Weekly Provider Payroll Dashboard (query + display + approve + pay)
```

---

## Access Control Requirements

### Provider Billing (provider_task_billing_status)
- **Can Mark as Billed:** Justin (user_id=1), Harpreet (user_id=2)
- **Can View:** All users with appropriate role
- **Can Update Other States:** 3rd Party Biller (future - via API)

### Coordinator Billing (coordinator_monthly_summary)
- **Can Mark as Billed:** Justin (user_id=1), Harpreet (user_id=2)
- **Can View:** Coordinators (own records), Harpreet, Justin
- **Can Update Other States:** 3rd Party Biller (future - via API)

### Provider Payroll (provider_weekly_payroll_status)
- **Can Approve:** Justin ONLY (user_id=1)
- **Can Mark as Paid:** Justin ONLY (user_id=1)
- **Can View:** Harpreet (all), Justin (all), Providers (own only)

---

## Success Criteria

✅ All provider tasks in provider_task_billing_status (100% coverage from provider_tasks_YYYY_MM)  
✅ All coordinator months in coordinator_monthly_summary with workflow columns  
✅ All provider weeks in provider_weekly_payroll_status with task aggregation  
✅ Dashboards query workflow tables (not raw tasks)  
✅ Workflow state transitions recorded with timestamps  
✅ Role-based access control enforced  
✅ Dashboard load time < 2 seconds  
✅ Exports work correctly for 3rd party biller  

---

## Future Enhancements (Phase 2+)

- [ ] Populate hourly_rate and total_payroll_amount in provider_weekly_payroll_status
- [ ] Create visit_type_rates configuration table
- [ ] Implement 3rd party biller integration (API, webhooks)
- [ ] Add provider payment tracking with payment_method and payment_reference
- [ ] Create workflow audit log table
- [ ] Add billing status reports for compliance/audit
- [ ] Implement claims submission tracking
- [ ] Add insurance denial/correction workflows