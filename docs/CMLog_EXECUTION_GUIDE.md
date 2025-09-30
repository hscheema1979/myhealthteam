# CMLog Data Transfer - EXECUTION PROMPT

**URGENT P0 Implementation - Step-by-Step Execution Guide**

---

## PRE-EXECUTION CHECKLIST

Before starting, verify these requirements:

```powershell
# 1. Check you're in the correct directory
cd "D:\Git\myhealthteam2\Streamlit"
pwd  # Should show the Streamlit directory

# 2. Verify data files exist
ls downloads\cmlog.csv
ls downloads\coordinators\

# 3. Check database exists
ls production.db

# 4. Test Python/database connection
python -c "import sqlite3; conn = sqlite3.connect('production.db'); print('Database connection OK'); conn.close()"
```

---

## EXECUTION SEQUENCE

### STEP 1: Use Your Existing Workflow First

**Instead of creating new scripts, let's check if your existing 4-step workflow is properly handling the CMLog data:**

```powershell
# Check current status of coordinator data
python -c "
import sqlite3
conn = sqlite3.connect('production.db')
source_count = conn.execute('SELECT COUNT(*) FROM SOURCE_COORDINATOR_TASKS_HISTORY').fetchone()[0]
tasks_count = conn.execute('SELECT COUNT(*) FROM coordinator_tasks').fetchone()[0]
monthly_count = conn.execute('SELECT COUNT(*) FROM coordinator_monthly_summary').fetchone()[0]
print(f'SOURCE_COORDINATOR_TASKS_HISTORY: {source_count} rows')
print(f'coordinator_tasks: {tasks_count} rows')
print(f'coordinator_monthly_summary: {monthly_count} rows')
conn.close()
"
```

**If all counts are 0, run your complete workflow:**

```powershell
.\run_complete_workflow.ps1
```

**If SOURCE data exists but coordinator_tasks is empty, the transformation is broken - proceed to Step 2.**

### STEP 2: Fix the Transformation (Only if needed)

**Execute this prompt if your existing transformation isn't working:**

```
The coordinator tasks transformation is failing. Create a fixed SQL script that properly transforms data from SOURCE_COORDINATOR_TASKS_HISTORY to coordinator_tasks table.

The script should:
1. Clear existing coordinator_tasks and coordinator_monthly_summary data
2. Transform CMLog data using proper staff_code_mapping to get coordinator_id and user_id
3. Match patients using the "Last, First DOB" field
4. Filter out placeholder rows and entries with zero minutes
5. Use "Mins B" as the duration source

Create this as `src/sql/populate_coordinator_tasks_fixed.sql` and test it works with the existing database structure.
```

### STEP 3: Add Database Functions

**Execute this prompt:**

```
Create the PowerShell scripts for CMLog data import as specified in the CMLog_Data_Transfer_URGENT.md document:

1. Create `scripts/5_import_cmlog_data.ps1` with the exact PowerShell code from Phase 1
2. Create `scripts/6_generate_coordinator_summaries.ps1` with the exact PowerShell code from Phase 2
3. Make sure both scripts handle error cases and provide status updates
4. Test the scripts syntax before execution
```

### STEP 2: Add Database Functions

**Execute this prompt:**

```
Add the following database functions to `src/database.py` as specified in Phase 3 of CMLog_Data_Transfer_URGENT.md:

1. `get_coordinator_weekly_patient_minutes(coordinator_id, weeks_back=4)`
2. `get_coordinator_tasks_by_date_range(coordinator_id, start_date, end_date)`
3. `get_coordinator_monthly_summary_current_month(coordinator_id)`

Follow the exact function signatures and SQL queries provided in the document. Add proper error handling with try/finally blocks for database connections.
```

### STEP 4: Test Your Existing Workflow Results

**After running your existing workflow, verify the data:\*\***Run these commands in PowerShell terminal:\*\*

```powershell
# Navigate to scripts directory
cd scripts

# Execute the import (this will take several minutes)
.\5_import_cmlog_data.ps1

# Verify import results
python -c "
import sqlite3
conn = sqlite3.connect('../production.db')
count = conn.execute('SELECT COUNT(*) FROM coordinator_tasks').fetchone()[0]
print(f'Total coordinator tasks imported: {count}')

# Check by coordinator
results = conn.execute('''
    SELECT coordinator_name, COUNT(*) as task_count,
           SUM(duration_minutes) as total_minutes
    FROM coordinator_tasks
    WHERE coordinator_name IS NOT NULL
    GROUP BY coordinator_id
    ORDER BY total_minutes DESC
    LIMIT 10
''').fetchall()

print('\nTop coordinators by total minutes:')
for row in results:
    print(f'{row[0]}: {row[1]} tasks, {row[2]} minutes')

conn.close()
"
```

