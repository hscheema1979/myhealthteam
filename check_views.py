import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
views = cursor.fetchall()
print("Views in database:")
for view in views:
    print(f"\n{view[0]}:")
    print(f"  {view[1]}")
conn.close()
