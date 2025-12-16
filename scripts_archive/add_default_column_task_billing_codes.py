"""Add an `is_default` column to task_billing_codes if it doesn't exist.
Run: python scripts/add_default_column_task_billing_codes.py
This is non-destructive (ADD COLUMN) and safe; it will not overwrite data.
"""
import sqlite3
DB = 'production.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
# Check existing columns
cols = [r[1] for r in c.execute("PRAGMA_TABLE_INFO('task_billing_codes')").fetchall()] if False else None
# Use pragma correctly
c.execute("PRAGMA table_info('task_billing_codes')")
info = c.fetchall()
col_names = [row[1] for row in info]
if 'is_default' in col_names:
    print('Column is_default already exists in task_billing_codes')
else:
    print('Adding is_default column to task_billing_codes')
    c.execute("ALTER TABLE task_billing_codes ADD COLUMN is_default INTEGER DEFAULT 0")
    conn.commit()
    print('Added column is_default with default 0')

conn.close()
