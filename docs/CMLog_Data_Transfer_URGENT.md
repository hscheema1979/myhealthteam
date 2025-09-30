# CMLog Data Transfer Implementation Guide - URGENT P0

**Priority:** P0 - URGENT  
**Date:** September 22, 2025  
**Status:** Critical Implementation Required  
**Issue:** Coordinator tasks data needs to be finalized from CMLog downloads

---

## Overview

This document provides the urgent implementation guide for transferring CMLog data from the `downloads/` folder into the `coordinator_tasks` table and ensuring proper data flow to the coordinator dashboards.

## Current State Analysis

### Data Sources Available

- **Main consolidated file:** `downloads/cmlog.csv` (17,557 rows)
- **Individual coordinator files:** `downloads/coordinators/CMLog_*.csv`
- **Target table:** `coordinator_tasks` (exists but needs population)
- **Summary table:** `coordinator_monthly_summary` (dependent on coordinator_tasks)

### CMLog Data Structure

```csv
# Key columns from downloads/cmlog.csv:
Staff,Pt Name,Type,Date Only,Start Time,Notes,Stop Time,Start Time B,Stop Time B,Mins B,ZEN,Total Mins,Current,"Last, First DOB",NotZEN,Start Time A,Stop Time A
```

### Critical Data Mapping

**FROM CMLog TO coordinator_tasks:**

- `Staff` → `user_id` (via staff_code_mapping)
- `Pt Name` → `patient_name`
- `Type` → `task_type`
- `Date Only` → `task_date`
- `Mins B` → `duration_minutes` (primary time field)
- `Notes` → `notes`
- `"Last, First DOB"` → Used for patient_id matching

---

## URGENT Implementation Steps

### Phase 1: Integration with Existing Workflow (IMMEDIATE)

**The issue:** CMLog data is already being imported through your existing workflow but not properly transformed into `coordinator_tasks`.

**Root cause:** The existing `4_transform_data_enhanced.ps1` script calls `populate_coordinator_tasks.sql` which transforms from `SOURCE_COORDINATOR_TASKS_HISTORY` to `coordinator_tasks`, but this transformation may not be working properly.

**Solution:** Fix the transformation instead of creating new import scripts.

**Check current status:**

```powershell
# Check if SOURCE_COORDINATOR_TASKS_HISTORY has data
python -c "
import sqlite3
conn = sqlite3.connect('production.db')
source_count = conn.execute('SELECT COUNT(*) FROM SOURCE_COORDINATOR_TASKS_HISTORY').fetchone()[0]
tasks_count = conn.execute('SELECT COUNT(*) FROM coordinator_tasks').fetchone()[0]
print(f'SOURCE_COORDINATOR_TASKS_HISTORY: {source_count} rows')
print(f'coordinator_tasks: {tasks_count} rows')
conn.close()
"
```

**If SOURCE_COORDINATOR_TASKS_HISTORY is empty, run existing workflow:**

```powershell
# Use your existing workflow to get the data
.\run_complete_workflow.ps1
```

**If SOURCE_COORDINATOR_TASKS_HISTORY has data but coordinator_tasks is empty:**

**Fix the transformation SQL script:**

```powershell
# Check if the SQL transformation script exists and is working
ls src\sql\populate_coordinator_tasks.sql
```

**Create fixed transformation script if needed:**

```sql
-- src/sql/populate_coordinator_tasks_fixed.sql
-- Clear existing data first
DELETE FROM coordinator_tasks;
DELETE FROM coordinator_monthly_summary;

-- Transform from SOURCE_COORDINATOR_TASKS_HISTORY to coordinator_tasks
INSERT INTO coordinator_tasks (
    patient_id,
    patient_name,
    coordinator_id,
    user_id,
    coordinator_name,
    task_date,
    duration_minutes,
    task_type,
    notes
)
SELECT
    p.patient_id,
    sct."Pt Name" as patient_name,
    c.coordinator_id,
    u.user_id,
    u.full_name as coordinator_name,
    sct."Date Only" as task_date,
    CAST(sct."Mins B" AS INTEGER) as duration_minutes,
    sct."Type" as task_type,
    sct."Notes" as notes
FROM SOURCE_COORDINATOR_TASKS_HISTORY sct
LEFT JOIN staff_code_mapping scm ON LOWER(TRIM(sct."Staff")) = LOWER(TRIM(scm.staff_code))
LEFT JOIN users u ON scm.user_id = u.user_id
LEFT JOIN coordinators c ON u.user_id = c.user_id
LEFT JOIN patients p ON sct."Last, First DOB" = p.last_first_dob
WHERE sct."Type" != 'Place holder.  Do not change this row data'
AND sct."Staff" IS NOT NULL
AND sct."Pt Name" IS NOT NULL
AND sct."Mins B" IS NOT NULL
AND CAST(sct."Mins B" AS REAL) > 0;
```

