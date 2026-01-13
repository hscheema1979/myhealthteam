import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%billing%"')
tables = [row[0] for row in cursor.fetchall()]
print("Billing-related tables:", tables)

for table in tables:
    print(f"\n{table} schema:")
    cols = conn.execute(f'PRAGMA table_info({table})').fetchall()
    for col in cols:
        print(f"  {col[1]} {col[2]}")

conn.close()
