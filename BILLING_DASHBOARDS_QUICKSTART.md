# Billing Dashboards - Quick Start Guide

## Overview
Three new billing dashboards have been created to track coordinator and provider billing workflows:

1. **Monthly Coordinator Billing Dashboard** - Track coordinator work by month/week
2. **Weekly Provider Billing Dashboard** - Track provider work by month/week
3. **Weekly Provider Payroll Dashboard** - Track provider payroll and mark payments

## How to Access

### Option 1: Direct Access (For Testing)
Run these commands in your Python terminal or Streamlit app:

```python
# Monthly Coordinator Billing
from src.dashboards import monthly_coordinator_billing_dashboard
monthly_coordinator_billing_dashboard.display_monthly_coordinator_billing_dashboard()

# Weekly Provider Billing
from src.dashboards import weekly_provider_billing_dashboard
weekly_provider_billing_dashboard.display_weekly_provider_billing_dashboard()

# Weekly Provider Payroll
from src.dashboards import weekly_provider_payroll_dashboard
weekly_provider_payroll_dashboard.display_weekly_provider_payroll_dashboard()
```

### Option 2: Add to Admin Dashboard (Recommended)
Edit `app.py` and find the role routing section (around line 545-565):

```python
elif dashboard_role == 34:  # Admin
    # Add tabs for billing reports
    tab1, tab2 = st.tabs(["Dashboard", "Billing Reports"])
    with tab1:
        admin_dashboard.show()
    with tab2:
        # Sub-tabs for different billing reports
        billing_tab1, billing_tab2, billing_tab3 = st.tabs([
            "Coordinator Billing", 
            "Provider Billing", 
            "Provider Payroll"
        ])
        with billing_tab1:
            monthly_coordinator_billing_dashboard.display_monthly_coordinator_billing_dashboard()
        with billing_tab2:
            weekly_provider_billing_dashboard.display_weekly_provider_billing_dashboard()
        with billing_tab3:
            weekly_provider_payroll_dashboard.display_weekly_provider_payroll_dashboard()
```

### Option 3: Create Dedicated Billing Manager Role
1. Create a new role in the database (role_id = 41, name = "Billing Manager")
2. Add role routing to app.py:

```python
elif dashboard_role == 41:  # Billing Manager
    st.title("Billing Management Portal")
    
    tab1, tab2, tab3 = st.tabs([
        "Coordinator Billing", 
        "Provider Billing", 
        "Provider Payroll"
    ])
    
    with tab1:
        monthly_coordinator_billing_dashboard.display_monthly_coordinator_billing_dashboard()
    with tab2:
        weekly_provider_billing_dashboard.display_weekly_provider_billing_dashboard()
    with tab3:
        weekly_provider_payroll_dashboard.display_weekly_provider_payroll_dashboard()
```

## Dashboard Features

### 1. Monthly Coordinator Billing Dashboard
**File:** `src/dashboards/monthly_coordinator_billing_dashboard.py`

**Workflow:**
1. Select a month from dropdown
2. (Optional) Select a specific week within that month
3. View summary metrics at the top
4. Browse three tabs:
   - **Summary:** Table of all coordinators with tasks, minutes, etc.
   - **Charts:** Visual representations of billing data
   - **Details:** Drill down into individual coordinator's tasks

**Key Data:**
- Total coordinators active in period
- Total minutes of service
- Total tasks completed
- Task breakdown by coordinator

### 2. Weekly Provider Billing Dashboard
**File:** `src/dashboards/weekly_provider_billing_dashboard.py`

**Workflow:**
1. Select a month from dropdown
2. Select a specific week within that month
3. View summary metrics (providers, minutes, tasks, avg minutes/task)
4. Browse three tabs:
   - **Summary:** Provider billing table with formatted numbers
   - **Charts:** Top 10 providers by minutes and task count
   - **Details:** Individual provider task listing

**Key Data:**
- Total providers active in period
- Total minutes of service
- Total tasks completed
- Unique patients seen per provider

### 3. Weekly Provider Payroll Dashboard
**File:** `src/dashboards/weekly_provider_payroll_dashboard.py`

**Workflow for Marking Providers as Paid:**

1. Select month and week
2. Navigate to "Provider Payroll" tab
3. View payroll summary table showing:
   - Provider name
   - Number of tasks
   - Total minutes
   - Visit types count
   - Payment status (Paid/Unpaid)
4. Multi-select providers you want to mark as paid
5. Click "Submit Payment for Selected Providers"
6. See success message

**Workflow for Reviewing Provider Details:**

1. Navigate to "Provider Details" tab
2. Select a provider from dropdown
3. View their tasks breakdown by visit type
4. See charts showing:
   - Task distribution by visit type
   - Minutes distribution by visit type
5. At bottom, see individual payment status with "Mark as Paid" button
6. Click button to mark this provider as paid for the week

## Data Requirements

### Tables Used
- `coordinator_tasks_YYYY_MM` - Coordinator task records
- `provider_tasks_YYYY_MM` - Provider task records
- `provider_weekly_summary_with_billing` - Provider weekly summaries (used for payment tracking)

### Important Note
The dashboards dynamically find available months and weeks based on actual data in these tables. If no data exists for a period, the dashboard will show "No data available."

## Common Tasks

### View Coordinator Billing for December 2025
1. Open Monthly Coordinator Billing Dashboard
2. Select "December 2025" from month dropdown
3. (Optional) Select specific week or leave as "All Weeks"
4. View summary metrics and tables
5. Click on coordinator name to see their individual tasks

### Mark Provider as Paid for Week of Dec 1-7
1. Open Weekly Provider Payroll Dashboard
2. Select "December 2025"
3. Select "Week of 2025-12-01 to 2025-12-07"
4. Go to "Provider Payroll" tab
5. Check the provider name(s) you paid
6. Click "Submit Payment for Selected Providers"
7. See success confirmation

### Compare Provider Hours Week-over-Week
1. Open Weekly Provider Billing Dashboard
2. Select first month/week, note the minutes
3. Change to next week/month
4. Compare totals
5. Use Charts tab to visualize trends

## Troubleshooting

### "No data available for selected period"
- The selected month/week has no data in the database
- Try selecting a different month
- Check if data was imported correctly

### "Month selector shows no options"
- No coordinator/provider tasks have been imported to the database yet
- Import data using the data entry dashboards first

### Payment status not updating
- Ensure you clicked "Submit Payment for Selected Providers"
- Check database connection is active
- Verify `provider_weekly_summary_with_billing` table exists

### Charts not displaying
- This is normal when there's no data
- Charts will display once data is available

## Performance Notes

- Large months (1000+ tasks) may take 2-3 seconds to load
- Charts render using Plotly and are interactive (hover for details)
- All queries are optimized with proper WHERE clauses
- Database connections are properly closed to prevent leaks

## Next Steps

1. **Test the dashboards** by visiting them through the admin panel
2. **Import sample data** if not already done
3. **Create accounts** for users who need access (Billing Managers, Coordinators, Admins)
4. **Configure hourly rates** if cost calculations are needed (future enhancement)
5. **Set up recurring reports** if automated exports are needed (future enhancement)

## Support

For issues or questions:
1. Check the BILLING_DASHBOARDS_README.md for detailed documentation
2. Verify database schema matches requirements
3. Check app.py imports are in place
4. Review error messages in Streamlit console
