import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = cursor.fetchall()
    
    for view in views:
        view_name = view[0]
        cursor.execute(f'DROP VIEW IF EXISTS {view_name}')
        print(f"Dropped view: {view_name}")
    
    cursor.execute('ALTER TABLE task_billing_codes RENAME TO reference_task_billing_codes')
    print("Successfully renamed task_billing_codes to reference_task_billing_codes")
    
    conn.commit()
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()