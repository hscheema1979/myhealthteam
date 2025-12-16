#!/usr/bin/env python3
import sqlite3
import sys

def investigate_column_mapping():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== INVESTIGATING COLUMN MAPPING ISSUE ===\n")

    # Check if there's a mismatch between what we think the columns are and what they contain
    print("1. Check column headers and first few data rows:")
    cursor.execute('SELECT * FROM SOURCE_PATIENT_DATA LIMIT 3')

    headers = [description[0] for description in cursor.description]
    print(f"   Headers: {headers}")

    rows = cursor.fetchall()
    for i, row in enumerate(rows, 1):
        print(f"   Row {i}: {row[:5]}...")  # Show first 5 columns

    print(f"\n2. Check the 'LAST FIRST DOB' column specifically:")
    cursor.execute('SELECT DISTINCT "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA ORDER BY "LAST FIRST DOB" LIMIT 10')
    unique_values = cursor.fetchall()
    print("   Unique values in 'LAST FIRST DOB':")
    for val in unique_values:
        print(f"     '{val[0]}'")

    print(f"\n3. Check if there's a header row being treated as data:")
    cursor.execute('SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA WHERE "Last" = "Last" OR "First" = "First" OR "DOB" = "DOB" OR "LAST FIRST DOB" = "LAST FIRST DOB"')
    header_like = cursor.fetchall()
    print(f"   Found {len(header_like)} header-like records:")
    for record in header_like[:5]:
        print(f"     {record}")

    print(f"\n4. Check for the literal 'LAST FIRST DOB' text:")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "LAST FIRST DOB" = "LAST FIRST DOB"')
    literal_count = cursor.fetchone()[0]
    print(f"   Records with literal 'LAST FIRST DOB': {literal_count}")

    print(f"\n5. Check if row 1 is a header:")
    cursor.execute('SELECT "Last", "First", "DOB", "LAST FIRST DOB" FROM SOURCE_PATIENT_DATA WHERE ROWID = 1')
    first_row = cursor.fetchone()
    print(f"   First row: {first_row}")

    print(f"\n6. Now let's see what the 4a-transform.ps1 is actually using:")

    # Let's recreate the exact query from 4a-transform.ps1 to see what happens
    query = '''
    SELECT DISTINCT 
        UPPER(TRIM(REPLACE(REPLACE(REPLACE(TRIM(spd."Last") || ' ' || TRIM(spd."First") || ' ' || TRIM(spd."DOB")), ', ', ' '), ',', ' '), '  ', ' '))) as patient_id,
        NULL as region_id,
        TRIM(spd."First") as first_name,
        TRIM(spd."Last") as last_name,
        spd."DOB" as date_of_birth
    FROM SOURCE_PATIENT_DATA spd
    WHERE spd."LAST FIRST DOB" IS NOT NULL AND spd."LAST FIRST DOB" != '' AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
      AND TRIM(spd."First") IS NOT NULL AND TRIM(spd."Last") IS NOT NULL AND spd."DOB" IS NOT NULL;
    '''

    print("   Testing the exact query from 4a-transform.ps1:")
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"   Query returned {len(results)} records")

        if results:
            print("   First few results:")
            for i, result in enumerate(results[:3], 1):
                print(f"     {i}. {result}")

    except Exception as e:
        print(f"   Query failed: {e}")

    conn.close()

if __name__ == '__main__':
    investigate_column_mapping()