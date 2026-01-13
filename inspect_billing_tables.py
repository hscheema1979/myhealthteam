import sqlite3
import os

db_path = 'production.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables_to_check = ['provider_weekly_payroll_status', 'provider_task_billing_status']

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (" + ",".join([f"'{t}'" for t in tables_to_check]) + ")")
found_tables = [row[0] for row in cursor.fetchall()]

print(f"Tables found: {found_tables}")

for table in found_tables:
    print(f"\n--- Schema for {table} ---")
    cursor.execute(f"PRAGMA table_info({table})")
    cols = cursor.fetchall()
    for col in cols:
        print(col)
    
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")
    
    if count > 0:
        print(f"Sample data (first 3 rows):")
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

conn.close()
