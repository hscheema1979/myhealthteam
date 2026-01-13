import sqlite3

conn = sqlite3.connect('production.db')

# Check if main provider_tasks table exists
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provider_tasks'")
main_exists = cursor.fetchone() is not None
print(f"Main provider_tasks table exists: {main_exists}")

# Get all provider_tasks tables
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks%' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print(f"\nAll provider_tasks tables ({len(tables)}):")
for table in tables:
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count} records")

conn.close()
