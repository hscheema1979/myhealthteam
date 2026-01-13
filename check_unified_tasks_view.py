import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='unified_tasks'")
result = cursor.fetchone()

if result:
    print("unified_tasks view definition:")
    print(result[0])
else:
    print("unified_tasks view not found")

conn.close()
