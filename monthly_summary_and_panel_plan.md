# Coordinator & Provider Monthly/Weekly Summaries and Patient Panel Enhancement

## Overview

This document tracks the implementation plan for new summary tables, billing logic, and patient panel enhancements for ZEN Medical Healthcare Management System. It provides detailed steps, table designs, and update logic to ensure robust, repeatable ETL and dashboard display.

---

## 1. Coordinator Monthly Summaries

### A. Patient Minutes Pivot Table

- **Table:** `coordinator_monthly_summary_YYYY_MM`
- **Fields:**
  - `patient_id`
  - `coordinator_id`
  - `total_minutes`
  - `month`, `year`
- **Logic:**
  - For each patient, sum minutes spent by all coordinators in `coordinator_tasks_YYYY_MM`.
  - Used for billing and performance review.

### B. Coordinator Minutes Pivot Table

- **Table:** `coordinator_minutes_YYYY_MM`
- **Fields:**
  - `coordinator_id`
  - `total_minutes`
  - `month`, `year`
- **Logic:**
  - For each coordinator, sum all minutes in `coordinator_tasks_YYYY_MM`.
  - Used for workload and billing analysis.

### C. Monthly Billing Summary

- **Table:** `coordinator_monthly_billing_YYYY_MM`
- **Fields:**
  - `coordinator_id`, `patient_id`, `billing_code`, `total_minutes`, `month`, `year`
- **Logic:**
  - Add billing codes to each row in the monthly summary.
  - Used for billing reconciliation and audit.

---

## 2. Provider Weekly Summaries

### A. Provider Weekly Tasks Table

- **Table:** `provider_weekly_summary_YYYY_WW`
- **Fields:**
  - `provider_id`, `week`, `year`, `total_tasks`
- **Logic:**
  - For each provider, count tasks per week in `provider_tasks_YYYY_MM`.
  - Used for performance monitoring and scheduling.

### B. Monthly Billing Summary

- **Table:** `provider_monthly_billing_YYYY_MM`
- **Fields:**
  - `provider_id`, `patient_id`, `billing_code`, `total_tasks`, `month`, `year`
- **Logic:**
  - Add billing codes to each row in the monthly summary.
  - Used for billing and compliance.

---

## 3. Patient Panel Enhancements

### A. Last Visit Date & Provider

- **Fields to Add:**
  - `last_visit_date`, `last_visit_provider_id` (to `patient_panel`)
- **Logic:**
  - Update when a provider completes a visit task (from `provider_tasks_YYYY_MM` or Initial TV Provider).
  - Used for care continuity and alerts.

### B. Color Coding for Last Visit

- **UI Logic:**
  - Color code patient name in panel based on last visit date:
    - Green: <2 weeks
    - Yellow: >2 weeks
    - Orange: >4 weeks
    - Red: >8 weeks
  - Use pastel/muted colors for professional appearance.
  - Used for quick visual triage and follow-up prioritization.

---

## 5. Implementation Steps

### A. SQL Table Creation

- ✅ Design and create summary tables for September 2025:
  - `coordinator_monthly_summary_2025_09` - Patient minutes per coordinator
  - `coordinator_minutes_2025_09` - Total minutes per coordinator
  - `provider_weekly_summary_2025_35` - Weekly tasks per provider
- ✅ Add last_visit_date, last_visit_provider_id, last_visit_provider_name to patient_panel

### B. ETL Logic

- ✅ Write SQL scripts to populate summaries from monthly/weekly task tables
- ✅ Update patient panel ETL to set last visit date/provider from provider tasks
- ✅ Include billing codes in all summary tables

### C. Patient Panel Logic

- ✅ Update ETL to set last visit date/provider in patient_panel
- ⏳ Update dashboard UI to apply color coding based on last visit date

### D. Display

- ⏳ Add dashboard tabs/views for:
  - Coordinator monthly summary (patient minutes, coordinator minutes, billing)
  - Provider weekly summary (tasks, billing)
  - Enhanced patient panel (last visit, color coding)

