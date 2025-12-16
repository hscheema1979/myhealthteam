# ZMO Tab - Quick Start Guide

## Overview

The "For Testing" tab has been renamed to **ZMO** and enhanced with powerful search and filtering capabilities for patient data management.

## Tab Location
- **Admin Dashboard** → **ZMO** tab (8th tab)
- **Purpose**: Patient Data Management (patient_panel + patients combined, fully editable)
- **Access**: All Admin users

## What You'll See

```
ZMO: Patient Data Management
├── Search & Filter
│   ├── Search patients by name or ID
│   └── Clear search button
├── Column Management
│   ├── Search columns input
│   ├── Show Only checkbox
│   └── Reset columns button
├── Show/Hide Columns (expandable)
│   └── Checkbox list of all columns
└── Data Editor (Editable Table)
    └── Combined patient_panel + patients data
```

## How to Use

### Task 1: Find a Specific Patient

1. Go to **Search patients by name or ID** field
2. Type patient name or ID (e.g., "John Smith" or "12345")
3. Table instantly updates to show matching patients
4. See result count (e.g., "Found 1 patient matching search")
5. Click **Clear search** button to restore full table

**Example Searches:**
- "John Smith" → Find all Johns or Smiths
- "12345" → Find by patient ID or MRN
- "Active" → Find active patients
- "2024-01" → Find records from January 2024

### Task 2: Find Specific Columns (Checkbox Method)

1. Go to **Search columns** field
2. Type column name or part (e.g., "initial", "phone", "status")
3. Click **Show/Hide Columns** expander
4. See only columns matching your search
5. Check/uncheck individual columns to show/hide
6. Column selection saves automatically
7. Click **Reset columns to default** to restore all

**Example Column Searches:**
- "name" → first_name, last_name, full_name, patient_name
- "phone" → phone_primary, phone_secondary, medical_contact_phone
- "initial" → initial_tv_date, initial_tv_notes, initial_tv_provider
- "status" → status, code_status, billing_status
- "date" → All date-related fields

### Task 3: Show ONLY Specific Columns (Quick Method)

1. Go to **Search columns** field
2. Type what you're looking for (e.g., "phone")
3. **Check the "Show Only" checkbox**
4. Instantly see ONLY columns matching that term!
5. All other columns hidden for focused viewing
6. Perfect for laser-focused analysis
7. Uncheck **Show Only** to restore all columns
8. Or click **Reset columns to default**

**Quick Example:**
- Search: "initial" + Check "Show Only" → See only Initial TV related fields
- Search: "contact" + Check "Show Only" → See only contact information
- Search: "workflow" + Check "Show Only" → See only workflow-related data

### Task 4: Edit Patient Data

1. Click on any cell in the table to edit
2. Type new value
3. Press Tab to move to next cell
4. Add new rows using the "+" button
5. Delete rows using the "×" button
6. Changes are live in the editor
7. Column preferences persist across sessions

## Key Features

✅ **Combined Data Source**
- patient_panel table + patients table merged
- No duplicate columns
- All patient data in one place

✅ **Patient Search**
- Search across ALL columns simultaneously
- Case-insensitive matching
- Partial word matches work
- Real-time filtering

✅ **Column Search**
- Search by column name
- Two modes: Individual checkboxes or "Show Only"
- Partial name matching (e.g., "tv" finds all _tv_ fields)

✅ **"Show Only" Feature**
- Instantly hide all non-matching columns
- One-click to display only relevant data
- Perfect for focused review
- Easy to restore with Reset button

✅ **Editable Table**
- Click to edit any cell
- Add/remove rows dynamically
- Live editing with immediate feedback
- Changes visible in real-time

✅ **Configuration Persistence**
- Your column selections save automatically
- Restored when you revisit the tab
- Stored in for_testing_col_config.json

## Workflow Example

**Scenario: Review Initial TV data for John Smith**

1. **Search for patient**
   - Patient Search: "John Smith"
   - Result: 1 patient found

2. **Filter to Initial TV columns**
   - Column Search: "initial"
   - Check "Show Only"
   - Result: Shows only initial_tv_date, initial_tv_notes, initial_tv_provider

3. **Review data**
   - See focused view of Initial TV information
   - Can edit if needed
   - All other columns hidden for clarity

4. **Restore view**
   - Uncheck "Show Only" to restore columns
   - OR Click "Reset columns to default"
   - OR Click "Clear search" to see all patients

## Tips & Tricks

1. Use **"Show Only"** for laser-focused viewing of specific data types
2. Searches are **case-insensitive** (type lowercase)
3. **Partial searches work** (e.g., "tv" finds all _tv_ fields)
4. Click **"Clear search"** button to reset patient filter
5. Click **"Reset columns to default"** to restore all columns
6. Column selections **persist across sessions**
7. First 200 rows shown (scroll to see more)
8. **All columns are searchable** simultaneously
9. No data saved when editing (test/view mode only)
10. **Combine patient search + column filter** for maximum precision

## After Streamlit Restart

1. Go to: **Admin Dashboard → ZMO** tab
2. See the new **"Search & Filter"** section
3. See the **"Column Management"** section with search and "Show Only"
4. Start searching for patients and columns!

## Quick Command Reference

| Want to... | Do this |
|-----------|---------|
| Find patient John Smith | Type "John Smith" in patient search |
| See only Initial TV columns | Type "initial" in column search + check "Show Only" |
| View all phone fields | Type "phone" in column search + check "Show Only" |
| Show/hide specific columns | Use Column Search then check/uncheck in expander |
| Edit patient data | Click cell → type → Tab to move |
| Add a new row | Click "+" button at bottom of table |
| Delete a row | Click "×" button on the row |
| Reset everything | Click "Reset columns to default" button |
| See all patients again | Click "Clear search" button |
| Restore column choices | Column selections auto-save to config file |

---

**Status**: ✅ Ready for immediate use after Streamlit restart
**Access**: All Admin users
**Data**: Combined patient_panel + patients (600+ records)
**Editable**: Yes (test/view mode)