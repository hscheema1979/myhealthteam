#!/usr/bin/env python3
import sqlite3
import sys

def detailed_analysis():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== DETAILED DATA INTEGRITY ANALYSIS ===\n")

    # 1. Check the exact WHERE logic from 4a-transform.ps1
    print("=== CHECKING 4a-transform.ps1 WHERE CLAUSE LOGIC ===")

    # The actual WHERE clause from 4a-transform.ps1:
    # WHERE spd."LAST FIRST DOB" IS NOT NULL AND spd."LAST FIRST DOB" != '' AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    #   AND TRIM(spd."First") IS NOT NULL AND TRIM(spd."Last") IS NOT NULL AND spd."DOB" IS NOT NULL;

    # Let's test this step by step
    print("Step 1: Last First DOB is not null and not empty and not 'LAST FIRST DOB'")
    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"''')
    step1 = cursor.fetchone()[0]
    print(f"  Records passing step 1: {step1}")

    print("Step 2: TRIM(First) is not null")
    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL''')
    step2 = cursor.fetchone()[0]
    print(f"  Records passing step 2: {step2}")

    print("Step 3: TRIM(Last) is not null")
    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL
                      AND TRIM("Last") IS NOT NULL''')
    step3 = cursor.fetchone()[0]
    print(f"  Records passing step 3: {step3}")

    print("Step 4: DOB is not null (final)")
    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL
                      AND TRIM("Last") IS NOT NULL
                      AND "DOB" IS NOT NULL''')
    step4 = cursor.fetchone()[0]
    print(f"  Records passing final step: {step4}")

    # 2. Check what's failing at each step
    print(f'\n=== CHECKING RECORDS FAILING EACH STEP ===')

    print("Records failing final step but passing step 3 (missing DOB):")
    cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL
                      AND TRIM("Last") IS NOT NULL
                      AND ("DOB" IS NULL OR "DOB" = "")
                      LIMIT 5''')
    failing_dob = cursor.fetchall()
    for record in failing_dob:
        print(f'  Last: "{record[0]}", First: "{record[1]}", DOB: "{record[2]}", Full: "{record[3]}"')

    print("\nRecords failing step 3 (missing Last or First after TRIM):")
    cursor.execute('''SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA
                      WHERE "LAST FIRST DOB" IS NOT NULL
                      AND "LAST FIRST DOB" != ""
                      AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND (TRIM("First") IS NULL OR TRIM("Last") IS NULL OR TRIM("First") = "" OR TRIM("Last") = "")
                      LIMIT 5''')
    failing_names = cursor.fetchall()
    for record in failing_names:
        print(f'  Last: "{record[0]}", First: "{record[1]}", DOB: "{record[2]}", Full: "{record[3]}"')

    # 3. Analyze the duplicates
    print(f'\n=== DUPLICATE ANALYSIS ===')
    cursor.execute('''SELECT patient_id, COUNT(*) as count, 
                      GROUP_CONCAT(first_name || ' ' || last_name, ' | ') as names,
                      GROUP_CONCAT(date_of_birth, ' | ') as dobs
                      FROM staging_patients
                      GROUP BY patient_id
                      HAVING COUNT(*) > 1''')

    duplicates = cursor.fetchall()
    print(f"Found {len(duplicates)} duplicate patient groups:")

    for dup in duplicates:
        print(f"\nPatient ID: {dup[0]} (appears {dup[1]} times)")
        print(f"  Names: {dup[2]}")
        print(f"  DOBs: {dup[3]}")

    # 4. Check if the issue is with DISTINCT in the CREATE TABLE statement
    print(f'\n=== CHECKING CREATE TABLE LOGIC ===')
    print("The 4a-transform.ps1 uses: CREATE TABLE staging_patients AS SELECT DISTINCT ...")
    print("But we found duplicates, so let's see why DISTINCT didn't work")

    # Check if any duplicates are actually identical
    cursor.execute('''SELECT patient_id, first_name, last_name, date_of_birth, COUNT(*) as count
                      FROM staging_patients
                      GROUP BY patient_id, first_name, last_name, date_of_birth
                      HAVING COUNT(*) > 1''')

    exact_duplicates = cursor.fetchall()
    if exact_duplicates:
        print(f"\nFound {len(exact_duplicates)} EXACT duplicate records:")
        for dup in exact_duplicates:
            print(f"  {dup[0]}, {dup[1]}, {dup[2]}, {dup[3]}: {dup[4]} times")
    else:
        print("\nNo EXACT duplicates found - duplicates have different data")

    conn.close()

if __name__ == '__main__':
    detailed_analysis()