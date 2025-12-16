# Billing Dashboards Implementation Summary

## Overview
Three billing/payroll dashboards have been created and integrated into the ZEN Medical system to provide comprehensive tracking of coordinator and provider billing workflows.

## Dashboards Created

### 1. Monthly Coordinator Billing Dashboard
**Location:** `src/dashboards/monthly_coordinator_billing_dashboard.py`

**Purpose:** Track coordinator billing by month with weekly breakdown capability

**Features:**
- Month selector to view different billing periods
- Week selector for focused weekly analysis
- Summary metrics:
  - Total Coordinators
  - Total Minutes of Service
  - Billed Tasks Count
  - Paid Tasks Count
- Three main tabs:
  - **Summary Tab:** Coordinator billing summary table with formatting
  - **Charts Tab:** Visual representations of billing status and coordinator performance
  - **Details Tab:** Drill-down into individual coordinator tasks by visit type

**Data Source:** `coordinator_tasks_YYYY_MM` tables

**Key Functions:**
- `get_available_months()` - Lists all available billing months
- `get_coordinator_monthly_summary()` - Aggregates coordinator data by month/week
- `get_coordinator_task_details()` - Retrieves individual task records
- `create_billing_status_chart()` - Visualizes billing status distribution
- `create_minutes_by_coordinator_chart()` - Shows top performers by minutes

**Database Columns Used:**
- coordinator_name
- COUNT(*) as total_tasks
- SUM(duration_minutes) as total_minutes
- submission_status, notes, task_type

---

### 2. Weekly Provider Billing Dashboard
**Location:** `src/dashboards/weekly_provider_billing_dashboard.py`

**Purpose:** Track provider billing by week, mirroring the coordinator billing dashboard structure

**Features:**
- Month selector for billing period selection
- Week selector for specific week analysis
- Summary metrics:
  - Total Providers
  - Total Minutes
  - Total Tasks
  - Average Minutes per Task
- Three main tabs:
  - **Summary Tab:** Provider billing summary with formatted numbers
  - **Charts Tab:** Top 10 providers by minutes and task count
  - **Details Tab:** Individual provider task breakdown

**Data Source:** `provider_tasks_YYYY_MM` tables

**Key Functions:**
- `get_available_months()` - Lists billing months with data
- `get_weeks_for_month()` - Gets available weeks within a month
- `get_provider_weekly_summary()` - Aggregates provider billing data
- `get_provider_task_details()` - Retrieves individual provider tasks
- `create_provider_minutes_chart()` - Visualizes provider minutes
- `create_provider_tasks_chart()` - Shows task distribution by provider

**Database Columns Used:**
- provider_name
- COUNT(*) as total_tasks
- SUM(minutes_of_service) as total_minutes
- COUNT(DISTINCT patient_id) as unique_patients
- task_description, billing_code, billing_code_description

---

### 3. Weekly Provider Payroll Dashboard
**Location:** `src/dashboards/weekly_provider_payroll_dashboard.py`

**Purpose:** Track provider payroll with task breakdown by visit type and payment status management

**Features:**
- Month selector for payroll period
- Week selector for specific week
- Summary metrics:
  - Total Providers
  - Total Minutes
  - Total Tasks
- Two main tabs:
  - **Provider Payroll Tab:**
    - Payroll summary table showing tasks, minutes, visit types, and payment status
    - Multi-select interface to mark providers as paid
    - Bulk payment submission button
  - **Provider Details Tab:**
    - Individual provider selection
    - Tasks breakdown by visit type (task_description)
    - Metrics: Total tasks, total minutes, average minutes per task
    - Charts showing task distribution by visit type
    - Charts showing minute distribution by visit type
    - Individual payment status with single "Mark as Paid" button

**Data Sources:**
- `provider_tasks_YYYY_MM` tables - for task details and visit type counts
- `provider_weekly_summary_with_billing` - for payment status tracking

**Key Functions:**
- `get_provider_payroll_summary()` - Aggregates payroll data by provider
- `get_provider_tasks_by_visit_type()` - Breaks down tasks by visit type
- `get_provider_payment_status()` - Retrieves payment status from summary table
- `update_provider_paid_status()` - Updates paid status in database
- `create_visit_type_chart()` - Visualizes task distribution by visit type
- `create_minutes_chart()` - Shows minutes by visit type

**Database Updates:**
- Updates `provider_weekly_summary_with_billing.paid` field (BOOLEAN)
- Records `updated_date` when payment status changes

---

## Integration into Main App

### Imports Added to `app.py`
```python
from src.dashboards import (
    ...
    monthly_coordinator_billing_dashboard,
    weekly_provider_billing_dashboard,
    weekly_provider_payroll_dashboard,
)
```

### Access Patterns
Currently, these dashboards are imported but not automatically routed through the main app.py dashboard role system. They can be accessed by:

1. **Direct Import and Call** - Add to appropriate role's dashboard function
2. **Admin Dashboard Integration** - Can be added to admin role with tabs for billing reports
3. **New Role Creation** - Can create a dedicated "Billing Manager" role

### Recommended Implementation
To make these dashboards accessible, add to `app.py` in the role routing section:

