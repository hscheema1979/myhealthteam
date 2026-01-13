import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.execute('PRAGMA table_info(provider_task_billing_status)')
cols = cursor.fetchall()
print("provider_task_billing_status columns:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")
print()

cursor = conn.execute('PRAGMA table_info(provider_weekly_payroll_status)')
cols = cursor.fetchall()
print("provider_weekly_payroll_status columns:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")
print()

cursor = conn.execute('PRAGMA table_info(provider_weekly_summary_with_billing)')
cols = cursor.fetchall()
print("provider_weekly_summary_with_billing columns:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")
conn.close()
