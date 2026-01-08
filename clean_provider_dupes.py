import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Find entries without DOB that have matching entries WITH DOB
query = """
SELECT
    bad.provider_task_id,
    bad.patient_id as bad_pid,
    good.provider_task_id as good_pid,
    good.patient_id as good_pid
FROM provider_tasks_2025_12 bad
JOIN provider_tasks_2025_12 good ON (
    bad.provider_name = good.provider_name AND
    bad.task_date = good.task_date AND
    bad.task_description = good.task_description AND
    bad.patient_id NOT LIKE '%/%' AND
    good.patient_id LIKE '% %/%/%'
)
WHERE bad.source_system = 'CSV_IMPORT'
"""

# First, let's see all entries without DOB
print("=== Entries WITHOUT DOB ===")
no_dob = cursor.execute("""
    SELECT provider_task_id, provider_name, patient_id, task_date, task_description
    FROM provider_tasks_2025_12
    WHERE patient_id NOT LIKE '%/%'
""").fetchall()

for row in no_dob:
    print(f"ID: {row[0]}, Provider: {row[1]}, Patient: '{row[2]}', Date: {row[3]}, Task: {row[4]}")

print(f"\nTotal entries without DOB: {len(no_dob)}")

# Now find matching entries WITH DOB
print("\n=== Finding matching entries WITH DOB ===")
to_delete = []
for bad_row in no_dob:
    bad_id, provider, bad_patient, task_date, task_desc = bad_row

    # Try to find a matching entry with DOB - must match patient name (case-insensitive)
    # Extract name parts from bad_patient (e.g., "Anderson Jefforie")
    bad_upper = bad_patient.upper().replace(' ', '').replace('-', '')

    # Get all entries with DOB for same provider/date/task
    candidates = cursor.execute("""
        SELECT provider_task_id, patient_id
        FROM provider_tasks_2025_12
        WHERE provider_name = ?
        AND task_date = ?
        AND task_description = ?
        AND patient_id LIKE '% %/%/%'
        AND source_system = 'CSV_IMPORT'
    """, (provider, task_date, task_desc)).fetchall()

    for cand_id, cand_patient in candidates:
        # Extract name from candidate (remove DOB portion)
        # Format: "LAST FIRST MM/DD/YYYY"
        parts = cand_patient.split()
        if len(parts) >= 3:
            # Reconstruct name without DOB
            cand_name_only = ' '.join(parts[:-1])  # Everything except last part (DOB)
            cand_upper = cand_name_only.upper().replace(' ', '').replace('-', '')

            # Check if names match (allowing for slight variations)
            if bad_upper == cand_upper or bad_upper in cand_upper or cand_upper in bad_upper:
                to_delete.append((bad_id, bad_patient, cand_id, cand_patient))
                print(f"DELETE ID {bad_id} ('{bad_patient}') -> KEEP ID {cand_id} ('{cand_patient}')")
                break

print(f"\nTotal duplicates to delete: {len(to_delete)}")

# Show entries without DOB that have NO match (these won't be deleted)
print("\n=== Entries WITHOUT DOB that have NO match (will NOT be deleted) ===")
matched_ids = [t[0] for t in to_delete]
for row in no_dob:
    if row[0] not in matched_ids:
        print(f"ID: {row[0]}, Patient: '{row[2]}', Date: {row[3]}")

# Perform deletion
if to_delete:
    print(f"\n=== DELETING {len(to_delete)} duplicate entries ===")
    delete_ids = [t[0] for t in to_delete]
    placeholders = ','.join(['?' for _ in delete_ids])
    cursor.execute(f"""
        DELETE FROM provider_tasks_2025_12
        WHERE provider_task_id IN ({placeholders})
    """, delete_ids)
    conn.commit()
    print(f"Deleted {cursor.rowcount} entries")
else:
    print("\nNo entries to delete")

# Verify deletion
remaining = cursor.execute("""
    SELECT COUNT(*) FROM provider_tasks_2025_12
    WHERE patient_id NOT LIKE '%/%'
""").fetchone()
print(f"\nRemaining entries without DOB: {remaining[0]}")

conn.close()
