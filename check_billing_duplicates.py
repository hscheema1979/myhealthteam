"""Script to identify duplicates in provider_task_billing_status table"""
import sqlite3
import pandas as pd

conn = sqlite3.connect("production.db")

# Check for duplicate provider_task_ids
query = """
SELECT 
    provider_task_id,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(billing_status_id) as status_ids,
    GROUP_CONCAT(billing_week) as weeks,
    GROUP_CONCAT(is_carried_over) as carried_over_flags
FROM provider_task_billing_status
GROUP BY provider_task_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 20
"""

print("=" * 80)
print("DUPLICATES IN provider_task_billing_status TABLE")
print("=" * 80)
duplicates = pd.read_sql_query(query, conn)
if not duplicates.empty:
    print(duplicates.to_string(index=False))
    print(f"\nTotal duplicate groups: {len(duplicates)}")
else:
    print("No duplicates found")

# Check for duplicate rows (exact same provider_task_id, billing_week, is_carried_over)
print("\n" + "=" * 80)
print("EXACT DUPLICATE ROWS (same provider_task_id + billing_week + is_carried_over)")
print("=" * 80)

query2 = """
SELECT 
    provider_task_id,
    billing_week,
    is_carried_over,
    COUNT(*) as exact_dupes,
    GROUP_CONCAT(billing_status_id) as status_ids
FROM provider_task_billing_status
GROUP BY provider_task_id, billing_week, is_carried_over
HAVING COUNT(*) > 1
"""

exact_duplicates = pd.read_sql_query(query2, conn)
if not exact_duplicates.empty:
    print(exact_duplicates.to_string(index=False))
    print(f"\nTotal exact duplicate groups: {len(exact_duplicates)}")
else:
    print("No exact duplicates found")

# Sample of first duplicate to see pattern
if not duplicates.empty:
    first_duplicate_id = duplicates.iloc[0]['provider_task_id']
    print("\n" + "=" * 80)
    print(f"SAMPLE DETAIL FOR provider_task_id = {first_duplicate_id}")
    print("=" * 80)
    
    sample_query = """
    SELECT * FROM provider_task_billing_status
    WHERE provider_task_id = ?
    ORDER BY created_date, billing_status_id
    """
    sample = pd.read_sql_query(sample_query, conn, params=[first_duplicate_id])
    print(sample.to_string(index=False))

conn.close()
