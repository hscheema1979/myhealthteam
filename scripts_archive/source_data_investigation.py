#!/usr/bin/env python3
import sqlite3
import sys

def investigate_source_data():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== INVESTIGATING SOURCE DATA ISSUES ===\n")

    # Check what's actually in the source data
    print("1. Sample records from SOURCE_PATIENT_DATA:")
    cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA LIMIT 10''')
    samples = cursor.fetchall()

    for i, (last, first, dob, full) in enumerate(samples, 1):
        print(f"  {i}. Last='{last}', First='{first}', DOB='{dob}', Full='{full}'")

    print(f"\n2. Check for NULL vs empty string issues:")

    # Check for NULL vs empty string
    cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB", 
                      CASE WHEN "Last" IS NULL THEN 'NULL' ELSE 'NOT_NULL' END as last_type,
                      CASE WHEN "First" IS NULL THEN 'NULL' ELSE 'NOT_NULL' END as first_type,
                      CASE WHEN "DOB" IS NULL THEN 'NULL' ELSE 'NOT_NULL' END as dob_type
                      FROM SOURCE_PATIENT_DATA LIMIT 5''')

    type_samples = cursor.fetchall()
    print("   Data types check:")
    for record in type_samples:
        print(f"     {record}")

    print(f"\n3. Check why TRIM might be failing:")

    # Check if there are spaces causing TRIM issues
    cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB",
                      LENGTH(TRIM("Last")) as trimmed_last_len,
                      LENGTH(TRIM("First")) as trimmed_first_len,
                      TRIM("Last") as trimmed_last,
                      TRIM("First") as trimmed_first
                      FROM SOURCE_PATIENT_DATA LIMIT 5''')

    trim_samples = cursor.fetchall()
    print("   TRIM analysis:")
    for record in trim_samples:
        print(f"     Last='{record[3]}', TRIM Last len={record[4]}, TRIM Last='{record[6]}'")

    print(f"\n4. Test the exact WHERE clause step by step:")

    # Test exact WHERE clause components
    print("   a) Check 'LAST FIRST DOB' != '':")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "LAST FIRST DOB" != ""')
    not_empty = cursor.fetchone()[0]
    print(f"      Records where 'LAST FIRST DOB' != '': {not_empty}")

    print("   b) Check 'LAST FIRST DOB' != 'LAST FIRST DOB':")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "LAST FIRST DOB" != "LAST FIRST DOB"')
    not_header = cursor.fetchone()[0]
    print(f"      Records where 'LAST FIRST DOB' != 'LAST FIRST DOB': {not_header}")

    print("   c) Check TRIM(First) IS NOT NULL:")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE TRIM("First") IS NOT NULL')
    first_not_null = cursor.fetchone()[0]
    print(f"      Records where TRIM(First) IS NOT NULL: {first_not_null}")

    print("   d) Check TRIM(Last) IS NOT NULL:")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE TRIM("Last") IS NOT NULL')
    last_not_null = cursor.fetchone()[0]
    print(f"      Records where TRIM(Last) IS NOT NULL: {last_not_null}")

    print("   e) Check 'DOB' IS NOT NULL:")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "DOB" IS NOT NULL')
    dob_not_null = cursor.fetchone()[0]
    print(f"      Records where 'DOB' IS NOT NULL: {dob_not_null}")

    print(f"\n5. Now test combination:")

    print("   f) Check 'LAST FIRST DOB' != '' AND != 'LAST FIRST DOB':")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "LAST FIRST DOB" != "" AND "LAST FIRST DOB" != "LAST FIRST DOB"')
    step1 = cursor.fetchone()[0]
    print(f"      Records passing step 1: {step1}")

    print("   g) Check ALL conditions combined:")
    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA 
                      WHERE "LAST FIRST DOB" != "" 
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL
                      AND TRIM("Last") IS NOT NULL
                      AND "DOB" IS NOT NULL''')
    all_combined = cursor.fetchone()[0]
    print(f"      Records passing ALL conditions: {all_combined}")

    print(f"\n6. Check what records are failing the DOB condition specifically:")
    cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB",
                      CASE WHEN "DOB" IS NULL THEN 'NULL' 
                           WHEN "DOB" = "" THEN 'EMPTY' 
                           ELSE 'HAS_VALUE' END as dob_status
                      FROM SOURCE_PATIENT_DATA 
                      WHERE "LAST FIRST DOB" != "" 
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL
                      AND TRIM("Last") IS NOT NULL
                      LIMIT 10''')

    dob_failing = cursor.fetchall()
    print("   Records failing DOB condition:")
    for record in dob_failing:
        print(f"     {record}")

    conn.close()

if __name__ == '__main__':
    investigate_source_data()