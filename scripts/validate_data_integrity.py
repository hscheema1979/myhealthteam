#!/usr/bin/env python3
import sqlite3
import sys

def validate_data_integrity():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== DATA INTEGRITY VALIDATION ===\n")

    # Check source data
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA')
    total_source = cursor.fetchone()[0]
    print(f'Total source records: {total_source}')

    # Check source data with valid patient info
    query = '''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA
               WHERE "Last" IS NOT NULL AND "Last" != ""
               AND "First" IS NOT NULL AND "First" != ""
               AND "DOB" IS NOT NULL AND "DOB" != ""
               AND "LAST FIRST DOB" IS NOT NULL AND "LAST FIRST DOB" != ""
               AND "LAST FIRST DOB" != "LAST FIRST DOB"'''

    cursor.execute(query)
    valid_source = cursor.fetchone()[0]
    print(f'Valid source records: {valid_source}')

    # Check staging data
    cursor.execute('SELECT COUNT(*) FROM staging_patients')
    total_staging = cursor.fetchone()[0]
    print(f'Total staging records: {total_staging}')

    # Check for filtered records
    filtered_out = total_source - valid_source
    print(f'Records filtered out during validation: {filtered_out}')

    # Check if there are any records that should have made it to staging but didn't
    missing_in_staging = valid_source - total_staging
    print(f'Missing records in staging (should be 0): {missing_in_staging}')

    print(f'\n=== BREAKDOWN ===')
    print(f'Source total: {total_source}')
    print(f'Source valid: {valid_source}')
    print(f'Source filtered: {filtered_out}')
    print(f'Staging total: {total_staging}')
    print(f'Missing in staging: {missing_in_staging}')

    if filtered_out > 0 or missing_in_staging > 0:
        print(f'\n=== DETAILED ANALYSIS ===')

        # Show filtered records
        print('Filtered records:')
        query = '''SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA
                   WHERE "Last" IS NULL OR "Last" = ""
                   OR "First" IS NULL OR "First" = ""
                   OR "DOB" IS NULL OR "DOB" = ""
                   OR "LAST FIRST DOB" IS NULL OR "LAST FIRST DOB" = ""
                   OR "LAST FIRST DOB" = "LAST FIRST DOB"'''

        cursor.execute(query)
        filtered_records = cursor.fetchall()

        if filtered_records:
            for i, record in enumerate(filtered_records[:5]):  # Show first 5
                print(f'  {i+1}. {record}')
            if len(filtered_records) > 5:
                print(f'  ... and {len(filtered_records) - 5} more')

        # Check for duplicates that might cause issues
        print('\nChecking for duplicates in valid source:')
        query = '''SELECT "LAST FIRST DOB", COUNT(*) as count FROM SOURCE_PATIENT_DATA
                   WHERE "Last" IS NOT NULL AND "Last" != ""
                   AND "First" IS NOT NULL AND "First" != ""
                   AND "DOB" IS NOT NULL AND "DOB" != ""
                   AND "LAST FIRST DOB" IS NOT NULL AND "LAST FIRST DOB" != ""
                   AND "LAST FIRST DOB" != "LAST FIRST DOB"
                   GROUP BY "LAST FIRST DOB"
                   HAVING COUNT(*) > 1'''

        cursor.execute(query)
        duplicates = cursor.fetchall()

        if duplicates:
            for dup in duplicates:
                print(f'  DUPLICATE: {dup[0]} (count: {dup[1]})')
        else:
            print('  No duplicates found')

        print(f'\n⚠️  DATA INTEGRITY ISSUE: {missing_in_staging} records missing from staging!')

    else:
        print('✅ Data integrity looks good!')

    conn.close()

if __name__ == '__main__':
    validate_data_integrity()