### E. Automation Script

- ✅ Create `create_and_populate_summaries.ps1` to run all SQL scripts in sequence

### C. Patient Panel Logic

- Update ETL to set last visit date/provider in `patient_panel`.
- Update dashboard UI to apply color coding.

### D. Display

- Add dashboard tabs/views for:
  - Coordinator monthly summary (patient minutes, coordinator minutes, billing)
  - Provider weekly summary (tasks, billing)
  - Enhanced patient panel (last visit, color coding)

---

## 6. Tracking & Execution Checklist

- ✅ Design SQL schemas for new summary tables
- ✅ Write SQL scripts for monthly/weekly aggregation
- ✅ Update ETL scripts to run these after each import
- ✅ Update patient panel ETL and dashboard UI for last visit logic and color coding
- ⏳ Add dashboard views for all new tables
- ⏳ Validate with test data and real workflow
- ⏳ Document any issues, edge cases, or improvements

---

## Notes

- All table and field names should follow existing naming conventions for consistency.
- Billing codes must be validated for compliance before use in summaries.
- Color coding should use professional, muted colors (no emojis).
- All changes should be tested in sandbox before production deployment.

## 7. Implementation Summary

### ✅ Completed Tasks

1. **Database Tables Created:**

   - `coordinator_monthly_summary_2025_09` - Patient minutes per coordinator with billing codes
   - `coordinator_minutes_2025_09` - Total minutes per coordinator with billing codes
   - `provider_weekly_summary_2025_35` - Weekly tasks per provider with billing codes
   - Added `last_visit_date`, `last_visit_provider_id`, `last_visit_provider_name` to `patient_panel`

2. **ETL Scripts Created:**

   - `create_summary_tables_2025_09.sql` - Creates all summary tables
   - `populate_coordinator_monthly_summary_2025_09.sql` - Populates patient minutes summary
   - `populate_coordinator_minutes_2025_09.sql` - Populates coordinator total minutes
   - `populate_provider_weekly_summary_2025_35.sql` - Populates provider weekly tasks
   - `update_patient_panel_last_visit.sql` - Updates patient panel with last visit info

3. **Automation Script:**

   - `create_and_populate_summaries.ps1` - Runs all SQL scripts in sequence

4. **Data Population:**

   - Coordinator monthly summary: 1,091 records populated
   - Coordinator minutes summary: 6 coordinators with data
   - Provider weekly summary: 4 providers with data for week 35
   - Patient panel: Last visit information updated

5. **Viewer Application:**
   - `summary_tables_viewer.py` - Streamlit app to display all summary tables

### 🔄 Next Steps

1. **Dashboard Integration:**

   - Integrate summary table displays into main care_provider_dashboard_enhanced.py
   - Add patient panel color coding based on last visit date

2. **Color Coding Implementation:**

   - Update patient panel display to show colored patient names:
     - Green: < 2 weeks since last visit
     - Yellow: 2-4 weeks
     - Orange: 4-8 weeks
     - Red: > 8 weeks

3. **Workflow Integration:**

   - Update provider task completion to automatically update patient_panel last visit
   - Ensure monthly/weekly summary generation runs after each data import

4. **Testing & Validation:**
   - Test with real workflow data
   - Validate billing code assignments
   - Verify date calculations and color coding logic

### 📋 Files Created

**SQL Scripts:**

- `src/sql/create_summary_tables_2025_09.sql`
- `src/sql/populate_coordinator_monthly_summary_2025_09.sql`
- `src/sql/populate_coordinator_minutes_2025_09.sql`
- `src/sql/populate_provider_weekly_summary_2025_35.sql`
- `src/sql/update_patient_panel_last_visit.sql`

**Automation:**

- `scripts/create_and_populate_summaries.ps1`

**Viewer:**

- `summary_tables_viewer.py`

**Documentation:**

- Updated `monthly_summary_and_panel_plan.md`
