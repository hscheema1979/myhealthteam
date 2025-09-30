# ZEN Medical System Enhancement Implementation Guide

**Priority:** P0 Issues and Feature Requests  
**Date:** September 22, 2025  
**Status:** Implementation Required

## Overview

This document outlines the implementation requirements for enhancing the Care Coordinator, Care Provider, and Onboarding workflows in the ZEN Medical Healthcare Management System.

---

## P0 - Care Coordinators / CC / CM / LC Enhancements

### 1. Patient Panel Minutes Tracking (Weekly View)

**Requirement:** Show minutes logged per week per patient for CC dashboard

**Implementation:**

- **File to modify:** `src/dashboards/care_coordinator_dashboard_enhanced.py`
- **Database function needed:** `get_coordinator_weekly_patient_minutes(coordinator_id, week_range)`
- **UI component:** Add weekly time tracking table to patient panel tab

**Technical Details:**

```python
# Add to src/database.py
def get_coordinator_weekly_patient_minutes(coordinator_id, weeks_back=4):
    """Get minutes logged per patient per week for coordinator"""
    query = """
        SELECT
            ct.patient_id,
            p.first_name || ' ' || p.last_name as patient_name,
            strftime('%Y-%W', ct.task_date) as week,
            SUM(ct.duration_minutes) as total_minutes
        FROM coordinator_tasks ct
        JOIN patients p ON ct.patient_id = p.patient_id
        WHERE ct.coordinator_id = ?
        AND ct.task_date >= date('now', '-' || ? || ' days')
        GROUP BY ct.patient_id, strftime('%Y-%W', ct.task_date)
        ORDER BY week DESC, patient_name
    """
```

### 2. Phone Reviews Tab

**Requirement:** New tab for coordinators to log phone reviews with provider information

**Implementation:**

- **File to modify:** `src/dashboards/care_coordinator_dashboard_enhanced.py`
- **New UI tab:** "Phone Reviews"
- **Task configuration:** Task_ID = "19|Communication|Communication: Phone"

**Form Fields:**

```python
# Phone Review Form
{
    'task_date': st.date_input("Today's Date"),
    'provider_name': st.selectbox("Provider Name", get_providers_list()),
    'task_id': "19|Communication|Communication: Phone",  # Fixed value
    'duration_minutes': st.number_input("Duration (minutes)"),
    'notes': st.text_area("Review Notes")
}
```

### 3. Workflow Management Section

**Requirement:** Add workflow controls under patient table

**Implementation:**

- **New component:** Workflow management section
- **Actions:** Kick off, Resume, Manage workflows
- **Field:** workflow_id dropdown for daily tasks

**UI Layout:**

```python
# Under patient table
st.subheader("Workflow Management")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Kick Off Workflow"):
        # Workflow initiation logic
with col2:
    if st.button("Resume Workflow"):
        # Resume workflow logic
with col3:
    workflow_id = st.selectbox("Workflow ID", get_available_workflows())
```

### 4. Patient Service Minutes Table (CM/LC)

**Requirement:** Show minutes per patient per month using dashboard_monthly_summary view

**Implementation:**

- **Data source:** `coordinator_monthly_summary` table
- **View for:** CM (role_id=40) and LC (role_id=37) roles
- **Display:** Minutes per patient per month breakdown

---

## P0 - Care Providers / CP / CPM Enhancements

### 1. Provider Patient Panel Updates

**Requirement:** Remove region columns, add last visited, facility, assigned care coordinator

**Implementation:**

- **File to modify:** `src/dashboards/care_provider_dashboard_enhanced.py`
- **Database updates needed:** Add new columns to patient view queries

**New Columns:**

```sql
-- Update patient panel query
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    p.last_visit_date,  -- NEW
    p.facility,         -- NEW
    cc.coordinator_name as assigned_coordinator  -- NEW
FROM patients p
LEFT JOIN user_patient_assignments upa ON p.patient_id = upa.patient_id
LEFT JOIN coordinators cc ON p.assigned_coordinator_id = cc.coordinator_id
WHERE upa.user_id = ?
```

### 2. PSL Calendar Month Subdivision

**Requirement:** Pre-load panel patients by calendar month with simplified selection

**Implementation:**

- **New PSL interface:** Monthly calendar view
- **Pre-loaded data:** All panel patients by month
- **Selection fields:** DOS month, Visit type, Patient type

**UI Design:**

```python
# PSL Monthly View
st.subheader("Patient Service Log - Monthly View")
selected_month = st.selectbox("DOS Month", get_calendar_months())
visit_type = st.selectbox("Visit Type", ["Home", "Tele", "Office"])
patient_type = st.selectbox("Patient Type", ["New", "Established"])

# Pre-loaded patient panel for selected month
patients_for_month = get_panel_patients_for_month(provider_id, selected_month)
```

### 3. CPM Monthly Summary (Current Month)

**Requirement:** Show current month minutes using dashboard_monthly_summary

**Implementation:**

- **Component:** Add to CPM management tab
- **Data source:** `provider_monthly_summary` table
- **Filter:** Current month only

