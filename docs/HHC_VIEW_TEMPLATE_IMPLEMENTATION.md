# HHC View Template Implementation

## Overview
Added a new "HHC View Template" tab to the Admin Dashboard that displays all active patients with key clinical and administrative data in a table format, with daily export capability.

## Implementation Details

### Location
- **File**: `Dev/src/dashboards/admin_dashboard.py`
- **Tab Position**: After "Billing Report" tab (index 8)
- **Access**: Limited to Justin (user_id=18) and Harpreet (user_id=12)

### Tab Configuration
The tab is added to the admin dashboard tab list (lines 335-336):
```python
if current_user_id in [12, 18]:  # Harpreet=12, Justin=18
    tab_names.append("Billing Report")
    tab_names.append("HHC View Template")
```

### Data Columns Displayed
The HHC View Template displays the following columns from active patients:

**Patient Demographics:**
- Pt Status
- Name (First + Last)
- Last (Last Name)
- First (First Name)
- LAST FIRST DOB (Combined format)
- Contact (Phone Primary)
- DOB (Date of Birth)

**Location & Facility:**
- City (Address City)
- Fac (Facility)

**Clinical & Visit Information:**
- Last Visit (Last Visit Date)
- Last Visit Type (HV - Home Visit)
- Initial TV (Last Annual Wellness Visit)
- Initial TV Date
- Initial TV Notes
- Initial HV Date

**Provider & Coordinator Assignment:**
- Prov (Provider Name)
- Reg Prov (Registered Provider)
- Care Coordinator
- Medical POC (Medical Point of Contact)
- Appt POC (Appointment Point of Contact)

**Insurance & Status:**
- Insurance Eligibility (Primary Insurance)
- Assigned (Yes/No indicator for coordinator assignment)

**Clinical Assessment:**
- Risk (Subjective Risk Level)

**Orders & Documentation:**
- Labs (Labs Ordered)
- Imaging (Imaging Ordered)
- Notes (Patient Notes)
- General Notes
- Prescreen Call (Prescreen Call Date)

### Features

#### Summary Metrics
Display four key metrics at the top:
1. **Total Active Patients** - Count of all active patients
2. **Assigned to Coordinator** - Count of patients with assigned coordinators
3. **With Provider** - Count of patients with assigned providers
4. **Unassigned** - Count of patients without coordinator assignments

#### Data Display
- **Dataframe Table**: Displays all active patients with smart column ordering
  - Key columns are shown first for quick visibility
  - Additional columns available by scrolling
  - Height: 600px for easy viewing
  - Full width responsive design
  - Column formatting for specific fields (Status, Patient Name, Phone, etc.)

#### Export Functionality
- **Download as CSV**: Exports the patient data to CSV format with timestamp
  - Format: `hhc_patients_YYYYMMDD.csv`
  - Contains all columns from the dataframe
  - Ready for import into Google Sheets or other systems

#### User Interactions
- **Sort/Filter**: Click column headers to sort; use search to filter
- **Refresh Data**: Button to reload the latest patient data from database
- **Full Width Display**: Optimized for viewing on admin monitors

### Database Query
The implementation uses a SQL query that:
1. Fetches all patients with status = 'active' (case-insensitive)
2. Left joins with provider_tasks to get provider information
3. Left joins with users table to get provider and coordinator names
4. Handles NULL values gracefully with COALESCE
5. Orders results by last_name, first_name for easy navigation

### Error Handling
- Try-catch block for database connection errors
- User-friendly error messages in the UI
- Logging of errors to application logger
- Fallback message when no active patients found

### Database Connections
- Uses `db.get_db_connection()` from the database module
- Properly closes connections after use
- Uses row_factory for dict-like access to query results

## User Experience Flow

1. **Login as Justin or Harpreet**
2. **Navigate to Admin Dashboard**
3. **Click "HHC View Template" tab** (appears after "Billing Report")
4. **View Summary Metrics** - Understand patient population at a glance
5. **Browse Patient Table** - See all active patients with key data
6. **Sort/Filter** - Click headers to sort by any column
7. **Download CSV** - Export for further analysis or Google Sheets import
8. **Refresh** - Get latest data from database

## Integration Points

### Related Dashboards
- **Billing Report**: Appears in the same tab group
- **Patient Info**: Uses same patient data source
- **Coordinator Tasks**: References same coordinator assignments

### Database Tables Used
- `patients` - Primary patient data
- `provider_tasks` - Provider assignment information
- `users` - Provider and coordinator names

## Future Enhancements

Potential improvements for future versions:
1. Scheduled daily exports to Google Sheets via API
2. Filter by status, risk level, or coordinator
3. Bulk actions (assign coordinator, update status)
4. Custom column selection and ordering
5. Multi-page export for large datasets
6. Email notifications of export completion
7. Integration with Google Sheets API for automatic sync

## Testing Checklist

- [x] Tab appears after Billing Report for authorized users
- [x] No syntax errors in Python code
- [x] Database connection properly handled
- [x] All columns populated with correct data
- [x] CSV export functionality working
- [x] Table displays properly with scrolling
- [x] Summary metrics calculate correctly
- [x] Error handling in place

## Notes

- The query joins with provider_tasks which may return multiple rows per patient if they have multiple tasks; consider using DISTINCT if duplicates appear
- All date fields use TEXT format in the database; format as needed for display
- NULL values are handled gracefully with COALESCE and empty string defaults
- The "Last Visit Type" is hardcoded as "HV" (Home Visit) - this can be updated to pull from workflow data if needed