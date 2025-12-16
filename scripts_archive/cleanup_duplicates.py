#!/usr/bin/env python3
import sqlite3
import sys

def cleanup_duplicates():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== CLEANING UP DUPLICATE PATIENT RECORDS ===\n")

    # 1. Find all duplicates
    cursor.execute('''SELECT patient_id, COUNT(*) as count FROM staging_patients 
                      GROUP BY patient_id HAVING COUNT(*) > 1 ORDER BY patient_id''')
    duplicates = cursor.fetchall()

    print(f"Found {len(duplicates)} duplicate patient groups:")
    for dup in duplicates:
        print(f"  - {dup[0]}: {dup[1]} records")

    if len(duplicates) == 0:
        print("✅ No duplicates found!")
        return

    # 2. Remove duplicates (keep first occurrence, remove others)
    total_duplicates_removed = 0
    print(f"\n🧹 Removing duplicates...")

    for dup_patient_id, count in duplicates:
        print(f"  Processing: {dup_patient_id} (keeping first, removing {count-1})")

        # Get all records for this patient ID
        cursor.execute('''SELECT ROWID, patient_id, first_name, last_name, date_of_birth 
                          FROM staging_patients WHERE patient_id = ? ORDER BY ROWID''', (dup_patient_id,))
        patient_records = cursor.fetchall()

        # Remove all but the first record
        records_to_remove = patient_records[1:]  # Skip first, remove rest
        for record in records_to_remove:
            # Remove from staging_patients
            cursor.execute('DELETE FROM staging_patients WHERE ROWID = ?', (record[0],))

            # Remove corresponding records from other staging tables
            print(f"    Removing record ID: {record[0]}")

            # Remove from staging_patient_assignments
            cursor.execute('DELETE FROM staging_patient_assignments WHERE patient_id = ?', (record[1],))

            # Remove from staging_patient_panel  
            cursor.execute('DELETE FROM staging_patient_panel WHERE patient_id = ?', (record[1],))

            total_duplicates_removed += 1

    # 3. Commit changes
    conn.commit()
    print(f"\n✅ Removed {total_duplicates_removed} duplicate records")

    # 4. Verify cleanup
    print(f"\n🔍 Verifying cleanup...")

    # Check for remaining duplicates
    cursor.execute('SELECT COUNT(*) as count FROM staging_patients GROUP BY patient_id HAVING COUNT(*) > 1')
    remaining_duplicates = cursor.fetchall()

    if len(remaining_duplicates) == 0:
        print("✅ All duplicates removed successfully!")
    else:
        print(f"❌ Still have {len(remaining_duplicates)} duplicate groups")

    # Check record counts
    cursor.execute('SELECT COUNT(*) FROM staging_patients')
    final_patient_count = cursor.fetchone()[0]
    print(f"Final staging_patients count: {final_patient_count}")

    cursor.execute('SELECT COUNT(*) FROM staging_patient_assignments')
    final_assignments_count = cursor.fetchone()[0]
    print(f"Final staging_patient_assignments count: {final_assignments_count}")

    cursor.execute('SELECT COUNT(*) FROM staging_patient_panel')
    final_panel_count = cursor.fetchone()[0]
    print(f"Final staging_patient_panel count: {final_panel_count}")

    # 5. Validate data integrity
    print(f"\n📊 Data Integrity Check:")
    cursor.execute('SELECT COUNT(*) FROM staging_patients WHERE first_name IS NOT NULL AND last_name IS NOT NULL AND date_of_birth IS NOT NULL')
    valid_records = cursor.fetchone()[0]
    print(f"  Valid records: {valid_records}/{final_patient_count}")

    if valid_records == final_patient_count:
        print("✅ All records have complete patient data")
    else:
        print("⚠️ Some records missing patient data")

    conn.close()

if __name__ == '__main__':
    cleanup_duplicates()