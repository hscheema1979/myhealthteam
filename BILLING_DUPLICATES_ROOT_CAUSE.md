# Billing Report Duplicates - Root Cause Analysis

## Executive Summary
**CRITICAL ISSUE FOUND:** 6,119 duplicate task groups exist in `provider_task_billing_status` table, causing billing reports to show duplicate/triplicate (or more) line items.

## Root Cause

### 1. **Missing UNIQUE Constraint**
The `provider_task_billing_status` table lacks a UNIQUE constraint on the natural key combination:
- `provider_task_id` + `billing_week` + `is_carried_over`

This allows the same task to be inserted multiple times with different billing_week values.

### 2. **Automatic Data Population on Every Dashboard Load**
File: `src/dashboards/weekly_provider_billing_dashboard.py`

```python
def display_weekly_provider_billing_dashboard(user_id=None, user_role_ids=None):
    # Auto-populate billing data from provider_tasks if empty
    ensure_billing_data_populated()  # ⚠️ Runs EVERY time!
```

The `ensure_billing_data_populated()` function:
- Runs on EVERY dashboard load
- Processes ALL monthly tables (provider_tasks_2025_09, 2025_10, etc.)
- Uses `INSERT OR IGNORE` which only prevents EXACT duplicates
- **Does NOT prevent the same task being inserted with DIFFERENT billing_week values**

### 3. **Carryover Logic Creates Additional Duplicates**
File: `src/billing/weekly_billing_processor.py`

The `_process_weekly_billing_python()` method:
```python
# Step 1: Create carryover entries for unbilled tasks from previous weeks
carryover_query = """
INSERT OR IGNORE INTO provider_task_billing_status (
    provider_task_id,
    ...,
    billing_week,  # ⚠️ NEW billing_week
    is_carried_over = 1,
    original_billing_week = pbs.billing_week  # ⚠️ Original week stored
)
FROM provider_task_billing_status pbs
WHERE pbs.billing_status = 'Not Billed'
    AND pbs.billing_week < ?
    AND pbs.is_carried_over = 0
```

**Problem:** If the weekly billing processor runs multiple times:
- First run: Creates carryover records for Week 10 tasks into Week 11
- Second run: Creates carryover records for Week 11 carryover tasks into Week 12
- Third run: Creates carryover records for Week 12 carryover tasks into Week 13
- **Result:** Same task appears in Week 10, 11, 12, 13, etc.

### 4. **Data Repopulation Issues**
When the dashboard loads multiple times or the data refresh scripts run:
- `ensure_billing_data_populated()` reads from monthly tables
- Each time it can re-insert tasks if billing_week calculation varies
- No deduplication beyond exact INSERT OR IGNORE

## Evidence from Database Analysis

```
Total exact duplicate groups: 6,119

Sample Pattern:
provider_task_id | billing_week | is_carried_over | duplicate_count
-----------------|--------------|------------------|---------------
262             | 2025-10      | 0                | 2
262             | 2025-15      | 0                | 2
262             | 2025-38      | 0                | 2
```

Each provider_task_id has 2-3 copies across different billing_week values.

## Impact

1. **Billing Reports:** Show duplicate/triplicate line items for the same service
2. **Weekly Summaries:** Inflated task counts and minutes
3. **Monthly Summaries:** Incorrect totals (summing same task multiple times)
4. **Provider Payroll:** Potential double-counting if not filtered properly
5. **Data Integrity:** Hard to determine which record is the "correct" one

## Recommended Fix Strategy

### Phase 1: Immediate Data Cleanup (HIGH PRIORITY)
1. **Identify and remove true duplicates** - keep one record per (provider_task_id, billing_week, is_carried_over) combination
2. **Create a cleanup script** that:
   - Identifies duplicates
   - Marks which record to keep (highest billing_status_id = most recent)
   - Deletes older duplicates

### Phase 2: Schema Changes
1. **Add UNIQUE constraint** to prevent future duplicates:
```sql
-- Create a new table with proper constraints
CREATE TABLE provider_task_billing_status_clean (
    billing_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_task_id INTEGER NOT NULL,
    billing_week TEXT NOT NULL,
    is_carried_over INTEGER DEFAULT 0 NOT NULL,
    UNIQUE(provider_task_id, billing_week, is_carried_over),
    -- ... other columns
);

-- Migrate unique data
INSERT INTO provider_task_billing_status_clean
SELECT DISTINCT ON (provider_task_id, billing_week, is_carried_over) *
FROM provider_task_billing_status;

-- Replace old table
DROP TABLE provider_task_billing_status;
ALTER TABLE provider_task_billing_status_clean RENAME TO provider_task_billing_status;
```

### Phase 3: Code Changes
1. **Fix `ensure_billing_data_populated()`**:
   - Add check: Only populate if table is EMPTY
   - Or add tracking of last populated timestamp
   - Prevent re-population of existing tasks

2. **Fix carryover logic**:
   - Add UNIQUE constraint on (provider_task_id, billing_week, is_carried_over)
   - Prevent re-carryover of already-carried-over tasks
   - Add tracking to ensure each task is only carried over once

3. **Fix summary queries**:
   - Add DISTINCT or GROUP BY clauses
   - Explicitly deduplicate by (provider_task_id, billing_week)

## Next Steps

1. Review and approve cleanup script
2. Backup current database before cleanup
3. Run cleanup script
4. Add schema constraints
5. Update code to prevent future duplicates
6. Test billing reports with clean data
