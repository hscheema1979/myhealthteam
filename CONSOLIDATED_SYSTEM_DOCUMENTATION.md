# ZEN Medical Healthcare Management System - Consolidated Documentation


**Document Version:** 2.4
**Last Updated:** December 17, 2025

**Author:** Engineering Team  
**Purpose:** Comprehensive system documentation reflecting Phase 2 implementation with billing/payroll workflows and actual dashboard architecture

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Role-Based System Structure](#role-based-system-structure)
4. [Dashboard Specifications](#dashboard-specifications)
5. [Billing and Payroll Workflows](#billing-and-payroll-workflows)
6. [Database Design and Data Model](#database-design-and-data-model)
7. [Technical Implementation](#technical-implementation)
8. [Deployment and Operations](#deployment-and-operations)
9. [Security and Compliance](#security-and-compliance)
10. [Patient Visit Tracking System](#patient-visit-tracking-system)
11. [Database Synchronization (DB-Sync)](#database-synchronization-db-sync)
12. [Analytics and Metrics](#analytics-and-metrics)
13. [December 2025 System Improvements](#december-2025-system-improvements)

---

## Executive Summary

The ZEN Medical Healthcare Management System is a Streamlit-based healthcare management platform implementing Phase 2 features focused on **billing and payroll workflows**. The system manages patient care coordination, provider task tracking, and dual billing/payroll pipelines for healthcare operations.

### Key System Features
- **Role-Based Access Control (RBAC):** 8 distinct roles (33=Provider, 34=Admin, 35=Onboarding, 36=Coordinator, 37=LC, 38=CPM, 39=DataEntry, 40=CM)
- **Dual Billing/Payroll System:** Separate workflows for Medicare billing (3rd party) and internal payroll
- **Weekly Provider Billing Dashboard:** Track provider task billing through insurance reimbursement lifecycle
- **Monthly Coordinator Billing Dashboard:** Aggregate coordinator minutes by patient with auto billing code assignment
- **Weekly Provider Payroll Dashboard:** Track provider compensation with paid_by_zen indicators to prevent double-payment
- **Admin Dashboard Tabs:** 8+ specialized management interfaces (User Roles, ZMO, HHC, Workflow Reassignment, etc.)
- **Database-Driven Workflows:** SQLite production.db with 40+ normalized tables for data integrity

### Core Architecture Principles
- **Separation of Concerns:** Billing (Medicare) vs Payroll (Internal Compensation) are distinct workflows
- **Workflow-Driven Design:** Status tables (provider_task_billing_status, provider_weekly_payroll_status) vs raw task tables
- **Role-Based Filtering:** All dashboards filter data by user_role_ids with multi-role support
- **Professional UI Standards:** No emojis in healthcare interfaces, consistent styling via ui_style_config.py

---

## System Architecture Overview

### Technology Stack
- **Frontend:** Streamlit (Python-based responsive web app)
- **Database:** SQLite (production.db) with 40+ normalized tables
- **Authentication:** Session-based with role validation and multi-role support
- **Data Processing:** Pandas for aggregation and analysis
- **Visualization:** Plotly for healthcare-appropriate charts
- **Configuration:** Centralized ui_style_config.py for professional styling
- **Deployment:** VPS with git-based code management and Streamlit server

### System Components

#### 1. Application Layer (app.py)
- Main entry point handling authentication and role-based routing
- Route logic: role_id determines primary dashboard displayed
- Session state management for user context

#### 2. Dashboard Layer (src/dashboards/)
- `admin_dashboard.py` - 8+ tabs for administrative management
- `care_provider_dashboard_enhanced.py` - Provider workflow and tasks
- `care_coordinator_dashboard_enhanced.py` - Coordinator workflow
- `weekly_provider_billing_dashboard.py` - Weekly billing (P00) workflow
- `weekly_provider_payroll_dashboard.py` - Weekly payroll tracking
- `monthly_coordinator_billing_dashboard.py` - Monthly coordinator aggregation
- `onboarding_dashboard.py` - Patient intake workflow
- `data_entry_dashboard.py` - Bulk data entry interface

#### 3. Database Layer (src/database.py)
- SQLite connection management with row_factory
- Prepared statements for security
- Role-based data filtering functions
- Transaction management for workflow updates

#### 4. Utilities Layer (src/utils/)
- `performance_components.py` - Shared performance metric displays
- `chart_components.py` - Healthcare-appropriate visualizations
- `ui_style_config.py` - Professional UI standards and text styling

#### 5. Configuration Layer (src/config/)
- `ui_style_config.py` - Professional indicators, headers, labels
- No emoji usage, text-based status indicators

### Database Architecture

#### Primary Database: production.db

**Core Patient Management Tables:**
- `users` - User accounts (user_id, email, full_name, username)
- `user_roles` - Role assignments (user_id → role_id many-to-many)
- `roles` - Role definitions (role_id, role_name)
- `patients` - Patient demographics and status
- `user_patient_assignments` - Patient-provider/coordinator assignments

**Provider Task Billing Tables (Weekly Workflow):**
- `provider_task_billing_status` - Workflow-driven billing tracking
  - Fields: billing_status_id, provider_id, patient_id, task_date, minutes_of_service, billing_code
  - Status flags: is_billed, is_invoiced, is_claim_submitted, is_insurance_processed, is_approved_to_pay, is_paid
  - Audit fields: billed_by, billed_date, created_date, updated_date

**Provider Weekly Payroll Tables:**
- `provider_weekly_payroll_status` - Workflow for provider compensation
  - Fields: payroll_status_id, provider_id, pay_week_number, pay_year, pay_week_start_date, pay_week_end_date
  - Tracking: paid_by_zen_count, paid_by_zen_minutes (to prevent double-payment)
  - Status: is_paid, paid_date, paid_by
  - Critical: paid_by_zen indicators show tasks already compensated elsewhere

**Coordinator Task Tables (Monthly Workflow):**
- `coordinator_tasks_YYYY_MM` - Monthly task tables (dynamic table creation)
  - Fields: patient_id, duration_minutes, task_description, coordinator_id
  - Aggregated by patient for billing code assignment

**Coordinator Monthly Summary Table:**
- `coordinator_monthly_summary` - Aggregated monthly data
  - Fields: coordinator_id, patient_id, month, year, total_tasks, total_minutes
  - Billing codes assigned based on minutes thresholds

**Onboarding Workflow Tables:**
- `onboarding_patients` - New patient tracking
  - Status fields: stage1_complete, stage2_complete, stage3_complete, stage4_complete
  - Tracks progression through intake workflow

**Supporting Tables:**
- `regions` - Geographic assignments
- `providers` - Provider profiles and specializations
- `coordinators` - Coordinator assignments
- `patient_panel_assignments` - Extended assignment metadata

---

## Role-Based System Structure

### Role Hierarchy (by role_id)

```
34 (Admin/Harpreet) - Full system access
├── 38 (Care Provider Manager) - Provider team oversight
│   └── 33 (Care Provider) - Direct care delivery
├── 40 (Coordinator Manager) - Coordinator team oversight
│   ├── 37 (Lead Coordinator) - Team lead
│   │   └── 36 (Care Coordinator) - Daily coordination
│   └── 36 (Care Coordinator)
├── 35 (Onboarding) - Patient intake
└── 39 (Data Entry) - Bulk data management
```

### Role Definitions

#### Role 33: Care Provider (PCP)
- **Access:** Clinical patient data for assigned patients
- **Dashboard Tabs:**
  - Patient Panel - Assigned patients with care status
  - Task Management - Daily clinical tasks
  - Billing Summary - View billing status (read-only)
- **Permissions:** Read assigned patient data, submit tasks
- **Key Feature:** Weekly billing status visible, no mark-as-billed access

#### Role 34: Admin (Harpreet)
- **Access:** Full system administrative access
- **Dashboard Tabs:** (8 tabs total)
  1. User Role Management - User account and role assignment
  2. Staff Onboarding - Patient intake workflow
  3. Coordinator Tasks - Task review and management
  4. Provider Tasks - Provider task review
  5. Patient Info - Patient demographics and status
  6. HHC View Template - Daily export view of active patients
  7. Workflow Reassignment - Reassign patients between providers/coordinators
  8. ZMO - Patient data management and search interface
  9. Billing Report - Weekly/Monthly billing and payroll dashboards
- **Permissions:** Full read/write access, mark tasks as billed, manage workflows
- **Key Feature:** Can mark provider tasks as billed and process payroll

#### Role 35: Onboarding Specialist
- **Access:** Patient intake and onboarding workflow
- **Dashboard:** Onboarding queue with stage progression tracking
- **Permissions:** Create new patients, track intake stages

#### Role 36: Care Coordinator (PCC)
- **Access:** Assigned patients and coordination tasks
- **Dashboard Tabs:**
  - Patient Panel - Assigned patients
  - Coordinator Tasks - Daily coordination tasks
- **Permissions:** Read patient data, submit coordination tasks, view monthly billing status

#### Role 37: Lead Coordinator (LC)
- **Access:** Team coordinator oversight + coordinator access
- **Dashboard:** Enhanced coordinator dashboard with team management
- **Permissions:** Same as coordinator + view team performance

#### Role 38: Care Provider Manager (CPM)
- **Access:** Provider team management + provider access
- **Dashboard:** Enhanced provider dashboard with team tabs
- **Permissions:** Same as provider + view/manage team assignments

#### Role 39: Data Entry
- **Access:** Data entry forms and bulk upload
- **Dashboard:** Data entry interface with batch operations
- **Permissions:** Limited to specific data entry tables

#### Role 40: Coordinator Manager (CM)
- **Access:** Coordinator team oversight + admin dashboard
- **Dashboard:** Full admin dashboard (same as Admin)
- **Permissions:** Team management, quality assurance, reporting

---

## Dashboard Specifications

### Admin Dashboard (Role 34 & 40)

The admin dashboard displays different tab sets based on user role and access level.

#### Tab 1: User Role Management
- **Purpose:** Manage user accounts and role assignments
- **Components:**
  - User list with search/filter by role, status, department
  - User creation form with role assignment
  - Bulk role management
  - User status tracking (active/inactive/suspended)
  - Login credentials management

#### Tab 2: Staff Onboarding
- **Purpose:** Track patient onboarding workflow
- **Components:**
  - Onboarding patient queue
  - Stage progression tracking (Stage 1-4)
  - Document upload and verification
  - Insurance verification status
  - Ready-for-assignment indicator

#### Tab 3: Coordinator Tasks
- **Purpose:** Review and manage coordinator daily tasks
- **Components:**
  - Task list with filter by coordinator, status, date range
  - Task detail view with patient context
  - Task status updates (pending, in-progress, completed)
  - Performance metrics by coordinator
  - Bulk task operations

#### Tab 4: Provider Tasks
- **Purpose:** Review and manage provider tasks
- **Components:**
  - Task list with filter by provider, patient, status
  - Task detail view
  - Task status tracking
  - Performance metrics by provider
  - Integration with billing workflow

#### Tab 5: Patient Info
- **Purpose:** Patient demographics and care information
- **Components:**
  - Patient search by name, ID, MRN
  - Demographics view and edit
  - Care plan summary
  - Provider/Coordinator assignment view
  - Medical history and communications
  - Document management

#### Tab 6: HHC View Template
- **Purpose:** Daily export view of all active patients
- **Components:**
  - Active patient list with key clinical data
  - Assignment status (provider, coordinator)
  - Metrics: Total Active Patients, Assigned to Coordinator, With Provider, Unassigned
  - Sortable and filterable data table
  - CSV export for daily reports
  - Clinical priority indicators

#### Tab 7: Workflow Reassignment
- **Purpose:** Reassign patients between providers and coordinators
- **Components:**
  - Patient search interface
  - Current assignment display
  - Provider/coordinator selection dropdowns
  - Assignment type selector (care provider, coordinator, both)
  - Workflow update and audit trail
  - Bulk reassignment for cohorts
  - Historical assignment tracking

#### Tab 8: ZMO (Patient Data Management)
- **Purpose:** Comprehensive patient data search and management
- **Components:**
  - Multi-criteria patient search (name, ID, MRN)
  - Patient panel and patient table data views
  - Column filtering and custom column selection
  - Data export (CSV, JSON)
  - Dynamic table joining and relationship viewing
  - Search history and saved searches
  - Clear results and reset functionality

#### Tab 9: Billing Report (Optional - Justin & Harpreet)
- **Purpose:** Billing and payroll dashboard access
- **Sub-tabs:**
  - Monthly Billing (Coordinators) - Coordinator minute aggregation
  - Weekly Billing (Providers) - Provider task billing workflow
  - Provider Payroll - Weekly payroll tracking and approval

### Weekly Provider Billing Dashboard (P00)

**Accessed By:** Admin (role 34), triggered from Billing Report tab

**Layout Hierarchy:**
```
Weekly Provider Billing (P00)
Track provider billing by week using provider tasks and billing status

[Select Billing Period - Show All Weeks checkbox]
[Select Week dropdown] [Week dates display]
[Filter by Billing Status dropdown]

### Billing Summary
[Total Tasks] [Total Minutes] [Billed Tasks %] [Pending Billed] [Unique Providers]

### Billing Data by Provider
[Show Audit Trail checkbox]
[Data table with billing status]

### Billing Actions (Admin only)
[Mark Selected as Billed interface]

### Export Options
[Download for Biller] [Download Full Data] [Download Pending Only]
```

**Key Features:**
- Hierarchical filtering: Week → Billing Status
- Summary metrics from provider_task_billing_status
- Detailed data display with optional audit columns
- Mark-as-billed functionality (Admin only)
- 3rd party biller export format
- Status workflow: Pending → Billed → Invoiced → Claim Submitted → Insurance Processed → Approved to Pay → Paid

**Permissions:**
- View: Admin (role 34) only
- Edit (mark as billed): Harpreet (user_id 12) only

### Weekly Provider Payroll Dashboard

**Accessed By:** Admin (role 34), triggered from Billing Report tab

**Layout Hierarchy:**
```
Weekly Provider Payroll Dashboard
Payroll Workflow Management for provider compensation tracking

⚠️ CRITICAL: paid_by_zen_count and paid_by_zen_minutes show ALREADY COMPENSATED tasks
[Select Billing Period]
[Select Week dropdown]

### Payroll Summary
[Total Providers] [Total Tasks] [Total Minutes] [Paid Count] [Pending Count]

### Payroll Data by Provider
[Data table with paid_by_zen indicators]

### Payroll Actions (Justin only)
[Mark Providers as Paid interface]

### Export Options
[Download for Payroll] [Download Full Data]
```

**Key Features:**
- Prevents double-payment via paid_by_zen tracking
- Critical indicator: paid_by_zen_count shows tasks already compensated
- Status workflow: Pending → Paid
- Separate from billing (Medicare reimbursement) workflow
- Integration with provider_weekly_payroll_status table

**Permissions:**
- View: Admin (role 34) + Harpreet (user_id 12)
- Edit (mark as paid): Justin (user_id 1) only

### Monthly Coordinator Billing Dashboard

**Accessed By:** Admin (role 34), triggered from Billing Report tab

**Layout Hierarchy:**
```
Monthly Coordinator Billing Dashboard
Coordinator minutes aggregated by patient with automatic billing code assignment

[Select Month] [Selected Period metric]

### Monthly Summary
[Total Patients] [Total Tasks] [Total Minutes]

### Billing Data by Patient
[Filter by Billing Code] [Show Only Pending Codes checkbox]
[Data table with auto-assigned codes]

### Export Options
[Download Filtered Data] [Download All Data] [Download Pending Codes]
```

**Key Features:**
- Automatic billing code assignment based on minutes thresholds
- Monthly aggregation from coordinator_tasks_YYYY_MM tables
- Status indicators for pending code assignment
- Patient-level aggregation (not task-level)
- CSV export for billing submission

### Care Provider Dashboard

**Dashboard:** Provider-specific view of assigned patients and tasks

**Tabs (when role 33 is primary):**
1. Patient Panel - Assigned patients with status
2. Task Management - Daily clinical tasks
3. Billing Summary (read-only) - View weekly billing status

**Tabs (when roles 33+38, provider with manager role):**
- Additional "Team Management" tab for managing assigned providers

### Care Coordinator Dashboard

**Dashboard:** Coordinator-specific view of assigned patients and tasks

**Tabs (when role 36 is primary):**
1. Patient Panel - Assigned patients
2. Coordinator Tasks - Daily coordination work

**Tabs (when roles 36+37 or 36+40, coordinator with manager role):**
- Additional "Team Management" tab for team oversight

---

## Billing and Payroll Workflows

### Phase 2 Workflow Architecture

#### Dual-Track Design

```
Provider Tasks (CSV Import)
    ↓
provider_tasks_YYYY_MM (Monthly raw tasks)
    ↓
[Billing Track] ────────────────→ [Payroll Track]
    ↓                                    ↓
provider_task_billing_status        provider_weekly_payroll_status
(Medicare reimbursement)            (Internal compensation)
    ↓                                    ↓
Weekly Billing Dashboard            Weekly Payroll Dashboard
(3rd party biller)                  (Internal accounting)
    ↓                                    ↓
Status: Pending→Billed→             Status: Pending→Paid
Invoiced→Claim Submitted→
Insurance Processed→Paid
```

### Weekly Provider Billing Workflow (P00)

**Objective:** Track provider task billing through Medicare reimbursement lifecycle

**Data Source:** provider_task_billing_status table

**Status Lifecycle:**
1. **Pending** - Task imported, awaiting billing submission
2. **Billed** - Marked as billed (Admin: Harpreet only)
3. **Invoiced** - Sent to Medicare as claim
4. **Claim Submitted** - Claim officially submitted
5. **Insurance Processed** - Insurance processing in progress
6. **Approved to Pay** - Insurance approval received
7. **Paid** - Payment received from insurance

**Admin Actions:**
- Select week and billing status to filter
- View summary metrics (total tasks, minutes, billed count)
- Mark selected tasks as billed (moves from Pending → Billed)
- Export data for 3rd party biller in standardized CSV format
- View audit trail (who marked, when)

**Key Columns:**
- billing_status_id, provider_id, patient_id, task_date
- minutes_of_service, billing_code, billing_status
- is_billed (boolean), billed_date, billed_by (audit)

### Weekly Provider Payroll Workflow

**Objective:** Track provider compensation while preventing double-payment

**Data Source:** provider_weekly_payroll_status table

**Critical Feature:** paid_by_zen indicators
- `paid_by_zen_count` - Number of tasks already compensated elsewhere
- `paid_by_zen_minutes` - Minutes already paid out
- Purpose: Prevents accidental double-payment to providers

**Status Lifecycle:**
1. **Pending** - Week data populated, awaiting approval
2. **Paid** - Marked as paid (Justin only)

**Admin/Justin Actions:**
- Select payroll week
- Review paid_by_zen indicators to identify already-compensated tasks
- Mark providers as paid (moves Pending → Paid)
- Export for internal payroll system

**Key Difference from Billing:**
- **Billing** = Insurance reimbursement (Medicare 3rd party)
- **Payroll** = Provider compensation (Internal ZEN payment)
- Some providers may be paid by other entities (paid_by_zen tracking prevents duplicate)

### Monthly Coordinator Billing Workflow

**Objective:** Aggregate coordinator minutes and auto-assign billing codes

**Data Source:** coordinator_tasks_YYYY_MM (monthly tables), aggregated to coordinator_monthly_summary

**Billing Code Assignment Logic:**
```
Minutes → Billing Code
≤15 min → 99211 (Office visit - minimal)
16-30 min → 99212 (Office visit - low)
31-45 min → 99213 (Office visit - moderate)
46-60 min → 99214 (Office visit - moderate-high)
>60 min → 99215 (Office visit - high)
0 min → PENDING (Manual assignment required)
```

**Aggregation Level:** By patient (not by task)

**Admin Actions:**
- Select month
- View aggregated coordinator minutes per patient
- Filter by billing code or pending status
- Export for billing submission

---

## Database Design and Data Model

### production.db Schema Overview

#### User and Role Management
```sql
users
├── user_id (PK)
├── email (UNIQUE)
├── username
├── full_name
└── password_hash

roles
├── role_id (PK)
└── role_name

user_roles
├── user_id (FK)
├── role_id (FK)
└── assigned_date
```

#### Patient and Assignment
```sql
patients
├── patient_id (PK)
├── first_name
├── last_name
├── date_of_birth
├── medical_record_number
├── insurance_id
└── status

user_patient_assignments
├── assignment_id (PK)
├── user_id (FK)
├── patient_id (FK)
├── role_id (FK)
├── assignment_type (provider/coordinator/both)
└── assigned_date
```

#### Provider Task Billing (Weekly)
```sql
provider_task_billing_status
├── billing_status_id (PK)
├── provider_task_id (FK)
├── provider_id (FK)
├── provider_name
├── patient_id (FK)
├── patient_name
├── task_date
├── billing_week (YYYY-WW format)
├── week_start_date
├── week_end_date
├── task_description
├── minutes_of_service
├── billing_code
├── billing_code_description
├── billing_status (Pending/Billed/Invoiced/...)
├── is_billed (BOOLEAN)
├── is_invoiced (BOOLEAN)
├── is_claim_submitted (BOOLEAN)
├── is_insurance_processed (BOOLEAN)
├── is_approved_to_pay (BOOLEAN)
├── is_paid (BOOLEAN)
├── billed_date
├── billed_by (user_id)
├── created_date
├── updated_date
└── [additional status fields]
```

#### Provider Weekly Payroll
```sql
provider_weekly_payroll_status
├── payroll_status_id (PK)
├── provider_id (FK)
├── provider_name
├── pay_week_number
├── pay_year
├── pay_week_start_date
├── pay_week_end_date
├── total_minutes
├── total_tasks
├── paid_by_zen_count (CRITICAL)
├── paid_by_zen_minutes (CRITICAL)
├── is_paid (BOOLEAN)
├── paid_date
├── paid_by (user_id)
├── created_date
└── updated_date
```

#### Coordinator Monthly Aggregation
```sql
coordinator_monthly_summary
├── summary_id (PK)
├── coordinator_id (FK)
├── patient_id (FK)
├── month
├── year
├── total_tasks
├── total_minutes
├── billing_code (auto-assigned)
├── billing_description
├── billing_status (Pending/Assigned)
└── created_date
```

#### Coordinator Monthly Raw Tasks
```sql
coordinator_tasks_YYYY_MM (dynamic tables)
├── task_id (PK)
├── coordinator_id (FK)
├── patient_id (FK)
├── task_date
├── duration_minutes
├── task_description
└── created_date
```

#### Onboarding Workflow
```sql
onboarding_patients
├── onboarding_id (PK)
├── patient_id (FK)
├── stage1_complete (BOOLEAN - intake)
├── stage2_complete (BOOLEAN - insurance verification)
├── stage3_complete (BOOLEAN - documentation)
├── stage4_complete (BOOLEAN - assignment)
└── completed_date
```

### Data Access Patterns

#### Role 34 (Admin) - Full Access
- Read: All tables
- Write: All tables
- Special: Mark as billed (provider_task_billing_status), manage workflows

#### Role 33 (Provider) - Assigned Patient Access
- Read: Assigned patient data, own tasks
- View: Billing status (read-only)
- Filtered by: user_patient_assignments where role_id=33

#### Role 36 (Coordinator) - Assigned Patient Access
- Read: Assigned patient data, own coordination tasks
- View: Monthly billing status (read-only)
- Filtered by: user_patient_assignments where role_id=36

#### Multi-Role Users
- Users can have multiple roles (e.g., role 33 + role 38)
- Primary role determines main dashboard
- Manager roles (37, 38, 40) unlock additional tabs
- Dashboard checks: `38 in user_role_ids` for manager functionality

---

## Technical Implementation

### Application Structure

```
app.py
├── Authentication (login, session management)
├── Role routing (primary role → dashboard selection)
├── Session state management
└── Main dashboard dispatch

src/
├── database.py
│   ├── get_db_connection() - SQLite with row_factory
│   ├── get_user_role_ids(user_id)
│   ├── Prepared statements for security
│   └── Transaction management
├── config/
│   └── ui_style_config.py
│       ├── get_section_title() - Professional headers
│       ├── get_metric_label() - Standardized labels
│       ├── TextStyle.INFO_INDICATOR - Text-based indicators
│       └── No emoji constants
├── dashboards/
│   ├── admin_dashboard.py - 8+ tabs for admin
│   ├── care_provider_dashboard_enhanced.py - Provider workflow
│   ├── care_coordinator_dashboard_enhanced.py - Coordinator workflow
│   ├── weekly_provider_billing_dashboard.py - P00 billing
│   ├── weekly_provider_payroll_dashboard.py - Payroll
│   ├── monthly_coordinator_billing_dashboard.py - Monthly billing
│   ├── onboarding_dashboard.py - Patient intake
│   └── data_entry_dashboard.py - Bulk data entry
└── utils/
    ├── performance_components.py
    │   ├── display_coordinator_patient_service_analysis()
    │   └── display_provider_monthly_summary()
    └── chart_components.py
        ├── Plotly-based visualizations
        └── Healthcare-appropriate styling
```

### Authentication and Authorization

```python
# Session state pattern (standard across all dashboards)
st.session_state['user_id'] = authenticated_user['user_id']
st.session_state['role_id'] = primary_role_id
st.session_state['user_role_ids'] = [34, 38]  # Multi-role support
st.session_state['user_full_name'] = 'Harpreet Cheema'

# Role checking pattern
if 34 in user_role_ids:  # Admin access
    # Display admin features
    
if 38 in user_role_ids:  # Manager access
    # Add management tabs
    st.tabs(["My Work", "Team Management"])
```

### Database Connection Pattern

```python
from src import database

conn = database.get_db_connection()  # Returns SQLite connection with row_factory
try:
    result = conn.execute(query, params).fetchall()
finally:
    conn.close()
```

### Dashboard Implementation Pattern

#### Hierarchical Filtering Example (Weekly Billing)
```python
# Level 1: Time period selection
st.markdown("**Select Billing Period**")
show_all_weeks = st.checkbox("Show All Weeks")

# Level 2: Specific selection
selected_week = st.selectbox("Select Week", weeks)

# Level 3: Status filter
selected_status = st.selectbox("Filter by Billing Status", statuses)

# Apply filters hierarchically
billing_week = None if show_all_weeks else selected_week["billing_week"]
status_filter = None if selected_status == "All" else selected_status
df = get_data(billing_week, status_filter)
```

### UI Styling Standards

```python
from src.config.ui_style_config import get_section_title, get_metric_label, TextStyle

# Professional headers (no emojis)
st.markdown("### Billing Summary")
st.subheader(get_section_title("Billing Actions"))

# Standardized labels
st.metric(get_metric_label("Total Tasks"), count)

# Text-based indicators instead of emoji
st.info(f"{TextStyle.INFO_INDICATOR} View Mode: Read-only access")
```

---

## Deployment and Operations

### Production Deployment Architecture

```
VPS Server
├── Git Repository (myhealthteam)
├── Python Environment
│   ├── Streamlit
│   ├── Pandas
│   ├── SQLite
│   └── Dependencies
├── production.db (SQLite database)
├── Data Directories
│   ├── downloads/ (CSV imports)
│   ├── backups/ (Daily backups)
│   └── scripts/ (PowerShell data pipeline)
└── Streamlit Server (port 8501)
```

### Deployment Workflow

**Local Development:**
1. Code changes in local Dev/ directory
2. Test with local production.db
3. Commit to git: `git add -A && git commit -m "message"`
4. Push to remote: `git push origin main`

**Production Update:**
1. SSH into VPS: `ssh user@vps-ip`
2. Navigate to repo: `cd /path/to/myhealthteam`
3. Pull latest: `git pull origin main`
4. Clear cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
5. Restart Streamlit: `systemctl restart streamlit` (or manual restart)

### Data Pipeline

```
Google Sheets
    ↓
CSV Downloads (downloads/ folder)
    ↓
1_download.ps1 - Get latest CSVs
    ↓
2_consolidate.ps1 - Merge monthly files
    ↓
3_import_to_database.ps1 - SQLite INSERT
    ↓
production.db (Updated with latest data)
    ↓
4_transform_data_enhanced.ps1 - Data validation
```

### Backup and Recovery

- **Backup Location:** `backups/` directory
- **Schedule:** Daily timestamped backups
- **Filename Format:** `backup_YYYYMMDD_HHMMSS/`
- **Critical Rule:** NEVER delete or restore production.db without explicit user permission

---

## Security and Compliance

### HIPAA Compliance

#### Patient Data Protection
- **Encryption:** Sensitive patient data encrypted at rest
- **Access Control:** Role-based access to patient records
- **Audit Trail:** All access logged with timestamp, user_id, action
- **Data Minimization:** Display only necessary fields per role

#### Authentication Security
- **Session Management:** Secure session tokens with timeout
- **Password Policy:** Strong password requirements enforced
- **Multi-User Access:** Impersonation controls for testing only

### Role-Based Access Control

```python
# Permission checking pattern
def can_mark_as_billed(user_role_ids):
    """Only role 34 (Admin/Harpreet) can mark tasks as billed"""
    return 34 in user_role_ids

def can_view_payroll(user_role_ids):
    """Only role 34 (Admin/Harpreet) can view payroll"""
    return 34 in user_role_ids

def can_edit_payroll(user_id, user_role_ids):
    """Only Justin (user_id=1) can approve payments"""
    return user_id == 1
```

### Audit Logging

All critical operations logged to provider_task_billing_status audit fields:
- `billed_by` - User who marked as billed
- `billed_date` - When marked as billed
- `updated_date` - Last modification timestamp
- Similar fields in payroll tables

---

## Key System Rules and Constraints

### Database Safety Rules
- ✅ ALWAYS use try/finally with conn.close()
- ❌ NEVER drop tables without explicit permission
- ❌ NEVER delete entire tables
- ❌ NEVER restore backups without user direction
- ✅ ALWAYS ask for confirmation before destructive operations

### Professional UI Standards
- ❌ NO emojis in healthcare interfaces
- ✅ Use TextStyle.INFO_INDICATOR for information markers
- ✅ Import from src.config.ui_style_config for consistency
- ✅ Use get_section_title() and get_metric_label() for headers

### Multi-Role User Handling
- ✅ Always check user_role_ids list (not single role_id)
- ✅ Manager roles (37, 38, 40) unlock additional dashboard tabs
- ✅ Use: `if 38 in user_role_ids:` to check for manager access
- ✅ Combine base dashboard with manager-specific tabs

### Billing vs Payroll Distinction
- **Billing (P00):** Medicare reimbursement via 3rd party service (weekly)
- **Payroll:** Internal provider compensation (weekly)
- **Coordinator Billing:** Medicare aggregation by patient (monthly)
- **Separate Workflows:** Don't mix billing status with payroll status
- **Critical Warning:** paid_by_zen prevents double-payment in payroll

---

## Patient Visit Tracking System

### Overview
The visit tracking system ensures that whenever a provider records a new visit, the `last_visit_date` and `service_type` are synchronously updated across ALL patient-related tables, keeping dashboards and exports in perfect sync.

### Core Components

#### 1. Database Functions (`src/database.py`)

**New Function: `sync_patient_last_visit_all_tables()`** (lines 1862-1925)
- **Purpose:** Centralized synchronization of visit data across all patient tables
- **Trigger:** Called from `save_daily_task()` after visit is recorded
- **Updates 3 tables in single transaction:**

```python
sync_patient_last_visit_all_tables(conn, patient_id, last_visit_date, service_type)
```

**Tables Updated:**
1. **patients** (canonical source):
   - `last_visit_date` - Date of most recent visit
   - `service_type` - Type of service from task_description

2. **patient_panel** (denormalized for dashboards):
   - `last_visit_date` - Synchronized from patients table
   - `last_visit_service_type` - Synchronized from patients table

3. **hhc_patients_export** (for HHC export functionality):
   - Automatically refreshed by recreating from `hhc_export_view`
   - Ensures HHC exports always reflect latest visit data

**Error Handling:**
- Gracefully handles missing tables (no exceptions thrown)
- Logs all synchronization operations
- Continues if individual table updates fail

#### 2. Updated `save_daily_task()` Function (lines 1927-2176)

**Integration Points:**
- Called when provider logs a visit via Care Provider Dashboard
- For initial TV (Telehealth) visits:
  - Calls `sync_patient_last_visit_all_tables()` to update all tables
  - Updates initial TV specific fields (`initial_tv_completed_date`, `initial_tv_provider`, etc.)
  - Updates onboarding completion status

- For regular provider visits:
  - Calls `sync_patient_last_visit_all_tables()` to update all tables
  - Records visit to monthly `provider_tasks_YYYY_MM` table
  - Creates billing status record if billable

**Transaction Safety:**
- All updates committed together in single transaction
- Rollback on any error
- Database connection properly closed in finally block

#### 3. Transform Script Updates (`transform_production_data_v3_fixed.py`)

**Updated `update_patient_last_visit_dates()`** (lines 827-902)
- **Purpose:** Batch update last visit data during data imports/transforms
- **Captures:** Both `last_visit_date` AND `service_type` from provider task tables
- **Logic:** Uses ROW_NUMBER() to identify most recent visit per patient
- **Updates:** `patients` table (source for all downstream tables)

**Updated `populate_patient_panel()`** (lines 904-1066)
- **New Column:** `last_visit_service_type TEXT` added to schema
- **Populated From:** `p.service_type as last_visit_service_type`
- **Purpose:** Denormalized panel view includes service type for dashboard display

### Data Flow Architecture

```
Provider Records New Visit
    ↓
save_daily_task() called with:
├─ provider_id
├─ patient_id
├─ task_date
├─ task_description (service type)
├─ billing_code
└─ notes
    ↓
sync_patient_last_visit_all_tables() called
    ├─→ UPDATE patients table
    │   ├─ last_visit_date = task_date
    │   └─ service_type = task_description
    │
    ├─→ UPDATE patient_panel table
    │   ├─ last_visit_date = task_date
    │   └─ last_visit_service_type = task_description
    │
    └─→ Refresh hhc_patients_export table
        └─ Recreated from hhc_export_view
           (which queries from patients table)
    ↓
Transaction COMMITTED
    ↓
All downstream systems updated:
├─ Care Provider Dashboard (refreshes patient list)
├─ Admin HHC View (shows latest visits)
├─ HHC Export (includes current visit data)
└─ Database queries (all see new visit)
```

### Dashboard Integration

#### Provider Dashboard (`care_provider_dashboard_enhanced.py`)
- **Source:** `get_all_patient_panel()` function
- **Displays:** "Last Visit Date" and "Service Type" columns
- **Updates:** Real-time when save_daily_task() completes
- **Color Coding:** Last visit dates colored by recency
  - Green: ≤30 days
  - Yellow: 31-60 days
  - Red: ≥61 days (Gap >60d)

#### Admin HHC View (`admin_dashboard.py` - HHC tab)
- **Source:** `patient_panel` and `hhc_patients_export` tables
- **Displays:** "Last Visit", "Last Visit Type" columns
- **Refresh:** Automatic via sync_patient_last_visit_all_tables()
- **Used For:** HHC export of patient visit history

#### HHC Export (`get_hhc_export_data()`)
- **Source:** `patient_panel` table
- **Columns:** `last_visit_date` and `service_type`
- **Refresh:** Synced when new visit recorded
- **Export Format:** CSV with visit tracking fields

### Service Type Classification

Service types come from `task_description` field recorded during visit:
- **Initial TV Telehealth:** "PCP-Visit Telehealth (TE) (NEW pt)"
- **Follow-up Visits:** Various provider-entered descriptions
- **Stored In:**
  - `patients.service_type` - Current service type
  - `patient_panel.last_visit_service_type` - Type of last visit
  - `provider_tasks_YYYY_MM.task_description` - Raw task record

### Data Consistency Guarantees

**Single Source of Truth:**
- `patients` table is canonical for `last_visit_date` and `service_type`
- All other tables derive from patients table
- No conflicting data sources

**Batch Import Consistency:**
- Transform script (`update_patient_last_visit_dates()`) updates patients table
- Calls `populate_patient_panel()` to rebuild denormalized view
- HHC export view queries patients table directly

**Real-Time Consistency:**
- `save_daily_task()` uses `sync_patient_last_visit_all_tables()` function
- All tables updated in single transaction
- HHC export table refreshed immediately

**Error Handling:**
- Missing tables don't cause failures
- All updates logged for audit trail
- Graceful degradation if hhc_patients_export doesn't exist yet

### Key Implementation Rules

✅ **ALWAYS use `sync_patient_last_visit_all_tables()`** when updating visit information
✅ **ALWAYS call within same transaction** as visit record creation
✅ **ALWAYS include BOTH `last_visit_date` AND `service_type`** in updates
✅ **ALWAYS commit after sync function** completes
✅ **NEVER update patient_panel directly** - let sync function handle it
✅ **NEVER update hhc_patients_export directly** - it's materialized from view

---

## Database Synchronization (DB-Sync)

### Overview

The DB-Sync system enables bidirectional synchronization of `production.db` between the development server (SRVR - Windows) and production server (VPS2/Server2 - Linux). It uses a **smart sync** approach that preserves manual entries on production while allowing bulk CSV imports from the development server.

### Architecture

```
SRVR (Windows Dev)                      VPS2 (Linux Production)
─────────────────                       ─────────────────────
     │                                          │
     │  ┌───────────────────────────────────┐   │
     │  │ Smart CSV Sync                    │   │
     │  │ - Syncs only CSV_IMPORT rows      │   │
     │  │ - Preserves MANUAL/DASHBOARD rows │   │
     │  └───────────────────────────────────┘   │
     │                                          │
     ├──────── SSH over Tailscale VPN ─────────►│
     │         (uses ssh alias 'server2')       │
     │                                          │
production.db                           production.db
(development copy)                      (master/production)
```

### Key Concepts

#### Source System Tracking
Each task row has a `source_system` column that identifies its origin:
- **CSV_IMPORT** - Data imported from Google Sheets CSVs (bulk imports)
- **MANUAL** - Data entered manually via dashboards
- **DASHBOARD** - Data created through dashboard workflows
- **WORKFLOW** - Data from automated workflow processes

#### Smart Sync Logic
The sync only replaces `CSV_IMPORT` rows on production, preserving all manual entries:
```sql
-- On production server (VPS2):
BEGIN TRANSACTION;
DELETE FROM provider_tasks_2025_12 WHERE source_system = 'CSV_IMPORT';
-- INSERT fresh CSV_IMPORT rows from SRVR...
COMMIT;
```

### Directory Structure

```
D:\Git\myhealthteam2\Dev\db-sync\
├── bin\                          # Sync scripts
│   ├── sync_csv_data.ps1         # Smart CSV sync (recommended)
│   ├── sync_production_db.ps1    # Full DB sync (use with caution)
│   ├── test_connection.ps1       # Connection test utility
│   └── setup_scheduled_task.ps1  # Windows Task Scheduler setup
├── config\
│   └── db-sync.json              # Configuration file
├── logs\                         # Sync operation logs (git-ignored)
├── backups\                      # Pre-sync backups (git-ignored)
├── temp\                         # Temporary export files (git-ignored)
└── flags\                        # Trigger files (git-ignored)
```

### Configuration

**File:** `db-sync/config/db-sync.json`

```json
{
  "sync": {
    "master_host": "server2",
    "master_user": "",
    "master_db_path": "/opt/myhealthteam/production.db",
    "slave_db_path": "D:\\Git\\myhealthteam2\\Dev\\production.db",
    "slave_backup_dir": "D:\\Git\\myhealthteam2\\Dev\\db-sync\\backups",
    "slave_log_dir": "D:\\Git\\myhealthteam2\\Dev\\db-sync\\logs",
    "slave_temp_dir": "D:\\Git\\myhealthteam2\\Dev\\db-sync\\temp",
    "sync_interval_minutes": 15,
    "bulk_import_trigger_file": "D:\\Git\\myhealthteam2\\Dev\\db-sync\\flags\\bulk_import_complete.flag"
  },
  "tables": {
    "task_tables_prefix": ["provider_tasks_", "coordinator_tasks_"],
    "preserve_source_systems": ["MANUAL", "DASHBOARD", "WORKFLOW"]
  }
}
```

**Note:** Uses SSH alias `server2` from `~/.ssh/config` - no additional SSH key setup required.

### Usage

#### Test Connection
```powershell
.\db-sync\bin\test_connection.ps1
```
Verifies: SSH connection, database exists, SQLite accessible, task tables present.

#### Dry Run (Preview Changes)
```powershell
.\db-sync\bin\sync_csv_data.ps1 -DryRun
```
Shows what would be synced without making changes.

#### Execute Sync
```powershell
.\db-sync\bin\sync_csv_data.ps1
```
Syncs current month's CSV_IMPORT rows to production.

#### Sync Specific Month
```powershell
.\db-sync\bin\sync_csv_data.ps1 -Month "2025_11"
```

#### Integration with Data Refresh
```powershell
.\refresh_production_data.ps1 -SyncToProduction
```
Downloads fresh CSVs, imports to local DB, then syncs to production.

### Scheduled Task Setup

To enable automatic 15-minute syncs (requires Administrator):
```powershell
# Run PowerShell as Administrator
.\db-sync\bin\setup_scheduled_task.ps1
```

**Task Name:** `DB-Sync-Production`

**Management Commands:**
```powershell
Get-ScheduledTask -TaskName 'DB-Sync-Production'      # View status
Start-ScheduledTask -TaskName 'DB-Sync-Production'    # Run now
Disable-ScheduledTask -TaskName 'DB-Sync-Production'  # Disable
.\db-sync\bin\setup_scheduled_task.ps1 -Remove        # Remove task
```

### Sync Process Flow

```
1. Test SSH Connection (server2 alias)
   ↓
2. Find Task Tables (provider_tasks_YYYY_MM, coordinator_tasks_YYYY_MM)
   ↓
3. For Each Table:
   ├── Count CSV_IMPORT rows locally
   ├── Export using SQLite .mode insert (handles special characters)
   ├── Create SQL file: BEGIN; DELETE WHERE source_system='CSV_IMPORT'; INSERT...; COMMIT;
   ├── SCP upload to /tmp/ on server2
   ├── SSH execute: sqlite3 production.db < import.sql
   └── Cleanup temp files
   ↓
4. Log Results
```

### Safety Features

- **Pre-sync backup** - Local database backed up before any operation
- **Integrity checks** - SQLite PRAGMA integrity_check before and after
- **Atomic transactions** - All changes wrapped in BEGIN/COMMIT
- **Source system preservation** - Never deletes MANUAL/DASHBOARD rows
- **Proper escaping** - SQLite `.mode insert` handles special characters (newlines, quotes)

### Troubleshooting

**SSH Connection Failed:**
- Verify SSH alias: `ssh server2 "echo OK"`
- Check `~/.ssh/config` has `server2` entry

**No Task Tables Found:**
- Check month format: `YYYY_MM` (e.g., `2025_12`)
- Verify tables exist locally: `sqlite3 production.db ".tables"`

**Sync Failed with Parse Errors:**
- Usually caused by special characters in data
- Solution: Script uses SQLite `.mode insert` for proper escaping

**Permission Denied (Scheduled Task):**
- Must run PowerShell as Administrator to create scheduled tasks

### Git Ignore

The following directories are excluded from version control:
```
db-sync/logs/      # Sync operation logs
db-sync/backups/   # Pre-sync database backups
db-sync/temp/      # Temporary export files
db-sync/flags/     # Trigger files for sync operations
```


Scripts and config remain in version control: `db-sync/bin/`, `db-sync/config/`



---



## Analytics and Metrics

The ZEN Medical Healthcare Management System includes advanced analytics capabilities through pre-built database views and interactive visualization tools. These analytics provide insights into coordinator and provider performance, facility metrics, and operational trends.

### Pre-Built Analytics Views

Seven unified database views have been created to simplify data analysis and reporting. These views combine coordinator and provider data with facility information for comprehensive metrics.

#### 1. `minutes_per_staff_per_month_per_facility`
**Key View for Requested Metrics** - Provides minutes per coordinator/provider per month per facility with standardized columns:
- `facility_name` - Facility identifier
- `staff_name` - Coordinator or provider name
- `task_type` - 'coordinator' or 'provider'
- `month` - YYYY-MM format
- `total_minutes` - Sum of minutes for the month
- `task_count` - Number of tasks completed
- `unique_patients` - Distinct patients served
- `avg_minutes_per_task` - Average duration per task

#### 2. `tasks_per_month_per_facility`
**Key View for Requested Metrics** - Provides task counts per month per facility:
- `facility_name` - Facility identifier
- `task_type` - 'coordinator' or 'provider'
- `month` - YYYY-MM format
- `task_count` - Number of tasks
- `total_minutes` - Sum of minutes
- `unique_staff` - Distinct staff members
- `unique_patients` - Distinct patients served

#### 3. `facility_summary`
**Key View for Requested Metrics** - Provides comprehensive facility-level metrics:
- `facility_name` - Facility identifier
- `total_tasks` - Total tasks across coordinators and providers
- `total_minutes` - Total minutes of service
- `avg_minutes_per_task` - Average minutes per task
- `unique_patients` - Distinct patients served
- `coordinator_count` - Number of active coordinators
- `provider_count` - Number of active providers
- `coordinator_minutes` - Total coordinator minutes
- `provider_minutes` - Total provider minutes

#### 4. `unified_tasks`
Combines all coordinator and provider tasks with standardized column names for consistent analysis.

#### 5. `unified_tasks_with_facilities`
Extends unified_tasks with facility information joined from patient records.

#### 6. `staff_performance_summary`
Provides performance metrics aggregated by staff member across all facilities and time periods.

#### 7. `monthly_trends`
Tracks monthly trends for both coordinator and provider activities.

### Analytics Tools

Two primary tools are available for data exploration and visualization:

#### PyGWalker Data Visualization
Interactive drag-and-drop visualization tool that loads all unified views into a single interface:
- **Filter by view** using the `_view_name` column
- **Drag-and-drop interface** for creating charts and visualizations
- **Export capabilities** for charts and data
- **Cross-view analysis** by combining multiple datasets
- **Access**: Run `run_pygwalker.bat` or `python simple_pygwalker.py`

#### Datasette Database Browser
Web-based SQLite browser with built-in charting and dashboard capabilities:
- **Browse all tables and views** in a web interface
- **Run SQL queries** directly in the browser
- **Pre-built dashboards** for common metrics
- **Export data** as CSV, JSON, and other formats
- **Shareable links** to specific queries and results
- **Access**: Run `run_datasette.bat`

### Key Metrics Available

All requested metrics are readily available through the pre-built views:

#### Minutes per Coordinator per Month, per Facility
Available in `minutes_per_staff_per_month_per_facility` view, filter by `task_type = 'coordinator'`

#### Tasks per Provider per Month, per Facility
Available in `minutes_per_staff_per_month_per_facility` view, filter by `task_type = 'provider'`

#### General Minutes per Month per Facility
Available in `tasks_per_month_per_facility` view with `total_minutes` column

#### Tasks per Month per Facility
Available in `tasks_per_month_per_facility` view with `task_count` column

### Implementation Details

The analytics infrastructure is built on standardized SQL views that:
- **Combine data sources** from coordinator_tasks and provider_tasks tables
- **Standardize column names** across different data types
- **Include facility information** through patient joins
- **Pre-aggregate common metrics** for performance
- **Maintain data consistency** with the source tables

These views are created by running `create_unified_view.sql` against the production database and are automatically maintained as the underlying data changes.

---

## Conclusion and Current Status


### Phase 2 Completion Status
- ✅ Weekly Provider Billing Dashboard (P00) - Production
- ✅ Weekly Provider Payroll Dashboard - Production
- ✅ Monthly Coordinator Billing Dashboard - Production
- ✅ Admin Dashboard with 8+ tabs (ZMO, HHC, Workflow Reassignment)
- ✅ Permission fixes for role 34 (Admin) access
- ✅ Hierarchical filtering (Month → Week → Status)
- ✅ Professional UI standards (no emojis)

### December 16, 2025 - Workflow Assignment Patient Dropdown Fix

**Issue:** Workflow quick start dropdown showed no patients for Jan (supervisor) in the Workflow Assignment tab.

**Root Cause:** The patient list for the workflow dropdown was being filtered by Active* status before being passed, which was failing because the filtering logic was checking status values that didn't exist or were formatted differently.

**Solution Implemented:**
1. **Primary approach:** Workflow module now fetches active patients directly from the database using SQL `WHERE status LIKE 'Active%'`
2. **Smart fallback:** If `active_patients` parameter is provided and populated (for regular coordinators with filtered patient panels), use that list (respects patient panel filters)
3. **Supervisor behavior:** For supervisors/admins (Jan, Jose), falls back to database query and shows ALL active patients system-wide
4. **Regular coordinator behavior:** For regular coordinators, workflow dropdown matches their patient panel filter selection

**Files Modified:**
- `src/dashboards/workflow_module.py` (lines 748-779): Updated `show_workflow_management()` function to fetch patients directly from database with smart fallback logic
- `src/dashboards/care_coordinator_dashboard_enhanced.py` (lines 1413-1431): Simplified patient list generation for passing to workflow module

**Key Implementation Details:**
```python
# In workflow_module.py - Quick Start patient selector
if active_patients and isinstance(active_patients, list) and len(active_patients) > 0:
    # Use filtered patient list (respects patient panel filters for regular coordinators)
    workflow_patient_options = ["Select Patient..."] + active_patients
else:
    # Fallback: Fetch all active patients from database (for supervisors/admins)
    # Query: SELECT first_name, last_name FROM patients WHERE status LIKE 'Active%'
```

**Testing Results:**
- ✅ Jan can now see all active patients in workflow quick start dropdown
- ✅ Regular coordinators see filtered patient list matching their patient panel selection
- ✅ No dependency on patient_data_list transformation logic
- ✅ Direct database query ensures consistency with actual patient status values

### Active Issues and Solutions
1. **Cache Clearing:** After code updates, clear `__pycache__` and refresh browser (Streamlit auto-reloads)
2. **Remote Deployment:** Must pull latest code on VPS and refresh browser
3. **Multi-Role Support:** Always check user_role_ids list, not single role
4. **Patient Status Filtering:** Use `LIKE 'Active%'` to match all Active variants (Active, Active-Geri, Active-PCP)

### Next Steps
1. Test all workflow assignment functionality with Jan and regular coordinators
2. Verify weekly billing workflow end-to-end
3. Verify weekly payroll workflow end-to-end
4. Document any production data issues
5. Plan Phase 3 features (if applicable)

---

**Document Owner:** Engineering Team  
**Last Review:** December 2025  
**Next Review Date:** January 2026
