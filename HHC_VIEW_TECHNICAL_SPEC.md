# HHC View Template - Technical Specification

## Overview
The HHC View Template is a Streamlit-based dashboard component that displays active patient data in a table format with export capabilities. It's integrated into the Admin Dashboard as a new tab accessible only to authorized users (Justin and Harpreet).

## Architecture

### File Location
- **Primary Implementation**: `Dev/src/dashboards/admin_dashboard.py`
- **Lines**: 2952-3097 (HHC View Template tab content)
- **Tab Configuration**: Lines 335-336 (tab name registration)

### Component Hierarchy
```
Admin Dashboard (admin_dashboard.py)
├── User Role Management Tab
├── Staff Onboarding Tab
├── Coordinator Tasks Tab
├── Provider Tasks Tab
├── Patient Info Tab
├── Workflow Reassignment Tab
├── For Testing Tab
├── Billing Report Tab
└── HHC View Template Tab (NEW)
    ├── Summary Metrics Row
    ├── Patient Data Table
    ├── Export Controls
    └── Refresh Button
```

## Database Schema

### Primary Tables Used

#### `patients` Table
Key columns queried:
- `patient_id` (TEXT PRIMARY KEY)
- `status` (TEXT) - "Active", "Inactive", etc.
- `first_name` (TEXT)
- `last_name` (TEXT)
- `date_of_birth` (TEXT)
- `phone_primary` (TEXT)
- `address_city` (TEXT)
- `facility` (TEXT)
- `insurance_primary` (TEXT)
- `last_visit_date` (TEXT)
- `last_first_dob` (TEXT)
- `last_annual_wellness_visit` (TEXT)
- `notes` (TEXT)
- `subjective_risk_level` (TEXT)
- `assigned_coordinator_id` (INTEGER, FOREIGN KEY)

#### `provider_tasks` Table
Key columns:
- `patient_id` (TEXT, FOREIGN KEY)
- `provider_id` (INTEGER, FOREIGN KEY)

#### `users` Table
Key columns:
- `user_id` (INTEGER PRIMARY KEY)
- `first_name` (TEXT)
- `last_name` (TEXT)

### Relationships
```
patients (1) ←→ (N) provider_tasks (N) ←→ (1) users (providers)
  ↓
patients.assigned_coordinator_id → users.user_id
```

## SQL Query Structure

### Query Purpose
Retrieve all active patients with their associated provider and coordinator information.

### Query Components

#### SELECT Clause
Returns 26 columns with aliases matching the HHC View Template format:
- Patient identifiers (patient_id)
- Patient demographics (status, name, DOB)
- Contact information (phone_primary)
- Facility information (facility, city)
- Visit history (last_visit_date, last_visit_type)
- Provider/Coordinator assignments
- Insurance information
- Risk assessment
- Clinical notes and additional fields

#### JOIN Operations
1. **LEFT JOIN provider_tasks**: Connects patients to their provider assignments
2. **LEFT JOIN users (pr)**: Retrieves provider names
3. **LEFT JOIN users (c)**: Retrieves coordinator names using assigned_coordinator_id

#### WHERE Clause
- Filters for active patients only
- Uses LOWER() for case-insensitive status matching
- Condition: `LOWER(p.status) = 'active'`

#### ORDER BY
- Primary: `p.last_name` (ascending)
- Secondary: `p.first_name` (ascending)

### NULL Handling
Uses COALESCE for graceful NULL value handling:
```sql
COALESCE(pr.first_name || ' ' || pr.last_name, 'Unassigned') -- providers
COALESCE(c.first_name || ' ' || c.last_name, 'Unassigned') -- coordinators
```

## Data Processing Pipeline

### Step 1: Data Retrieval
```python
conn = db.get_db_connection()  # SQLite3 connection with row_factory
cursor = conn.cursor()
cursor.execute(query)
columns = [description[0] for description in cursor.description]
rows = cursor.fetchall()
conn.close()
```

### Step 2: DataFrame Creation
```python
df_hhc = pd.DataFrame([dict(zip(columns, row)) for row in rows])
```
Converts SQLite rows into pandas DataFrame with column names as keys.

### Step 3: Metric Calculation
- **Total Active Patients**: `len(df_hhc)`
- **Assigned to Coordinator**: `(df_hhc["Assigned"] == "Yes").sum()`
- **With Provider**: Count where Prov != "Unassigned"
- **Unassigned**: Total - Assigned count

### Step 4: Column Reordering
```python
key_columns = [list of important columns]
display_columns = [col for col in key_columns if col in df_hhc.columns]
other_columns = [col for col in df_hhc.columns if col not in display_columns]
df_display = df_hhc[display_columns + other_columns]
```

### Step 5: Display Rendering
- Uses `st.dataframe()` with custom configuration
- Height: 600px
- Full width responsive layout
- Column-specific formatting

## Streamlit Components

### 1. Page Header
```python
st.subheader("HHC View Template - Active Patients")
st.markdown("Daily export view of all active patients with key clinical and administrative data")
```

### 2. Metrics Row
```python
col1, col2, col3, col4 = st.columns(4)
# Each column displays a metric using st.metric()
```

### 3. Data Table
```python
st.dataframe(
    df_display,
    use_container_width=True,
    height=600,
    column_config={...}
)
```

### 4. Column Configuration
Custom formatting for specific columns:
- `st.column_config.TextColumn()` - For text fields
- Specific width for Notes column (medium)

### 5. Control Row
Three columns for:
- CSV Download Button
- Tip Text
- Refresh Data Button

## Export Functionality

### CSV Generation
```python
csv_export = df_display.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download as CSV",
    data=csv_export,
    file_name=f"hhc_patients_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
```

