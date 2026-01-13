import sqlite3

backup_db = 'db-sync/backups/production_backup_20260112_002108.db'

conn = sqlite3.connect(backup_db)
cursor = conn.cursor()

cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
views = cursor.fetchall()

print(f"Views in backup ({len(views)}):")
for view_name, view_sql in views:
    print(f"\n-- View: {view_name}")
    print(view_sql)

conn.close()
