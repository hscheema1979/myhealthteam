import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "provider_tasks%"')
tables = [row[0] for row in cursor.fetchall()]
print("Provider tasks tables:")
for table in tables:
    print(f"  {table}")
    cols = conn.execute(f'PRAGMA table_info({table})').fetchall()
    print(f"    Columns: {', '.join([col[1] for col in cols])}")
conn.close()