**Run the fixed transformation:**

```powershell
# Apply the fixed transformation
Get-Content "src\sql\populate_coordinator_tasks_fixed.sql" | sqlite3 production.db
```

### Phase 2: Generate Monthly Summaries (Using Existing Process)

**Your existing workflow already handles this in step 4:** `4_transform_data_enhanced.ps1` calls:

- `populate_coordinator_monthly_summary.sql`

**But if monthly summaries are empty, run manually:**

```sql
-- Generate monthly summaries (this should already be in your SQL scripts)
DELETE FROM coordinator_monthly_summary;

INSERT INTO coordinator_monthly_summary (
    coordinator_id, coordinator_name, patient_id, patient_name,
    year, month, total_minutes, billing_code_id, billing_code, billing_code_description
)
SELECT
    ct.coordinator_id,
    ct.coordinator_name,
    ct.patient_id,
    ct.patient_name,
    CAST(strftime('%Y', ct.task_date) AS INTEGER) as year,
    CAST(strftime('%m', ct.task_date) AS INTEGER) as month,
    SUM(ct.duration_minutes) as total_minutes,
    cbc.code_id,
    cbc.billing_code,
    cbc.billing_code_description
FROM coordinator_tasks ct
LEFT JOIN coordinator_billing_codes cbc ON
    SUM(ct.duration_minutes) >= cbc.min_minutes AND
    SUM(ct.duration_minutes) <= cbc.max_minutes
WHERE ct.duration_minutes IS NOT NULL
GROUP BY ct.coordinator_id, ct.patient_id,
         strftime('%Y', ct.task_date), strftime('%m', ct.task_date);
```

### Phase 3: Database Functions (IMMEDIATE)

**Add to:** `src/database.py`

```python
def get_coordinator_weekly_patient_minutes(coordinator_id, weeks_back=4):
    """Get minutes logged per patient per week for coordinator"""
    conn = get_db_connection()
    try:
        query = """
            SELECT
                ct.patient_id,
                ct.patient_name,
                strftime('%Y-%W', ct.task_date) as week,
                strftime('%Y-%m-%d', ct.task_date) as week_start,
                SUM(ct.duration_minutes) as total_minutes,
                COUNT(*) as task_count
            FROM coordinator_tasks ct
            WHERE ct.coordinator_id = ?
            AND ct.task_date >= date('now', '-' || ? || ' days')
            AND ct.duration_minutes > 0
            GROUP BY ct.patient_id, strftime('%Y-%W', ct.task_date)
            ORDER BY week DESC, ct.patient_name
        """
        return conn.execute(query, (coordinator_id, weeks_back * 7)).fetchall()
    finally:
        conn.close()

def get_coordinator_tasks_by_date_range(coordinator_id, start_date, end_date):
    """Get all coordinator tasks within date range"""
    conn = get_db_connection()
    try:
        query = """
            SELECT
                ct.coordinator_task_id,
                ct.patient_name,
                ct.task_date,
                ct.duration_minutes,
                ct.task_type,
                ct.notes,
                p.patient_id
            FROM coordinator_tasks ct
            LEFT JOIN patients p ON ct.patient_id = p.patient_id
            WHERE ct.coordinator_id = ?
            AND date(ct.task_date) >= date(?)
            AND date(ct.task_date) <= date(?)
            ORDER BY ct.task_date DESC
        """
        return conn.execute(query, (coordinator_id, start_date, end_date)).fetchall()
    finally:
        conn.close()

def get_coordinator_monthly_summary_current_month(coordinator_id):
    """Get current month summary for coordinator"""
    conn = get_db_connection()
    try:
        query = """
            SELECT
                cms.patient_name,
                cms.total_minutes,
                cms.billing_code,
                cms.billing_code_description
            FROM coordinator_monthly_summary cms
            WHERE cms.coordinator_id = ?
            AND cms.year = strftime('%Y', 'now')
            AND cms.month = strftime('%m', 'now')
            ORDER BY cms.total_minutes DESC
        """
        return conn.execute(query, (coordinator_id,)).fetchall()
    finally:
        conn.close()
```

