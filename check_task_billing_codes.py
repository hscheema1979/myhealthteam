import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.execute('PRAGMA table_info(task_billing_codes)')
cols = cursor.fetchall()
print("task_billing_codes columns:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")
print()

cursor = conn.execute('SELECT * FROM task_billing_codes LIMIT 5')
rows = cursor.fetchall()
print("Sample data from task_billing_codes:")
for row in rows:
    print(f"  {row}")
conn.close()
