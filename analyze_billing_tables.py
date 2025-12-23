import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = [row[0] for row in cursor.fetchall()]

print("=" * 80)
print("BILLING-RELATED TABLES IN DATABASE")
print("=" * 80)

billing_tables = [t for t in all_tables if 'billing' in t.lower() or 'summary' in t.lower()]

for table in billing_tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"\n{table}: {count} rows")
    
    # Show columns
    cursor.execute(f"PRAGMA table_info({table})")
    cols = cursor.fetchall()
    print(f"  Columns: {', '.join([col[1] for col in cols])}")

print("\n" + "=" * 80)
print("TABLE USAGE IN PYTHON CODE")
print("=" * 80)

# Check which billing tables are referenced in dashboards
import os
import re

python_files = []
for root, dirs, files in os.walk('src/dashboards'):
    for f in files:
        if f.endswith('.py'):
            python_files.append(os.path.join(root, f))

for f in python_files:
    with open(f, 'r') as file:
        content = file.read()
        for table in billing_tables:
            if table in content:
                count = content.count(table)
                print(f"\n{os.path.basename(f)}: uses '{table}' ({count} times)")

print("\n" + "=" * 80)
print("WHICH TABLES ARE EMPTY/UNUSED")
print("=" * 80)

for table in billing_tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    if count == 0:
        print(f"  {table}: EMPTY - potentially unused")
    else:
        print(f"  {table}: {count} records - IN USE")

conn.close()
