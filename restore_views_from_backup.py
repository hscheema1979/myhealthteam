import sqlite3

backup_db = 'db-sync/backups/production_backup_20260112_002108.db'
current_db = 'production.db'

backup_conn = sqlite3.connect(backup_db)
backup_cursor = backup_conn.cursor()

backup_cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
views = backup_cursor.fetchall()

current_conn = sqlite3.connect(current_db)
current_cursor = current_conn.cursor()

try:
    for view_name, view_sql in views:
        print(f"Restoring view: {view_name}")
        current_cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
        current_cursor.execute(view_sql)
        print(f"  -> Restored")
    
    current_conn.commit()
    print("\nAll views restored successfully!")
except Exception as e:
    print(f"Error: {e}")
    current_conn.rollback()
finally:
    backup_conn.close()
    current_conn.close()
