# HHC View Template - Quick Start Guide

## What is the HHC View Template?

The HHC View Template is a new admin dashboard tab that displays all active patients in a table format, perfect for daily review and export to Google Sheets.

## How to Access

1. **Login** to the Zen Medicine application
2. **Navigate** to the Admin Dashboard
3. **Look for the tabs** at the top of the page
4. **Click "HHC View Template"** tab (appears after "Billing Report")

**Note**: This tab is only visible to:
- Justin (user_id: 18)
- Harpreet (user_id: 12)

## What You'll See

### Summary Metrics (Top of Tab)
Four quick stat boxes showing:
- **Total Active Patients** - How many patients are in the active status
- **Assigned to Coordinator** - Patients with coordinator assignments
- **With Provider** - Patients with provider assignments
- **Unassigned** - Patients waiting for coordinator assignment

### Patient Data Table
A comprehensive table with all active patients showing:

#### Key Columns (Displayed First)
- **Pt Status** - Current patient status
- **Name** - Full patient name
- **LAST FIRST DOB** - Combined name and DOB format
- **Last Visit** - Date of most recent visit
- **Contact** - Primary phone number
- **City** - Patient's city
- **Fac** - Facility name
- **Prov** - Assigned provider name
- **Care Coordinator** - Assigned coordinator name
- **Insurance Eligibility** - Primary insurance
- **Risk** - Risk level assessment
- **General Notes** - Notes about patient

#### Additional Columns (Available via Scroll)
- Last (Last Name)
- First (First Name)
- DOB
- Last Visit Type
- Initial TV
- Initial TV Date
- Initial TV Notes
- Initial HV Date
- Reg Prov (Registered Provider)
- Prescreen Call
- Notes
- Labs
- Imaging
- Medical POC
- Appt POC

## How to Use

### Sorting Data
Click any column header to sort by that column (ascending/descending)

### Filtering Data
Use the search box at the top right of the table to filter by any column value

### Scrolling
- **Horizontal**: Scroll right to see additional columns
- **Vertical**: Scroll down to see all patients

### Refreshing Data
Click the **🔄 Refresh Data** button to reload the latest information from the database

### Downloading as CSV
1. Click the **📥 Download as CSV** button
2. Your browser will download a file named `hhc_patients_YYYYMMDD.csv`
3. The file contains all patient data from the current view

## Common Tasks

### Export Today's Patient List
1. Go to HHC View Template tab
2. Click **📥 Download as CSV**
3. File will be named with today's date: `hhc_patients_20250115.csv`
4. Upload to Google Sheets or your preferred system

### Find Unassigned Patients
1. Click the "Assigned" column header to sort
2. All "No" values will group together
3. These patients need coordinator assignment

### Find Patients with High Risk
1. Scroll right to find the "Risk" column
2. Click the Risk column header to sort
3. High-risk patients will be grouped together

### See All Patients Without a Provider
1. Click the "Prov" (Provider) column header
2. "Unassigned" entries will group together
3. These patients need provider assignment

### Review Patients by City
1. Click the "City" column header to sort
2. Patients are grouped by location
3. Useful for coordinating regional visits

## Tips & Tricks

💡 **Pro Tips:**
- Use your browser's Find function (Ctrl+F) to search for specific patient names
- Download the CSV at the end of each day to maintain a backup
- The CSV can be directly imported into Google Sheets
- Column headers are sticky - they stay visible when scrolling down
- Use the Risk column to prioritize high-acuity patients
- The "Assigned" column shows coordinator assignment status at a glance

## Troubleshooting

### I Don't See the HHC View Template Tab
- **Check Access**: Only Justin and Harpreet can see this tab
- **Refresh**: Try refreshing your browser (F5)
- **Login Again**: Log out and log back in

### The Table is Empty
- **No Active Patients**: Your system has no active patients (check patient statuses)
- **Refresh**: Click the 🔄 Refresh Data button
- **Database Connection**: Check if the database is accessible

### CSV Download Isn't Working
- **Check Browser**: Make sure pop-ups aren't blocked
- **Try Different Browser**: Try Chrome, Firefox, or Edge
- **Check Storage**: Make sure you have disk space available

### Data Looks Incomplete
- Scroll right to see all columns
- Some fields may be empty for certain patients (NULL values appear blank)
- Click Refresh Data to ensure you have the latest version

## Data Refresh Schedule

The HHC View Template displays data **live from the database**:
- Click Refresh Data to get the absolute latest information
- Data automatically updates when changes are made in other parts of the system
- No scheduled refresh needed - you control when to update

## Questions?

If you need help or have questions about the HHC View Template:
1. Check the tooltips (hover over info icons)
2. Contact your system administrator
3. Refer to the main User Guide in the Help section

---

**Last Updated**: January 2025
**Version**: 1.0