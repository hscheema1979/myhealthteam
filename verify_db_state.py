import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

print("=== Tables ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%billing%'")
tables = cursor.fetchall()
for table in tables:
    print(f"  {table[0]}")

print("\n=== Views ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
views = cursor.fetchall()
for view in views:
    print(f"  {view[0]}")

print("\n=== Testing provider_tasks view ===")
try:
    cursor.execute("SELECT COUNT(*) FROM provider_tasks")
    count = cursor.fetchone()[0]
    print(f"  provider_tasks view works: {count} records")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== Testing unified_tasks view ===")
try:
    cursor.execute("SELECT COUNT(*) FROM unified_tasks LIMIT 1")
    count = cursor.fetchone()[0]
    print(f"  unified_tasks view works")
except Exception as e:
    print(f"  ERROR: {e}")

conn.close()