### Phase 4: Dashboard Integration (HIGH PRIORITY)

**Modify:** `src/dashboards/care_coordinator_dashboard_enhanced.py`

```python
def show_weekly_patient_minutes(coordinator_id):
    """Display weekly patient minutes tracking"""
    st.subheader("Weekly Patient Time Tracking")

    # Get weekly data
    weekly_data = database.get_coordinator_weekly_patient_minutes(coordinator_id, weeks_back=8)

    if weekly_data:
        df = pd.DataFrame(weekly_data)

        # Create pivot table for better display
        pivot_df = df.pivot(index='patient_name', columns='week', values='total_minutes')
        pivot_df = pivot_df.fillna(0)

        st.dataframe(pivot_df, use_container_width=True)

        # Summary stats
        total_patients = len(pivot_df)
        avg_minutes_per_patient = df.groupby('patient_name')['total_minutes'].sum().mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Patients", total_patients)
        with col2:
            st.metric("Avg Minutes/Patient", f"{avg_minutes_per_patient:.1f}")
        with col3:
            st.metric("Total Minutes", f"{df['total_minutes'].sum():.0f}")
    else:
        st.info("No task data available for the selected period.")
```

---

## Critical Issues to Resolve

### 1. Staff Code Mapping

**Issue:** CMLog uses staff codes (e.g., "AteDi000") that need mapping to user_id/coordinator_id
**Solution:** Ensure `staff_code_mapping` table is populated and accurate

### 2. Patient Matching

**Issue:** Patient names in CMLog may not exactly match database patients
**Solution:** Use "Last, First DOB" field for accurate patient matching

### 3. Data Quality

**Issue:** CMLog contains placeholder rows and invalid entries
**Solution:** Filter out placeholder data and validate time entries

### 4. Time Tracking Accuracy

**Issue:** Multiple time fields (Mins B, Total Mins, etc.)
**Solution:** Use "Mins B" as primary duration source (most accurate)

---

## Immediate Action Items

### TODAY (URGENT)

1. **Run data import:** Execute Phase 1 script to populate coordinator_tasks
2. **Generate summaries:** Run Phase 2 script for monthly summaries
3. **Test dashboard:** Verify coordinator dashboard shows weekly minutes

### THIS WEEK

1. **Add database functions** from Phase 3
2. **Update dashboard UI** with weekly tracking component
3. **Validate data accuracy** with coordinator team

### VERIFICATION QUERIES

```sql
-- Check total tasks imported
SELECT COUNT(*) as total_tasks FROM coordinator_tasks;

-- Check tasks by coordinator
SELECT coordinator_name, COUNT(*) as task_count,
       SUM(duration_minutes) as total_minutes
FROM coordinator_tasks
GROUP BY coordinator_id
ORDER BY total_minutes DESC;

-- Check monthly summaries
SELECT year, month, COUNT(*) as summaries
FROM coordinator_monthly_summary
GROUP BY year, month
ORDER BY year DESC, month DESC;
```

---

## Files to Create/Modify

**New Scripts:**

- `scripts/5_import_cmlog_data.ps1`
- `scripts/6_generate_coordinator_summaries.ps1`

**Modify:**

- `src/database.py` (add coordinator task functions)
- `src/dashboards/care_coordinator_dashboard_enhanced.py` (add weekly tracking)
- `scripts/run_complete_workflow.ps1` (add CMLog import step)

**Test:**

- Verify coordinator dashboard shows patient minutes
- Validate monthly summaries are accurate
- Check data consistency across all coordinator roles

This implementation will finalize the coordinator tasks data and enable the P0 dashboard features to function properly.
