# Billing Data Status Summary

## Current Situation

### Data Import Status
✅ **Successfully Imported:**
- Coordinator Tasks (2025-12): 1,650 rows with duration_minutes
- Provider Tasks (2025-12): 20 rows (but minutes_of_service = 0)
- Coordinator Monthly Summary: 57 rows (pre-aggregated)
- Provider Weekly Summary: 298 rows (pre-aggregated)

❌ **NOT Populated:**
- Patient Monthly Billing Tables (2025-12): 0 rows - EMPTY
- Patient Monthly Billing tables exist but have no data

### Data Quality Issues

#### Coordinator Tasks (Working)
```
Coordinator Name          Tasks    Total Minutes
Antonio, Ethel              5        NULL
Atencio, Dianela          484        3,739.84
Estomo, Jan               155          781.00
Hernandez, Hector         280        1,740.50
Malhotra MD, Justin        14        NULL
```
- Some coordinators have NULL duration_minutes
- Some have valid duration_minutes
- Data is present and importable

#### Provider Tasks (PROBLEM)
```
Provider Name              Tasks    Total Minutes
Melara, Claudia              6              0
Szalas NP, Andrew           14              0
```
- Data is imported BUT minutes_of_service = 0 for all rows
- This is data quality issue from source CSV, not import problem

### Root Causes Identified

#### 1. Patient Monthly Billing Tables Are Empty
- Tables exist with correct schema (billing_id, billing_code, patient_id, total_minutes, billing_status)
- Post-import SQL processing ran but didn't populate them
- The SQL likely expects data in a different format or table structure than what was imported

#### 2. Provider Minutes Are Zero
- Provider tasks were imported successfully (20 rows)
- But all minutes_of_service values = 0
- This suggests the source CSV data has zeros, or column mapping is wrong during import

#### 3. Coordinator Tasks Missing Minutes
- Some coordinators have NULL duration_minutes (e.g., Antonio, Ethel)
- Some have valid values (e.g., Atencio, Dianela)
- Not a complete failure, but partial data quality issue

## Impact on Dashboards

### Monthly Coordinator Billing Dashboard
- ❌ **BROKEN** - Depends on patient_monthly_billing_YYYY_MM tables which are empty
- Alternatives:
  1. Aggregate directly from coordinator_tasks_YYYY_MM (would work if all had minutes)
  2. Fix patient_monthly_billing population logic
  3. Create billing codes manually

### Weekly Provider Billing Dashboard  
- ❌ **BROKEN** - Provider minutes are all zero, making billing calculations meaningless
- Also depends on real-time billing status data which doesn't exist

## Next Steps to Investigate

### Priority 1: Why Patient Monthly Billing Tables Are Empty
1. Check post_import_processing.sql INSERT statements
2. Verify source table structure matches what SQL expects
3. Check if coordinator_tasks/provider_tasks need to be joined with patients
4. Look at actual INSERT statement for patient_monthly_billing

### Priority 2: Why Provider Minutes Are Zero
1. Check source CSV (downloads/PSL*.csv) - do they have minutes data?
2. Verify column mapping in transform_production_data_v3_fixed.py
3. Check if minutes are in a different column name in source

### Priority 3: Coordinator NULL Minutes
1. Identify which source records have missing minutes
2. Check if this is data quality issue or import mapping issue
3. May need data cleanup in source

## Current Database Schema

### Patient Monthly Billing Tables (Empty)
```
Columns: billing_id, billing_code, billing_code_description, 
         patient_id, total_minutes, billing_status, created_date
Status: EXIST but EMPTY (0 rows)
```

### Coordinator Tasks (Has Data)
```
Columns: coordinator_task_id, coordinator_id, coordinator_name,
         patient_id, task_date, duration_minutes, task_type, ...
Status: POPULATED (1,650 rows in Dec 2025)
Problem: Some NULL duration_minutes values
```

### Provider Tasks (Has Data But Zero Minutes)
```
Columns: provider_task_id, provider_id, provider_name,
         patient_id, task_date, minutes_of_service, task_description, ...
Status: POPULATED (20 rows in Dec 2025)
Problem: ALL minutes_of_service = 0
```

## DISCOVERED: How Billing Should Work

### CORRECTED Approach - On-Demand Aggregation
After discussion, the proper approach is to aggregate data when loading reports, NOT pre-populate tables:

**For Monthly Coordinator Billing:**
1. When user loads the report, query `coordinator_tasks_YYYY_MM` 
2. Sum minutes by patient
3. Apply billing codes based on service type and minutes
4. Display aggregated results with billing codes
5. Export option available

**For Weekly Provider Billing:**
1. Provider tasks are imported WITH billing codes from source
2. When user loads the report, query `provider_tasks_YYYY_MM`
3. Aggregate by patient and billing code (billing_code should already be populated)
4. Display aggregated results
5. Export option available

### Why This Approach Works
- ✅ No pre-aggregation needed - real-time calculation when reports load
- ✅ Provider tasks can use codes copied from source CSV
- ✅ Coordinator billing codes applied based on minutes formula at report time
- ✅ Simpler pipeline - fewer tables to maintain
- ✅ More flexible - billing logic can be updated without re-importing
- ✅ No dependency on `patient_monthly_billing_YYYY_MM` tables

## Implementation Plan

### Step 1: Verify Provider Task Billing Codes
- Check if provider_tasks are imported with billing_code from source CSV
- If not populated, copy/map them during import from task_description

### Step 2: Create Monthly Coordinator Billing Dashboard
- Query `coordinator_tasks_YYYY_MM` on-demand when report loads
- Aggregate SUM(duration_minutes) by patient_id
- Apply billing codes based on minutes and service type
- Add export buttons (CSV download)

### Step 3: Create Weekly Provider Billing Dashboard  
- Query `provider_tasks_YYYY_MM` on-demand when report loads
- Aggregate SUM(minutes_of_service) by patient_id + billing_code
- Display with billing status and export options

### Step 4: Remove Dependency on patient_monthly_billing Tables
- These pre-aggregated tables are no longer needed for reporting
- Can keep for historical/archival purposes but not required for current workflow

## Files to Create/Modify

1. `src/dashboards/monthly_coordinator_billing_dashboard.py` - Real-time aggregation
2. `src/dashboards/weekly_provider_billing_dashboard.py` - Real-time aggregation
3. Possibly update `transform_production_data_v3_fixed.py` to ensure provider billing codes are populated