# POT Onboarding Workflow Implementation Plan

## Overview

Design persistent onboarding workflow using existing workflow template system with simplified MVP requirements.

## 1. POT Onboarding Workflow Template

### Workflow Template: "POT_PATIENT_ONBOARDING"

**Stage 1: Patient Registration**

- Step 1: Collect patient demographics (POT) - Day 1
- Step 2: Collect address and contact information (POT) - Day 1
- Step 3: Collect referral information (POT) - Day 1

**Stage 2: Eligibility Verification**

- Step 4: Verify insurance coverage (POT) - Day 1
- Step 5: Record eligibility status (POT) - Day 1
- Step 6: Document eligibility notes (POT) - Day 1

**Stage 3: Chart Creation**

- Step 7: Create EMed chart (checkbox - manual verification) (POT) - Day 1
- Step 8: Assign facility in system (POT) - Day 1
- Step 9: Confirm chart creation complete (POT) - Day 1

**Stage 4: Intake Processing**

- Step 10: Request medical records (POT) - Day 2
- Step 11: Collect referral documents (POT) - Day 2
- Step 12: Complete prescreen call (POT) - Day 2
- Step 13: Upload/document received materials (POT) - Day 3

**Stage 5: TV Scheduling & Handoff**

- Step 14: Schedule Initial TV with PCPM (POT) - Day 3
- Step 15: Notify patient of TV appointment (POT) - Day 3
- Step 16: Prepare handoff documentation (POT) - Day 3
- Step 17: Complete handoff to PCPM (POT) - Day 3

## 2. Database Schema Extensions

### New Table: onboarding_patients

```sql
CREATE TABLE onboarding_patients (
    onboarding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,  -- Links to patients table when created
    workflow_instance_id INTEGER, -- Links to workflow_instances

    -- Patient Registration Data (Stage 1)
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_primary TEXT,
    email TEXT,
    gender TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,

    -- Address Information
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,

    -- Insurance Information
    insurance_provider TEXT,
    policy_number TEXT,
    group_number TEXT,

    -- Referral Information
    referral_source TEXT,
    referring_provider TEXT,
    referral_date DATE,

    -- System Fields
    patient_status TEXT DEFAULT 'Active',
    facility_assignment TEXT,
    assigned_pot_user_id INTEGER,

    -- Stage Completion Tracking
    stage1_complete BOOLEAN DEFAULT FALSE,
    stage2_complete BOOLEAN DEFAULT FALSE,
    stage3_complete BOOLEAN DEFAULT FALSE,
    stage4_complete BOOLEAN DEFAULT FALSE,
    stage5_complete BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,

    FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(instance_id),
    FOREIGN KEY (assigned_pot_user_id) REFERENCES users(user_id)
);
```

### New Table: onboarding_tasks

```sql
CREATE TABLE onboarding_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    onboarding_id INTEGER NOT NULL,
    workflow_step_id INTEGER NOT NULL,

    -- Task Details
    task_name TEXT NOT NULL,
    task_stage INTEGER NOT NULL, -- 1-5 for the 5 stages
    task_order INTEGER NOT NULL,

    -- Completion Status
    status TEXT DEFAULT 'Pending', -- Pending, In Progress, Complete, Skipped
    completed_by_user_id INTEGER,
    completed_date TIMESTAMP,

    -- Task-Specific Data (JSON or specific fields)
    task_data TEXT, -- JSON for flexible data storage
    notes TEXT,

    -- MVP Checkbox Fields
    eligibility_verified BOOLEAN DEFAULT FALSE,
    emed_chart_created BOOLEAN DEFAULT FALSE,
    documents_received BOOLEAN DEFAULT FALSE,
    prescreen_completed BOOLEAN DEFAULT FALSE,
    tv_scheduled BOOLEAN DEFAULT FALSE,
    handoff_complete BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (onboarding_id) REFERENCES onboarding_patients(onboarding_id),
    FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(step_id),
    FOREIGN KEY (completed_by_user_id) REFERENCES users(user_id)
);
```

## 3. MVP Implementation Requirements

### Simplified Integrations (Checkbox-Based):

1. **EMed Chart Creation**

   - Checkbox: "EMed Chart Created" ✓
   - Notes field for chart ID or details
   - Future: API integration

2. **Insurance Verification**

   - Checkbox: "Eligibility Verified" ✓
   - Dropdown: "Eligible" / "Not Eligible" / "Pending"
   - Notes field for details
   - Future: Real-time verification API

3. **PCPM Scheduling System**

   - Use existing workflow system to assign to PCPM
   - Checkbox: "Initial TV Scheduled" ✓
   - Date/time picker for appointment
   - PCPM user assignment dropdown

4. **Document Management** (Future)

   - Checkboxes for now: "Referral Documents Received" ✓
   - "Medical Records Requested" ✓
   - "Insurance Cards Received" ✓
   - Future: File upload system

5. **Communication Tracking** (Future)
   - Notes fields for communication history
   - Checkbox: "Prescreen Call Completed" ✓
   - Future: Integrated communication log

## 4. Workflow Process Flow

### Step-by-Step Process:

1. **POT starts onboarding** → Creates workflow_instance → Creates onboarding_patients record
2. **Stage 1: Registration** → Complete patient intake form → Mark stage1_complete = TRUE
3. **Stage 2: Eligibility** → Verify insurance → Mark eligibility_verified = TRUE → Mark stage2_complete = TRUE
4. **Stage 3: Chart Creation** → Create EMed chart → Mark emed_chart_created = TRUE → Mark stage3_complete = TRUE
5. **Stage 4: Intake Processing** → Complete documentation → Mark stage4_complete = TRUE
6. **Stage 5: TV Scheduling** → Schedule with PCPM → Mark tv_scheduled = TRUE → Mark stage5_complete = TRUE
7. **Handoff Complete** → Transfer to PCPM workflow → Mark handoff_complete = TRUE

### Persistence Features:

- **Resume anywhere**: POT can stop/start process at any stage
- **Multi-day processing**: Data persists across sessions
- **Assignment tracking**: Assigned POT user can continue work
- **Progress monitoring**: Real-time progress tracking
- **Audit trail**: Complete history of all actions

## 5. Implementation Steps

1. Create POT_PATIENT_ONBOARDING workflow template
2. Create onboarding_patients and onboarding_tasks tables
3. Modify onboarding dashboard to use workflow system
4. Implement stage-by-stage form progression
5. Add checkpoint saving and resume functionality
6. Implement PCPM handoff workflow trigger

This design provides the persistent, trackable onboarding system using the existing workflow infrastructure while keeping MVP requirements simple with checkbox-based completion tracking.
