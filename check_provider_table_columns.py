import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_2025_%'")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    print(f"\n{table_name}:")
    print(f"  Columns: {', '.join(col_names)}")

conn.close()