### File Format
- **Format**: CSV (Comma-Separated Values)
- **Encoding**: UTF-8
- **Filename Pattern**: `hhc_patients_YYYYMMDD.csv`
- **Headers**: Included as first row
- **Index**: Excluded from export

### Content
All columns from the dataframe are included in the CSV export in the same order as displayed.

## Access Control

### Authorization
```python
current_user_id = st.session_state.get("user_id")
if current_user_id in [12, 18]:  # Harpreet=12, Justin=18
    tab_names.append("Billing Report")
    tab_names.append("HHC View Template")
```

### User IDs
- **Justin**: 12
- **Harpreet**: 18

### Role-Based Access
- Requires Admin role (role_id = 34)
- Additional user_id whitelist for specific authorization

## Error Handling

### Try-Catch Block
```python
try:
    # Database operations
    conn = db.get_db_connection()
    # ... query execution ...
except Exception as e:
    st.error(f"Error loading HHC View Template: {e}")
    logger.error(f"HHC View Template error: {e}", exc_info=True)
```

### Error Scenarios
1. **Database Connection Failure**: Displays error message to user
2. **Query Execution Error**: Caught and logged with traceback
3. **No Results**: Displays info message "No active patients found"
4. **Dataframe Processing Error**: Caught by outer exception handler

### Logging
- Uses Python `logging` module
- Logger name: `__name__` (module-level)
- Error level logs include full traceback with `exc_info=True`

## Performance Considerations

### Query Optimization
- Uses indexed columns (primary key lookups)
- LEFT JOINs only necessary tables
- Simple WHERE clause on indexed status column

### Dataframe Operations
- Single-pass DataFrame creation
- No redundant queries
- Connection closed immediately after use

### Display Optimization
- Lazy rendering of table (Streamlit optimizes display)
- Limited to 600px height to prevent excessive scrolling
- Column configuration applied only to visible columns

## Dependencies

### Required Libraries
- **streamlit**: UI framework
- **pandas**: Data manipulation
- **sqlite3**: Database connection (via `db` module)
- **datetime**: Timestamp generation for exports
- **logging**: Error logging

### Module Dependencies
- `src.database`: Database connection management
- `src.config.ui_style_config`: UI styling constants (not used in this component)

## Testing Checklist

### Functional Testing
- [ ] Tab appears in correct position (after Billing Report)
- [ ] Tab only visible to authorized users (Justin and Harpreet)
- [ ] Query returns all active patients
- [ ] Metrics calculate correctly
- [ ] Table displays with proper formatting
- [ ] CSV export contains all data
- [ ] Refresh button works properly

### Data Validation
- [ ] NULL values handled gracefully
- [ ] Date fields display correctly
- [ ] Coordinator assignments show accurately
- [ ] Provider names populated from users table
- [ ] Risk levels displayed

### Error Scenarios
- [ ] No active patients: Shows info message
- [ ] Database connection error: Shows error message
- [ ] Missing columns: Gracefully skips unavailable columns
- [ ] Large datasets: Performance remains acceptable

## Future Enhancement Opportunities

### Phase 2 Features
1. **Automated Google Sheets Sync**
   - Daily scheduled export to Google Sheets
   - Requires Google Sheets API credentials
   - Real-time sync option

2. **Advanced Filtering**
   - Filter by status, risk level, coordinator
   - Multi-select options
   - Saved filter presets

3. **Column Customization**
   - User-defined column visibility
   - Custom column ordering
   - Save preferences per user

4. **Bulk Operations**
   - Select multiple patients
   - Bulk assign coordinators
   - Bulk status updates
   - Bulk export variations

5. **Data Enhancements**
   - Days since last visit calculation
   - Days to next scheduled visit
   - Pending orders (labs/imaging)
   - Overdue actions

6. **Scheduling**
   - Scheduled daily exports
   - Email delivery
   - Automated Google Sheets updates

### Phase 3 Features
1. **Analytics Dashboard**
   - Charts on patient demographics
   - Provider utilization metrics
   - Coordinator workload distribution

2. **Export Variations**
   - Multiple format support (Excel, PDF)
   - Filtered exports
   - Template-based exports

3. **Alerts & Notifications**
   - Alert on unassigned patients
   - Alert on overdue visits
   - Alert on high-risk patients

## Related Components

### Dashboard Components
- **Billing Report**: Adjacent tab, similar design
- **Patient Info**: Uses same patient data source
- **Admin Dashboard**: Parent container

### Database Components
- **get_db_connection()**: Provides database access
- **Patient tables**: Primary data source
- **User tables**: For name/ID lookups

### Utility Functions
- **_fix_dataframe_for_streamlit()**: Data preparation
- **format_date()**: Date formatting helpers

## Maintenance Notes

### Code Location
- Implementation starts at line 2952 of admin_dashboard.py
- Tab registration at lines 335-336
- Tab variable assignment at line 402

### Key Variables
- `tab_hhc`: Streamlit tab object
- `df_hhc`: Main DataFrame with patient data
- `columns`: Column names from query
- `rows`: Raw query results

### Configuration Points
- User IDs (line 335): `[12, 18]`
- Table height: 600px (line 3009)
- Key columns list (lines 3013-3026)
- Export filename pattern (line 3070)

## Documentation References

### Internal Documents
- `HHC_VIEW_IMPLEMENTATION.md`: Implementation details
- `HHC_VIEW_QUICK_START.md`: User guide

### External References
- Streamlit Docs: https://docs.streamlit.io/
- SQLite Docs: https://www.sqlite.org/docs.html
- Pandas Docs: https://pandas.pydata.org/docs/

---

**Document Version**: 1.0
**Last Updated**: January 2025
**Status**: Active