#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Check workflow_instances table structure
print("=== workflow_instances table structure ===")
cursor.execute("PRAGMA table_info(workflow_instances)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]}) - {col[3] and 'NOT NULL' or 'NULL'}")

print("\n=== workflow_templates table structure ===")
cursor.execute("PRAGMA table_info(workflow_templates)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]}) - {col[3] and 'NOT NULL' or 'NULL'}")

print("\n=== workflow_steps table structure ===")
cursor.execute("PRAGMA table_info(workflow_steps)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]}) - {col[3] and 'NOT NULL' or 'NULL'}")

# Check if there are any existing workflow instances
print("\n=== Sample data from workflow_instances ===")
cursor.execute("SELECT * FROM workflow_instances LIMIT 3")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  {row}")
else:
    print("  No workflow instances found")

conn.close()