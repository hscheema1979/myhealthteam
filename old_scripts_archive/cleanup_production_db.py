# Database Cleanup Script - Remove Unnecessary Tables

## Required Tables (Keep These)

### Core Infrastructure
- users
- roles
- user_roles
- facilities
- task_billing_codes

### Patient Data
- patients
- patient_panel
- patient_assignments

### Task Data (Monthly Partitions)
- provider_tasks_2025_* (all months)
- coordinator_tasks_2025_* (all months)

### Summary Tables
- provider_weekly_summary_with_billing
- coordinator_monthly_summary_2025_* (all months)
- patient_monthly_billing_2025_* (all months)
- provider_task_billing_status

### Onboarding (Keep for Future)
- onboarding_patients
- onboarding_tasks
- workflow_instances
- workflow_steps
- tasks

---

## Tables to Remove

### Pattern-Based Removal
```sql
-- Drop all staging tables
SELECT 'DROP TABLE IF EXISTS ' || name || ';' 
FROM sqlite_master 
WHERE type='table' AND name LIKE 'staging_%';

-- Drop all SOURCE tables
SELECT 'DROP TABLE IF EXISTS ' || name || ';' 
FROM sqlite_master 
WHERE type='table' AND name LIKE 'SOURCE_%';

-- Drop backup tables
SELECT 'DROP TABLE IF EXISTS ' || name || ';' 
FROM sqlite_master 
WHERE type='table' AND (name LIKE '%_backup' OR name LIKE '%_old' OR name LIKE '%_test');
```

### Specific Deprecated Tables
```sql
-- Non-partitioned versions (replaced by YYYY_MM partitions)
DROP TABLE IF EXISTS provider_tasks;
DROP TABLE IF EXISTS coordinator_tasks;
DROP TABLE IF EXISTS coordinator_monthly_summary;

-- Old summary table versions
DROP TABLE IF EXISTS provider_weekly_summary;
DROP TABLE IF EXISTS provider_weekly_summary_2025_09;
DROP TABLE IF EXISTS provider_weekly_summary_2025_35;
DROP TABLE IF EXISTS provider_monthly_summary;
```

---

## Cleanup Script

```python
# cleanup_production_db.py
import sqlite3
import re

DB_PATH = 'production.db'

# Tables to KEEP (whitelist approach is safer)
KEEP_PATTERNS = [
    r'^users$',
    r'^roles$',
    r'^user_roles$',
    r'^facilities$',
    r'^task_billing_codes$',
    r'^patients$',
    r'^patient_panel$',
    r'^patient_assignments$',
    r'^provider_tasks_\d{4}_\d{2}$',  # Monthly partitions
    r'^coordinator_tasks_\d{4}_\d{2}$',  # Monthly partitions
    r'^provider_weekly_summary_with_billing$',
    r'^coordinator_monthly_summary_\d{4}_\d{2}$',  # Monthly partitions
    r'^patient_monthly_billing_\d{4}_\d{2}$',  # Monthly partitions
    r'^provider_task_billing_status$',
    r'^onboarding_patients$',
    r'^onboarding_tasks$',
    r'^workflow_instances$',
    r'^workflow_steps$',
    r'^tasks$',
    r'^audit_log$',  # Keep for compliance
    r'^sqlite_sequence$',  # SQLite internal
]

def should_keep_table(table_name):
    """Check if table matches any keep pattern"""
    for pattern in KEEP_PATTERNS:
        if re.match(pattern, table_name):
            return True
    return False

def cleanup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Total tables in database: {len(all_tables)}")
    
    # Identify tables to drop
    tables_to_drop = [t for t in all_tables if not should_keep_table(t)]
    tables_to_keep = [t for t in all_tables if should_keep_table(t)]
    
    print(f"\nTables to KEEP: {len(tables_to_keep)}")
    for t in sorted(tables_to_keep):
        print(f"  ✓ {t}")
    
    print(f"\nTables to DROP: {len(tables_to_drop)}")
    for t in sorted(tables_to_drop):
        print(f"  ✗ {t}")
    
    # Confirm before dropping
    response = input(f"\nDrop {len(tables_to_drop)} tables? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled.")
        return
    
    # Drop tables
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  Dropped: {table}")
        except Exception as e:
            print(f"  Error dropping {table}: {e}")
    
    # Vacuum to reclaim space
    print("\nVacuuming database...")
    conn.execute("VACUUM")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Cleanup complete!")

if __name__ == '__main__':
    cleanup_database()
```

---

## Usage

```powershell
# Dry run (see what would be dropped)
python cleanup_production_db.py

# Confirm and execute
# Script will prompt for confirmation before dropping
```

---

## Safety Checks

- ✅ Whitelist approach (only drop what's NOT needed)
- ✅ Regex patterns prevent accidental drops
- ✅ Manual confirmation required
- ✅ Backup recommended before running
