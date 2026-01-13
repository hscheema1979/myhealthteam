import sqlite3

conn = sqlite3.connect('production.db')

# Check for provider_tasks (non-monthly)
cursor = conn.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="provider_tasks"')
provider_tasks_exists = cursor.fetchone()
print(f"provider_tasks table exists: {provider_tasks_exists is not None}")
if provider_tasks_exists:
    cols = conn.execute('PRAGMA table_info(provider_tasks)').fetchall()
    print(f"  Columns: {', '.join([col[1] for col in cols])}")

# Check for weekly_billing_summary
cursor = conn.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%billing%"')
billing_tables = [row[0] for row in cursor.fetchall()]
print("\nBilling-related tables:")
for table in billing_tables:
    print(f"  {table}")
    cols = conn.execute(f'PRAGMA table_info({table})').fetchall()
    print(f"    Columns: {', '.join([col[1] for col in cols])}")

conn.close()