---

## Database Schema Enhancements

### New Patient Table Columns

**Onboarding Data (Stage 1):**

```sql
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_name TEXT;
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_phone TEXT;
ALTER TABLE onboarding_patients ADD COLUMN appointment_contact_email TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_name TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_phone TEXT;
ALTER TABLE onboarding_patients ADD COLUMN medical_contact_email TEXT;
```

**Onboarding Data (Stage 2):**

```sql
ALTER TABLE onboarding_patients ADD COLUMN primary_care_provider TEXT;
ALTER TABLE onboarding_patients ADD COLUMN pcp_last_seen DATE;
ALTER TABLE onboarding_patients ADD COLUMN active_specialist TEXT;
ALTER TABLE onboarding_patients ADD COLUMN specialist_last_seen DATE;
ALTER TABLE onboarding_patients ADD COLUMN chronic_conditions_onboarding TEXT;

-- Mental Health Checkboxes (Stage 2)
ALTER TABLE onboarding_patients ADD COLUMN mh_schizophrenia BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_depression BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_anxiety BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_stress BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_adhd BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_bipolar BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN mh_suicidal BOOLEAN DEFAULT FALSE;
```

**Provider Clinical Data:**

```sql
ALTER TABLE patients ADD COLUMN er_count_1yr INTEGER;
ALTER TABLE patients ADD COLUMN hospitalization_count_1yr INTEGER;
ALTER TABLE patients ADD COLUMN clinical_biometric TEXT;
ALTER TABLE patients ADD COLUMN chronic_conditions_provider TEXT;
ALTER TABLE patients ADD COLUMN cancer_history TEXT;
ALTER TABLE patients ADD COLUMN subjective_risk_level INTEGER; -- 1-6 scale

-- Provider Mental Health Checkboxes
ALTER TABLE patients ADD COLUMN provider_mh_schizophrenia BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_depression BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_anxiety BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_stress BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_adhd BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_bipolar BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN provider_mh_suicidal BOOLEAN DEFAULT FALSE;

-- Additional Clinical Fields
ALTER TABLE patients ADD COLUMN active_specialists TEXT;
ALTER TABLE patients ADD COLUMN code_status TEXT;
ALTER TABLE patients ADD COLUMN cognitive_function TEXT;
ALTER TABLE patients ADD COLUMN functional_status TEXT;
ALTER TABLE patients ADD COLUMN goals_of_care TEXT;
ALTER TABLE patients ADD COLUMN active_concerns TEXT;
```

### Subjective Risk Level Checkboxes

**Implementation in Provider Dashboard:**

```python
st.subheader("Subjective Risk Level Assessment")
risk_level = st.selectbox("Risk Level", [
    "Level 6 - In danger of dying or institutionalized within 1 yr",
    "Level 5 - Complications of chronic conditions or high risk social determinants",
    "Level 4 - Unstable chronic conditions but no complications",
    "Level 3 - Stable chronic conditions",
    "Level 2 - Healthy, some out of range biometrics",
    "Level 1 - Healthy, in range biometrics"
])
```

---

## Implementation Priority Order

### Phase 1: Immediate (P0)

1. CC Patient Panel weekly minutes tracking
2. Provider Patient Panel column updates
3. Database schema additions for new fields

### Phase 2: High Priority

1. Phone Reviews tab for coordinators
2. PSL monthly calendar subdivision
3. Workflow management section

### Phase 3: Data Collection Enhancement

1. Onboarding form updates (Stage 1 & 2)
2. Provider clinical data collection forms
3. Mental health condition checkboxes

### Phase 4: Future Implementation

1. Objective risk score calculations
2. Claims integration
3. RAF score integration

---

## Technical Notes

### File Modifications Required

**Dashboard Files:**

- `src/dashboards/care_coordinator_dashboard_enhanced.py`
- `src/dashboards/care_provider_dashboard_enhanced.py`
- `src/dashboards/onboarding_dashboard.py`

**Database Functions:**

- Add new functions to `src/database.py` for weekly/monthly summaries
- Update patient query functions for new columns

**UI Components:**

- Mental health checkbox components
- Risk level assessment forms
- Weekly/monthly time tracking tables

### Database Migration Script Needed

Create `scripts/5_schema_enhancement.ps1` to handle:

- Adding new columns to existing tables
- Creating indexes for performance
- Data migration for existing records

---

## Testing Requirements

1. **Unit Tests:** New database functions
2. **Integration Tests:** Dashboard tab functionality
3. **User Acceptance Tests:** Coordinator and Provider workflows
4. **Performance Tests:** Monthly summary queries with new data

---

## Notes for AI Development

When implementing these features:

1. **Follow existing patterns** from copilot-instructions.md
2. **Use professional UI standards** - no emojis, consistent styling
3. **Implement proper error handling** with try/finally blocks
4. **Maintain role-based access** - check user_role_ids before showing features
5. **Add database connection management** - always close connections
6. **Use existing components** from `src/utils/performance_components.py`

This implementation guide provides the roadmap for resolving all P0 issues while maintaining system architecture integrity.
