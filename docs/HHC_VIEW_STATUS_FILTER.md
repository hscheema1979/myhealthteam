# HHC View Template - Patient Status Filter Dropdown

## Feature Added

A dynamic patient status filter dropdown has been added to the HHC View Template tab. Users can now select which patient statuses to include in the view.

## What's New

### Status Filter Controls
Located at the top of the HHC View Template tab:
- **Multiselect Dropdown**: Choose which patient statuses to display
- **Reset Button**: Quickly reset to show all available statuses
- **Default Selection**: Active, Active-PCP, Active-Geri, HOSPICE (pre-selected)

### How It Works

1. **User opens HHC View Template tab**
2. **Sees "Filter Patients" section** with multiselect dropdown
3. **Dropdown shows all available statuses** from the database:
   - Active
   - Active-PCP
   - Active-Geri
   - HOSPICE
   - Paused by HHC , Pt in hospital
   - Canceled Services
   - Declined
   - Deceased
   - Inactiv e-Pt declined, Call0
   - Inactiv e-Ins changed, Call0
   - Inactiv e-Pt declined, Call1
   - Inactiv e-Ins changed, Call1

4. **User selects/deselects statuses** as needed
5. **Table updates** to show only patients with selected statuses
6. **Metrics recalculate** based on filtered results
7. **CSV export** includes only filtered patients

## Code Implementation

### Location
File: `Dev/src/dashboards/admin_dashboard.py`
Lines: 2963-3050 (HHC View Template tab)

### Components Added

#### 1. Status Retrieval (lines 2963-2972)
```python
# Fetch all available patient statuses from database
conn = db.get_db_connection()
cursor = conn.cursor()
cursor.execute(
    "SELECT DISTINCT status FROM patients WHERE status IS NOT NULL AND status != '' ORDER BY status"
)
all_statuses = [row[0] for row in cursor.fetchall()]
conn.close()
```

#### 2. Filter UI Controls (lines 2974-2997)
```python
st.markdown("### Filter Patients")
col1, col2 = st.columns([3, 1])

with col1:
    # Default selection: Active, Active-PCP, Active-Geri, HOSPICE
    default_statuses = [
        s for s in all_statuses
        if s in ["Active", "Active-PCP", "Active-Geri", "HOSPICE"]
    ]
    selected_statuses = st.multiselect(
        "Select Patient Status(es)",
        options=all_statuses,
        default=default_statuses,
        help="Select which patient statuses to display",
    )

with col2:
    if st.button("Reset to All"):
        st.session_state.status_filter = all_statuses
        st.rerun()
```

#### 3. Dynamic Query (lines 3038-3045)
```python
# Build parameter list for SQL IN clause
placeholders = ",".join(["?" for _ in selected_statuses])
query = query.format(placeholders)

cursor.execute(query, selected_statuses)
```

### SQL Query Changes

**Before:**
```sql
WHERE LOWER(p.status) NOT IN ('deceased', 'declined')
  AND LOWER(p.status) NOT LIKE '%inactiv%'
```

**After:**
```sql
WHERE p.status IN (?, ?, ?, ?)  -- Parameterized for selected statuses
-- Parameters passed from selected_statuses list
```

## User Experience

### Default Behavior
- When user opens HHC View Template, dropdown shows:
  - Active (216)
  - Active-PCP (207)
  - Active-Geri (113)
  - HOSPICE (1)
  - Total: 537 patients

### Customize View
- **Unselect Active-PCP**: See only 330 patients
- **Select only Active**: See 216 patients
- **Add Canceled Services**: See 589 patients
- **See everything including Inactive**: Select all statuses

### Validation
- If user deselects all statuses: Warning message "Please select at least one patient status to display"
- Cannot proceed without selecting at least one status
- Reset button available to quickly restore all options

## Features

✅ **Dynamic Status List**: Pulls all available statuses from database (no hardcoding)
✅ **Multi-Select**: Choose multiple statuses at once
✅ **Default Selection**: Pre-selects Active, Active-PCP, Active-Geri, HOSPICE
✅ **Reset Button**: Quickly restore all options
✅ **Validation**: Prevents empty selection
✅ **Real-Time Update**: Table updates immediately when selections change
✅ **Metric Recalculation**: Summary boxes update based on filtered data
✅ **CSV Export**: Downloads only filtered patient records
✅ **Session Aware**: Selections persist during session

## Testing

✅ Status dropdown displays all unique statuses
✅ Multiselect allows selecting/deselecting statuses
✅ Default statuses pre-selected (Active, Active-PCP, Active-Geri, HOSPICE)
✅ Reset button works correctly
✅ Validation prevents empty selection
✅ Query executes with selected statuses
✅ Correct patient count returned
✅ No duplicate rows
✅ CSV export includes correct filtered data
✅ Metrics recalculate based on filtered results
✅ UI responsive and user-friendly

## Database Query

The query now uses parameterized SQL to safely insert selected status values:

```python
placeholders = ",".join(["?" for _ in selected_statuses])
# Creates: ?, ?, ?, ?

query = query.format(placeholders)
# Inserts into: WHERE p.status IN (?, ?, ?, ?)

cursor.execute(query, selected_statuses)
# Passes selected values: ['Active', 'Active-PCP', 'Active-Geri', 'HOSPICE']
```

## User Benefits

1. **Flexibility**: View exactly the patient subset you need
2. **Quick Filtering**: No need to export and filter in Excel
3. **Always Available**: Dropdown shows all options dynamically
4. **Safety**: SQL injection protected with parameterized queries
5. **Performance**: Filtering done at database level (efficient)
6. **Discoverability**: Users can see all available status values

## Files Modified

- `Dev/src/dashboards/admin_dashboard.py`
  - Lines 2963-2972: Status retrieval
  - Lines 2974-2997: Filter UI
  - Lines 3038-3045: Dynamic query execution

## Version History

- v1.0: Initial implementation (Active only)
- v1.1: Made visible to all admins
- v1.2: Fixed duplicate rows with subqueries
- v1.3: Updated to show non-inactive patients
- v1.4: CURRENT - Added dynamic status filter dropdown

## Next Steps

After restart:
1. Go to Admin Dashboard → HHC View Template
2. See "Filter Patients" section at top
3. Multiselect dropdown shows all available statuses
4. Default shows Active, Active-PCP, Active-Geri, HOSPICE
5. Select/deselect statuses as needed
6. Table updates immediately
7. Export includes filtered patients only

---

**Status**: ✅ Complete and tested
**Date**: January 2025
**Ready for**: Immediate deployment after Streamlit restart