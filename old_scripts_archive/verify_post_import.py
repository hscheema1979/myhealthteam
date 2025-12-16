import sqlite3

conn = sqlite3.connect('production.db')

print("="*60)
print("POST-IMPORT VERIFICATION")
print("="*60)

tables = {
    'provider_weekly_summary_with_billing': 'Summary of provider tasks by week',
    'coordinator_monthly_summary': 'Summary of coordinator tasks by month',
    'patient_monthly_billing_2025_10': 'October patient billing',
    'provider_task_billing_status': 'Billing workflow status',
    'audit_log': 'System audit log',
    'provider_tasks': 'Provider tasks view (all months)',
    'coordinator_tasks': 'Coordinator tasks view (all months)'
}

print("\nSUMMARY TABLES:")
for table, desc in tables.items():
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        status = "✅" if count > 0 or table == 'audit_log' else "⚠️"
        print(f"{status} {table:40} {count:6} rows - {desc}")
    except Exception as e:
        print(f"❌ {table:40} ERROR: {e}")

print("\nPATIENT PANEL LAST VISIT UPDATE:")
try:
    with_visits = conn.execute("SELECT COUNT(*) FROM patient_panel WHERE last_visit_date IS NOT NULL").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM patient_panel").fetchone()[0]
    print(f"✅ {with_visits}/{total} patients have last_visit_date")
except Exception as e:
    print(f"❌ ERROR: {e}")

conn.close()

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)
