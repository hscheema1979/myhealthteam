#!/usr/bin/env python3
import sqlite3
import sys

def test_fixed_query():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== TESTING FIXED QUERY ===\n")

    # Fixed query - I need to escape the quotes properly in the WHERE clause
    print("1. Test the correct WHERE clause:")
    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"''')
    step1_count = cursor.fetchone()[0]
    print(f"   Step 1 count: {step1_count}")

    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL
                      AND TRIM("Last") IS NOT NULL
                      AND "DOB" IS NOT NULL''')
    final_count = cursor.fetchone()[0]
    print(f"   Final count: {final_count}")

    print(f"\n2. If the WHERE clause works, let's see the data:")
    if final_count > 0:
        cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA
                          WHERE "LAST FIRST DOB" IS NOT NULL
                          AND "LAST FIRST DOB" != ""
                          AND "LAST FIRST DOB" != "LAST FIRST DOB"
                          AND TRIM("First") IS NOT NULL
                          AND TRIM("Last") IS NOT NULL
                          AND "DOB" IS NOT NULL
                          LIMIT 5''')
        samples = cursor.fetchall()
        print("   Sample records that should be processed:")
        for i, sample in enumerate(samples, 1):
            print(f"     {i}. {sample}")

    print(f"\n3. Check what's causing the WHERE clause to fail:")

    # Check individual conditions
    print("   a) Records with 'LAST FIRST DOB' = 'LAST FIRST DOB' (literal):")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "LAST FIRST DOB" = "LAST FIRST DOB"')
    literal_count = cursor.fetchone()[0]
    print(f"        Count: {literal_count}")

    print("   b) Records with 'LAST FIRST DOB' IS NULL:")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "LAST FIRST DOB" IS NULL')
    null_count = cursor.fetchone()[0]
    print(f"        Count: {null_count}")

    print("   c) Records with 'LAST FIRST DOB' = '' (empty):")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "LAST FIRST DOB" = ""')
    empty_count = cursor.fetchone()[0]
    print(f"        Count: {empty_count}")

    print(f"\n4. Let's check if the issue is with the CSV import - maybe header row was included:")
    print("   Looking for header-like data:")
    cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA
                      WHERE "Last" = "Last" OR "First" = "First" OR "DOB" = "DOB" LIMIT 3''')
    headers = cursor.fetchall()
    for i, header in enumerate(headers, 1):
        print(f"     {i}. {header}")

    print(f"\n5. Now let's test if 4a-transform.ps1 actually worked despite the WHERE issue:")
    print("   Checking staging_patients to see what data made it in:")

    cursor.execute('SELECT COUNT(*) FROM staging_patients')
    staging_count = cursor.fetchone()[0]
    print(f"   staging_patients count: {staging_count}")

    if staging_count > 0:
        cursor.execute('SELECT patient_id, first_name, last_name, date_of_birth FROM staging_patients LIMIT 5')
        staging_samples = cursor.fetchall()
        print("   Sample from staging_patients:")
        for i, sample in enumerate(staging_samples, 1):
            print(f"     {i}. {sample}")

        print(f"\n   Checking for duplicates in staging_patients:")
        cursor.execute('SELECT patient_id, COUNT(*) FROM staging_patients GROUP BY patient_id HAVING COUNT(*) > 1 LIMIT 3')
        duplicates = cursor.fetchall()
        for dup in duplicates:
            print(f"     DUPLICATE: {dup[0]} appears {dup[1]} times")

    conn.close()

if __name__ == '__main__':
    test_fixed_query()