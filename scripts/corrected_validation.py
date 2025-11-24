#!/usr/bin/env python3
import sqlite3
import sys

def corrected_validation():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== CORRECTED DATA INTEGRITY VALIDATION ===\n")

    # Check ALL source data
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA')
    total_source = cursor.fetchone()[0]
    print(f'Total source records: {total_source}')

    # Check staging data
    cursor.execute('SELECT COUNT(*) FROM staging_patients')
    total_staging = cursor.fetchone()[0]
    print(f'Total staging records: {total_staging}')

    # Check the actual WHERE clause used in 4a-transform.ps1
    # WHERE spd."LAST FIRST DOB" IS NOT NULL AND spd."LAST FIRST DOB" != '' AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
    #   AND TRIM(spd."First") IS NOT NULL AND TRIM(spd."Last") IS NOT NULL AND spd."DOB" IS NOT NULL;

    print(f'\n=== ANALYZING 4a-transform.ps1 FILTERING LOGIC ===')

    # Step 1: Check records that should be excluded by WHERE clause
    where_clause = '''WHERE ("LAST FIRST DOB" IS NOT NULL AND "LAST FIRST DOB" != "" AND "LAST FIRST DOB" != "LAST FIRST DOB"
                      AND TRIM("First") IS NOT NULL AND TRIM("Last") IS NOT NULL AND "DOB" IS NOT NULL)'''

    cursor.execute(f'SELECT COUNT(*) FROM SOURCE_PATIENT_DATA {where_clause}')
    should_be_processed = cursor.fetchone()[0]
    print(f'Records that SHOULD be processed: {should_be_processed}')
    print(f'Records in staging: {total_staging}')
    print(f'Difference (missing in staging): {total_staging - should_be_processed}')

    # Step 2: Check what records are being excluded
    excluded_clause = '''WHERE ("LAST FIRST DOB" IS NULL OR "LAST FIRST DOB" = "" OR "LAST FIRST DOB" = "LAST FIRST DOB"
                        OR TRIM("First") IS NULL OR TRIM("Last") IS NULL OR "DOB" IS NULL)'''

    cursor.execute(f'SELECT COUNT(*) FROM SOURCE_PATIENT_DATA {excluded_clause}')
    should_be_excluded = cursor.fetchone()[0]
    print(f'Records that SHOULD be excluded: {should_be_excluded}')

    # Step 3: Show examples of excluded records
    print(f'\nExcluded records (sample):')
    cursor.execute(f'SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA {excluded_clause} LIMIT 5')
    excluded_samples = cursor.fetchall()
    for i, record in enumerate(excluded_samples):
        print(f'  {i+1}. Last: "{record[0]}", First: "{record[1]}", DOB: "{record[2]}", Full: "{record[3]}"')

    # Step 4: Check if there are exactly 2 difference
    actual_difference = should_be_processed - total_staging
    if actual_difference == 2:
        print(f'\n✅ CORRECT: Exactly {actual_difference} records difference is explained by filtering logic')
    elif actual_difference == 0:
        print(f'\n✅ PERFECT: All valid records made it to staging!')
    else:
        print(f'\n⚠️  UNEXPECTED: {actual_difference} records difference cannot be explained by filtering')

    # Step 5: Check for actual duplicate patients in staging
    print(f'\n=== CHECKING FOR DUPLICATES IN STAGING ===')
    cursor.execute('SELECT patient_id, COUNT(*) FROM staging_patients GROUP BY patient_id HAVING COUNT(*) > 1')
    duplicates = cursor.fetchall()

    if duplicates:
        print(f'Found {len(duplicates)} duplicate patient IDs in staging:')
        for dup in duplicates:
            print(f'  {dup[0]}: {dup[1]} records')
    else:
        print('✅ No duplicate patient IDs in staging')

    conn.close()

if __name__ == '__main__':
    corrected_validation()