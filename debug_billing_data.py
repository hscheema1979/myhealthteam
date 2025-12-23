import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Check what's in provider_tasks_2025_12
cursor.execute("""
    SELECT COUNT(*) as total_records,
           COUNT(CASE WHEN billing_code IS NULL THEN 1 END) as null_billing_code,
           COUNT(CASE WHEN billing_code = 'Not_Billable' THEN 1 END) as not_billable,
           COUNT(CASE WHEN task_description LIKE '%pur%' THEN 1 END) as pur_descriptions
    FROM provider_tasks_2025_12
""")
result = cursor.fetchone()
print("provider_tasks_2025_12 Analysis:")
print(f"  Total records: {result[0]}")
print(f"  NULL billing_code: {result[1]}")
print(f"  'Not_Billable': {result[2]}")
print(f"  'pur' in description: {result[3]}")

# Check what's actually in provider_task_billing_status for December 2025
cursor.execute("""
    SELECT COUNT(*) as total_in_status
    FROM provider_task_billing_status
    WHERE billing_week LIKE '2025-5%'
""")
result = cursor.fetchone()
print(f"\nprovider_task_billing_status (December 2025 weeks): {result[0]}")

# Check the exact billing weeks in December 2025
cursor.execute("""
    SELECT DISTINCT billing_week
    FROM provider_task_billing_status
    WHERE strftime('%Y', week_start_date) = '2025' AND strftime('%m', week_start_date) >= '12'
    ORDER BY billing_week
""")
print("\nBilling weeks in provider_task_billing_status for Dec 2025:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Check provider_tasks_2025_12 task_date distribution
cursor.execute("""
    SELECT strftime('%Y-%W', task_date) as billing_week, COUNT(*) as count
    FROM provider_tasks_2025_12
    GROUP BY strftime('%Y-%W', task_date)
    ORDER BY billing_week
""")
print("\nTask dates in provider_tasks_2025_12 (by ISO week):")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} records")

# Show sample records with NULL billing_code
cursor.execute("""
    SELECT provider_id, task_description, billing_code, task_date
    FROM provider_tasks_2025_12
    WHERE billing_code IS NULL
    LIMIT 3
""")
print("\nSample records with NULL billing_code:")
for row in cursor.fetchall():
    print(f"  Provider {row[0]}: {row[1][:50]} | Code: {row[2]} | Date: {row[3]}")

# Check if ensure_billing_data_populated filters are too strict
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN billing_code IS NOT NULL THEN 1 END) as has_code,
           COUNT(CASE WHEN billing_code != 'Not_Billable' THEN 1 END) as not_not_billable,
           COUNT(CASE WHEN task_date IS NOT NULL THEN 1 END) as has_date,
           COUNT(CASE WHEN provider_id IS NOT NULL THEN 1 END) as has_provider
    FROM provider_tasks_2025_12
""")
result = cursor.fetchone()
print("\nFilter analysis for ensure_billing_data_populated:")
print(f"  Total: {result[0]}")
print(f"  Has billing_code (not NULL): {result[1]}")
print(f"  Not 'Not_Billable': {result[2]}")
print(f"  Has task_date: {result[3]}")
print(f"  Has provider_id: {result[4]}")

conn.close()
