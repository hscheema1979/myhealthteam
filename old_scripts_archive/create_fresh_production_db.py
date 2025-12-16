# create_fresh_production_db.py
# Copy infrastructure tables to fresh production.db

import sqlite3
import shutil
from datetime import datetime

# Backup current production.db
backup_name = f"production_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
print(f"Creating backup: {backup_name}")
shutil.copy('production.db', f'backups/{backup_name}')

# Tables to copy (infrastructure only - not derived from CSVs)
INFRASTRUCTURE_TABLES = [
    'users',
    'roles', 
    'user_roles',
    'facilities',
    'task_billing_codes',
    'audit_log',  # Keep for compliance
]

# Connect to old and new databases
old_db = sqlite3.connect('production.db')
new_db = sqlite3.connect('production_fresh.db')

print("\nCopying infrastructure tables...")

for table in INFRASTRUCTURE_TABLES:
    try:
        # Get table schema
        schema = old_db.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'").fetchone()
        
        if schema:
            # Create table in new database
            new_db.execute(schema[0])
            print(f"  ✓ Created table: {table}")
            
            # Copy data
            rows = old_db.execute(f"SELECT * FROM {table}").fetchall()
            if rows:
                # Get column count
                col_count = len(rows[0])
                placeholders = ','.join(['?' for _ in range(col_count)])
                new_db.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
                print(f"    Copied {len(rows)} rows")
        else:
            print(f"  ⚠ Table not found: {table}")
            
    except Exception as e:
        print(f"  ✗ Error copying {table}: {e}")

# Commit and close
new_db.commit()
old_db.close()
new_db.close()

print("\n✅ Fresh database created: production_fresh.db")
print("\nNext steps:")
print("1. Review production_fresh.db")
print("2. If satisfied, rename: production_fresh.db → production.db")
print("3. Run: .\\refresh_production_data.ps1")
