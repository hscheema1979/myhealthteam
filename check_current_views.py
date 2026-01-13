import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
views = cursor.fetchall()

print('Current views in database:')
for view in views:
    print(f"  - {view[0]}")

if not views:
    print('  (No views found)')

conn.close()