### STEP 4: Generate Monthly Summaries

**Run this command:**

```powershell
# Still in scripts directory
.\6_generate_coordinator_summaries.ps1

# Verify summaries
python -c "
import sqlite3
conn = sqlite3.connect('../production.db')

summaries = conn.execute('''
    SELECT year, month, COUNT(*) as summary_count,
           SUM(total_minutes) as total_minutes
    FROM coordinator_monthly_summary
    GROUP BY year, month
    ORDER BY year DESC, month DESC
    LIMIT 12
''').fetchall()

print('Monthly summaries generated:')
for row in summaries:
    print(f'{row[0]}-{row[1]:02d}: {row[2]} summaries, {row[3]} total minutes')

conn.close()
"
```

### STEP 5: Update Dashboard

**Execute this prompt:**

```
Update the Care Coordinator Dashboard to include weekly patient minutes tracking:

1. Modify `src/dashboards/care_coordinator_dashboard_enhanced.py`
2. Add the `show_weekly_patient_minutes()` function from Phase 4 of the CMLog_Data_Transfer_URGENT.md
3. Integrate it into the main coordinator dashboard tabs
4. Follow the existing dashboard patterns and UI style configuration
5. Test that the function imports and displays properly
```

### STEP 6: Test Dashboard Integration

**Run application and test:**

```powershell
# Go back to root directory
cd ..

# Start Streamlit application
streamlit run app.py

# In the app:
# 1. Select "Care Coordinator" role
# 2. Select a coordinator user
# 3. Verify the weekly patient minutes tracking appears
# 4. Check that data displays correctly
```

---

## VALIDATION CHECKLIST

After execution, verify these results:

### ✅ Data Import Validation

```sql
-- Run these queries in database to verify:

-- 1. Total tasks imported (should be > 10,000)
SELECT COUNT(*) as total_tasks FROM coordinator_tasks;

-- 2. Tasks have proper coordinator mapping
SELECT COUNT(*) as mapped_coordinators
FROM coordinator_tasks
WHERE coordinator_id IS NOT NULL;

-- 3. Patient matching worked
SELECT COUNT(*) as matched_patients
FROM coordinator_tasks
WHERE patient_id IS NOT NULL;

-- 4. Monthly summaries generated
SELECT COUNT(*) as monthly_summaries
FROM coordinator_monthly_summary;
```

### ✅ Dashboard Functionality

- [ ] Coordinator dashboard loads without errors
- [ ] Weekly patient minutes table displays
- [ ] Summary metrics show correct totals
- [ ] Data refreshes when switching coordinators

### ✅ Performance Check

- [ ] Dashboard loads within 3 seconds
- [ ] Database queries complete quickly
- [ ] No memory leaks or connection issues

---

## TROUBLESHOOTING PROMPTS

### If Data Import Fails:

```
Debug the CMLog data import process:

1. Check the cmlog.csv file format and verify column names match expected structure
2. Verify staff_code_mapping table exists and has proper coordinator mappings
3. Check for data type mismatches in the import script
4. Add debug logging to see exactly where the import is failing
5. Test with a smaller subset of data first
```

### If Dashboard Doesn't Load:

```
Debug the coordinator dashboard integration:

1. Check import statements in care_coordinator_dashboard_enhanced.py
2. Verify database functions are properly added to src/database.py
3. Test database functions independently before dashboard integration
4. Check for syntax errors in the new dashboard code
5. Verify UI style configuration imports are correct
```

### If Performance Is Slow:

```
Optimize the coordinator data queries:

1. Add database indexes for coordinator_tasks table on commonly queried columns
2. Optimize the weekly summary queries to use more efficient date filtering
3. Consider caching monthly summaries for better dashboard performance
4. Check for N+1 query issues in dashboard code
```

---

## SUCCESS METRICS

**You'll know it's working when:**

1. **coordinator_tasks table** has 10,000+ records
2. **coordinator_monthly_summary** has monthly aggregations
3. **Dashboard shows** weekly patient minutes by coordinator
4. **Performance** - pages load quickly without errors
5. **Data accuracy** - coordinators can see their actual logged time

---

## NEXT STEPS AFTER SUCCESS

Once CMLog data is successfully imported:

1. Move to P0 dashboard enhancements (Phone Reviews tab, etc.)
2. Begin provider patient panel updates
3. Implement onboarding form enhancements
4. Start working on workflow management features

---

**Execute each step in sequence and verify success before proceeding to the next step.**
