# Complete Database Schema Documentation

**Generated:** January 2025  
**Database:** production.db  
**Purpose:** Comprehensive documentation of all tables, schemas, and relationships

---

## Table of Contents

1. [Overview](#overview)
2. [Core Tables](#core-tables)
3. [Source Data Tables](#source-data-tables)
4. [Workflow Tables](#workflow-tables)
5. [Backup Tables](#backup-tables)
6. [Utility Tables](#utility-tables)
7. [Column Mappings for CSV Imports](#column-mappings-for-csv-imports)

---

## Overview

This database contains **176 tables** organized into several categories:
- **Core operational tables** (patients, providers, coordinators, etc.)
- **Source data tables** (monthly task imports from CSV files)
- **Workflow management tables** (onboarding, assignments, etc.)
- **Backup and historical tables**
- **Utility and configuration tables**

---

## Core Tables

### patients
**Purpose:** Main patient registry with normalized patient IDs
```sql
CREATE TABLE patients (
    patient_id TEXT,                    -- Format: "LASTNAME FIRSTNAME MM/DD/YYYY"
    region_id INT,
    first_name TEXT,
    last_name TEXT,
    date_of_birth TEXT,
    gender TEXT,
    phone_primary TEXT,
    phone_secondary TEXT,
    email TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relationship TEXT,
    insurance_primary TEXT,
    insurance_policy_number TEXT,
    insurance_secondary TEXT,
    medical_record_number TEXT,
    enrollment_date TEXT,
    discharge_date TEXT,
    notes TEXT,
    created_date TEXT,
    updated_date TEXT,
    created_by INT,
    updated_by INT,
    current_facility_id INT,
    hypertension INT,
    mental_health_concerns INT,
    dementia INT,
    last_annual_wellness_visit TEXT,
    last_first_dob TEXT,
    status TEXT,
    medical_records_requested BOOLEAN DEFAULT FALSE,
    referral_documents_received BOOLEAN DEFAULT FALSE,
    insurance_cards_received BOOLEAN DEFAULT FALSE,
    emed_signature_received BOOLEAN DEFAULT FALSE,
    last_visit_date DATE,
    facility TEXT,
    assigned_provider TEXT,
    assigned_cm TEXT,
    source_system TEXT,
    imported_at TEXT
);
```

### providers
**Purpose:** Healthcare provider information
```sql
CREATE TABLE providers (
    provider_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);
```

### coordinators
**Purpose:** Care coordinator information
```sql
CREATE TABLE coordinators (
    coordinator_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);
```

### users
**Purpose:** System user accounts
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    status TEXT NOT NULL,
    hire_date TEXT,
    termination_date TEXT,
    max_patients INTEGER,
    performance_rating REAL,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    full_name TEXT,
    password TEXT DEFAULT 'pass123',
    username TEXT,
    last_login TEXT
);
```

---

## Source Data Tables

### Monthly CM Tasks (CMLog imports)
**Pattern:** `SOURCE_CM_TASKS_YYYY_MM`
**Purpose:** Care manager task data imported from CMLog CSV files

**Available months:**
- SOURCE_CM_TASKS_1999_12
- SOURCE_CM_TASKS_2022_01
- SOURCE_CM_TASKS_2025_01 through SOURCE_CM_TASKS_2025_09

**Schema:**
```sql
CREATE TABLE SOURCE_CM_TASKS_YYYY_MM (
    patient_id TEXT,
    coordinator_id TEXT,
    date TEXT,
    duration_minutes REAL,
    task_description TEXT,
    comparison_key TEXT,
    imported_at TEXT
);
```

### Monthly PSL Tasks (Provider task imports)
**Pattern:** `SOURCE_PSL_TASKS_YYYY_MM`
**Purpose:** Provider task data imported from PSL CSV files

**Available months:**
- SOURCE_PSL_TASKS_2001_01
- SOURCE_PSL_TASKS_2023_05 through SOURCE_PSL_TASKS_2025_09

**Schema:**
```sql
CREATE TABLE SOURCE_PSL_TASKS_YYYY_MM (
    provider_code TEXT,
    patient_id TEXT,
    date TEXT,
    task_description TEXT,
    duration_minutes REAL,
    comparison_key TEXT,
    imported_at TEXT
);
```

### Other Source Tables
- **SOURCE_PATIENT_DATA:** Patient information from ZMO imports
- **SOURCE_PROVIDER_TASKS_HISTORY:** Historical provider task data
- **SOURCE_COORDINATOR_TASKS_HISTORY:** Historical coordinator task data
- **SOURCE_STAFF_INFO:** Staff information imports
- **SOURCE_REGION_ZIP_CODES:** Geographic region mappings

---

## Workflow Tables

### onboarding_patients
**Purpose:** Patient onboarding workflow management
```sql
CREATE TABLE onboarding_patients (
    patient_id TEXT PRIMARY KEY,
    workflow_stage TEXT DEFAULT 'initial_tv',
    stage_status TEXT DEFAULT 'pending',
    assigned_provider_id INTEGER,
    assigned_coordinator_id INTEGER,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (assigned_provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (assigned_coordinator_id) REFERENCES coordinators(coordinator_id)
);
```

### patient_assignments
**Purpose:** Patient-provider-coordinator assignments
```sql
CREATE TABLE patient_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    coordinator_id INTEGER NOT NULL,
    assignment_date TEXT,
    assignment_type TEXT,
    status TEXT,
    priority_level TEXT,
    notes TEXT,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    initial_tv_provider_id INTEGER,
    recommended_provider_id INTEGER
);
```

---

## Column Mappings for CSV Imports

### CMLog Files → SOURCE_CM_TASKS_YYYY_MM
| CSV Column | Database Column | Transformation |
|------------|----------------|----------------|
| `Pt Name` | `patient_id` | Remove "ZEN-", remove commas, normalize spaces, uppercase |
| `Coordinator` | `coordinator_id` | Direct mapping |
| `Date` | `date` | Normalize date format |
| `Duration` | `duration_minutes` | Convert to numeric |
| `Task` | `task_description` | Direct mapping |

### PSL Files → SOURCE_PSL_TASKS_YYYY_MM
| CSV Column | Database Column | Transformation |
|------------|----------------|----------------|
| `Patient Last, First DOB` | `patient_id` | Remove "ZEN-", remove commas, normalize spaces, uppercase |
| Filename | `provider_code` | Extract provider code from filename |
| `Date` or `Date Only` | `date` | Normalize date format |
| `Task` | `task_description` | Direct mapping |
| `Duration` | `duration_minutes` | Convert to numeric |

### RVZ Files → SOURCE_PSL_TASKS_YYYY_MM
| CSV Column | Database Column | Transformation |
|------------|----------------|----------------|
| `Patient Last, First DOB` | `patient_id` | Remove "ZEN-", remove commas, normalize spaces, uppercase |
| Filename | `provider_code` | Extract provider code from filename |
| `Date` or `Date Only` | `date` | Normalize date format |
| `Task` | `task_description` | Direct mapping |
| `Duration` | `duration_minutes` | Convert to numeric |

### ZMO Files → patients
| CSV Column | Database Column | Transformation |
|------------|----------------|----------------|
| `LAST FIRST DOB` | `patient_id` | Normalize spaces, uppercase |
| `Last` | `last_name` | Direct mapping |
| `First` | `first_name` | Direct mapping |
| `DOB` | `date_of_birth` | Normalize date format |
| Contact fields | `phone_primary`, `address_*` | Direct mapping |
| Provider fields | `assigned_provider`, `assigned_cm` | Direct mapping |

---

## Key Normalization Rules

### Patient ID Normalization
All patient IDs are normalized to the format: `"LASTNAME FIRSTNAME MM/DD/YYYY"`

**Transformation steps:**
1. Remove "ZEN-" prefix if present
2. Remove commas
3. Replace multiple spaces with single spaces
4. Convert to uppercase
5. Ensure consistent date format (MM/DD/YYYY)

**Examples:**
- `"ZEN-SMITH, JOHN 01/15/1980"` → `"SMITH JOHN 01/15/1980"`
- `"JOHNSON,  MARY  12/03/1975"` → `"JOHNSON MARY 12/03/1975"`

### Date Normalization
All dates are normalized to MM/DD/YYYY format for consistency.

### Provider Code Extraction
Provider codes are extracted from filenames:
- `PSL_ZEN-ABC.csv` → `ZEN-ABC`
- `RVZ_ZEN-XYZ.csv` → `ZEN-XYZ`

---

## Import Process Flow

1. **CSV File Detection:** Scan downloads folder for new CSV files
2. **File Type Classification:** Identify CMLog, PSL, RVZ, or ZMO files
3. **Data Normalization:** Apply appropriate transformations
4. **Duplicate Detection:** Compare against existing data using comparison_key
5. **Database Import:** Insert only new records
6. **Validation:** Verify data integrity and relationships

---

## Backup and Recovery

### Backup Tables
- **patients_backup:** Backup of patients table before migrations
- **patient_assignments_old:** Historical assignment data
- Various `*_old` tables for schema migration safety

### Recovery Procedures
1. Backup tables are created before major schema changes
2. Data can be restored from backup tables if needed
3. Migration scripts maintain data integrity during schema updates

---

**Last Updated:** January 2025  
**Maintained by:** Development Team  
**Contact:** For questions about this schema, refer to the development team.