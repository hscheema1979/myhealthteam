import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE task_billing_codes RENAME TO reference_task_billing_codes')
    conn.commit()
    print("Successfully renamed task_billing_codes to reference_task_billing_codes")
except Exception as e:
    print(f"Error renaming table: {e}")
finally:
    conn.close()