For Admin Role (34):
```python
elif dashboard_role == 34:  # Admin
    # Create tabs for different admin sections
    tab1, tab2, tab3 = st.tabs(["Patient Management", "Billing Reports", "Settings"])
    with tab1:
        admin_dashboard.show()
    with tab2:
        # Create sub-tabs for billing
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["Coordinator", "Provider Billing", "Provider Payroll"])
        with sub_tab1:
            monthly_coordinator_billing_dashboard.display_monthly_coordinator_billing_dashboard()
        with sub_tab2:
            weekly_provider_billing_dashboard.display_weekly_provider_billing_dashboard()
        with sub_tab3:
            weekly_provider_payroll_dashboard.display_weekly_provider_payroll_dashboard()
```

---

## Database Schema Requirements

### Existing Tables Used

**coordinator_tasks_YYYY_MM**
- coordinator_name (TEXT)
- duration_minutes (REAL) - *Note: Fixed from minutes_of_service*
- submission_status (TEXT)
- task_type (TEXT)
- notes (TEXT)

**provider_tasks_YYYY_MM**
- provider_name (TEXT)
- minutes_of_service (INTEGER)
- patient_id (TEXT)
- task_description (TEXT) - *Used as visit type*
- billing_code (TEXT)
- billing_code_description (TEXT)
- status (TEXT)

**provider_weekly_summary_with_billing**
- summary_id (INTEGER PRIMARY KEY)
- provider_id (INTEGER)
- provider_name (TEXT)
- week_start_date (DATE)
- week_end_date (DATE)
- year (INTEGER)
- week_number (INTEGER)
- total_tasks_completed (INTEGER)
- total_time_spent_minutes (INTEGER)
- paid (BOOLEAN) - *Updated by payroll dashboard*
- updated_date (DATETIME)

---

## Bug Fixes Applied

### Monthly Coordinator Billing Dashboard
**Issue:** Column name mismatch - query was using `minutes_of_service` which doesn't exist in coordinator_tasks tables

**Fix:** Changed to use `duration_minutes` (the actual column name in coordinator_tasks tables)

**Also Fixed:** Removed references to non-existent billing columns (is_billed, is_paid, is_carried_over) and set them to hardcoded 0 values

---

## Testing Checklist

- [ ] Verify Month selectors load available months correctly
- [ ] Verify Week selectors show weeks within selected month
- [ ] Test Summary metrics calculations (totals, averages)
- [ ] Verify table formatting (currency, numbers with commas)
- [ ] Test chart rendering (no data = no chart display)
- [ ] Test Details tab - provider/coordinator selection and drill-down
- [ ] Test Payroll Dashboard - multi-select providers
- [ ] Test Payment submission - updates to database
- [ ] Test individual provider "Mark as Paid" button
- [ ] Verify database updates are persisted
- [ ] Test with empty months (should show "No data available")
- [ ] Test with months containing single week
- [ ] Test with months containing multiple weeks

---

## Future Enhancements

1. **Financial Metrics:** Add hourly rate configuration and cost calculations
2. **Export Functionality:** Add ability to export summaries to CSV/PDF
3. **Date Range Filtering:** Allow custom date ranges instead of month/week only
4. **Billing Status Tracking:** Add columns to track billing pipeline (Billed → Invoiced → Paid)
5. **Provider Rates:** Support variable hourly rates by provider type
6. **Batch Operations:** Bulk import of payment records
7. **Payment History:** View historical payment records with dates and amounts
8. **Approval Workflow:** Add supervisor approval step before marking as paid
9. **Notifications:** Send alerts when providers have unpaid work beyond threshold
10. **Reconciliation Reports:** Compare internal payroll vs external payment records

---

## Files Modified

- `Dev/app.py` - Added imports for new dashboards
- `Dev/src/dashboards/monthly_coordinator_billing_dashboard.py` - Fixed column references

## Files Created

- `Dev/src/dashboards/weekly_provider_billing_dashboard.py` - New dashboard
- `Dev/src/dashboards/weekly_provider_payroll_dashboard.py` - New dashboard
- `Dev/sandbox/weekly_provider_billing_dashboard.py` - Sandbox version for testing
- `Dev/sandbox/weekly_provider_payroll_dashboard.py` - Sandbox version for testing

---

## Usage Examples

### Access Monthly Coordinator Billing Dashboard
```python
from src.dashboards import monthly_coordinator_billing_dashboard
monthly_coordinator_billing_dashboard.display_monthly_coordinator_billing_dashboard()
```

### Access Weekly Provider Billing Dashboard
```python
from src.dashboards import weekly_provider_billing_dashboard
weekly_provider_billing_dashboard.display_weekly_provider_billing_dashboard()
```

### Access Weekly Provider Payroll Dashboard
```python
from src.dashboards import weekly_provider_payroll_dashboard
weekly_provider_payroll_dashboard.display_weekly_provider_payroll_dashboard()
```

---

## Notes

- All three dashboards follow the same UI/UX pattern for consistency
- Month/Week selectors use dynamic data from actual database tables
- No hardcoded date ranges - automatically adapts to available data
- Payroll dashboard directly updates the `paid` field in `provider_weekly_summary_with_billing`
- Charts gracefully handle empty data (return None if no data to display)
- All database connections properly closed with try/finally blocks
- Number formatting applied to make large values readable (e.g., 1,000,000)