import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%'")
tables = [r[0] for r in cursor.fetchall()]

total_zen = 0
for t in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {t} WHERE notes LIKE '%paid by zen%'")
        count = cursor.fetchone()[0]
        total_zen += count
        if count > 0:
            print(f"{t}: {count} tasks with 'paid by zen' in notes")
    except Exception as e:
        print(f"Error checking {t}: {e}")

print(f"\nTotal tasks paid by zen: {total_zen}")

# Also check provider_task_billing_status since it's the source for payroll
try:
    cursor.execute("SELECT COUNT(*) FROM provider_task_billing_status WHERE notes LIKE '%paid by zen%'")
    count = cursor.fetchone()[0]
    print(f"provider_task_billing_status: {count} tasks with 'paid by zen' in notes")
except Exception as e:
    print(f"Error checking provider_task_billing_status: {e}")

conn.close()
