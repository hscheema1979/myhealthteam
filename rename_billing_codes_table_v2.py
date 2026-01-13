import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

try:
    cursor.execute('DROP VIEW IF EXISTS unified_tasks')
    print("Dropped unified_tasks view")
    
    cursor.execute('DROP VIEW IF EXISTS unified_tasks_with_facilities')
    print("Dropped unified_tasks_with_facilities view")
    
    cursor.execute('ALTER TABLE task_billing_codes RENAME TO reference_task_billing_codes')
    print("Successfully renamed task_billing_codes to reference_task_billing_codes")
    
    conn.commit()
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
