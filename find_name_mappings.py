#!/usr/bin/env python3

import sqlite3

def find_name_mappings():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("LOOKING FOR NAME MAPPINGS")
    print("=" * 50)
    
    # Check staff_code_mapping table
    print("1. STAFF CODE MAPPING TABLE:")
    cursor.execute('PRAGMA table_info(staff_code_mapping);')
    mapping_cols = cursor.fetchall()
    print(f"   Columns: {[col[1] for col in mapping_cols]}")
    
    cursor.execute('SELECT * FROM staff_code_mapping LIMIT 10;')
    mapping_data = cursor.fetchall()
    print(f"   Sample data:")
    for row in mapping_data:
        print(f"     {row}")
    
    # Check SOURCE_STAFF_INFO table
    print("\n2. SOURCE STAFF INFO TABLE:")
    cursor.execute('PRAGMA table_info(SOURCE_STAFF_INFO);')
    staff_cols = cursor.fetchall()
    print(f"   Columns: {[col[1] for col in staff_cols]}")
    
    cursor.execute('SELECT * FROM SOURCE_STAFF_INFO LIMIT 10;')
    staff_data = cursor.fetchall()
    print(f"   Sample data:")
    for row in staff_data:
        print(f"     {row}")
    
    # Check staff_codes table
    print("\n3. STAFF CODES TABLE:")
    cursor.execute('PRAGMA table_info(staff_codes);')
    codes_cols = cursor.fetchall()
    print(f"   Columns: {[col[1] for col in codes_cols]}")
    
    cursor.execute('SELECT * FROM staff_codes LIMIT 10;')
    codes_data = cursor.fetchall()
    print(f"   Sample data:")
    for row in codes_data:
        print(f"     {row}")
    
    # Look for mapping between coordinator/provider IDs and full names
    print("\n4. SEARCHING FOR MAPPINGS...")
    
    # Try to map coordinator codes to names
    coordinator_codes = ['ESTJA000', 'RIOMA000', 'SANBI000', 'SOBJO000']
    provider_codes = ['ZEN-SZA', 'ZEN-VIL']
    
    # Check if any tables have both code and full name
    tables_to_check = ['staff_code_mapping', 'SOURCE_STAFF_INFO', 'staff_codes']
    
    for table in tables_to_check:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        col_names = [col[1] for col in cols]
        
        if any('name' in col.lower() for col in col_names) and any('code' in col.lower() for col in col_names):
            print(f"   Table {table} has both name and code columns: {col_names}")
            
            # Try to find specific mappings
            cursor.execute(f"SELECT * FROM {table};")
            all_data = cursor.fetchall()
            
            # Check if any of our codes appear in this data
            all_codes = set(coordinator_codes + provider_codes)
            found_mappings = []
            
            for row in all_data:
                row_str = str(row)
                for code in all_codes:
                    if code in row_str:
                        found_mappings.append((code, row))
            
            if found_mappings:
                print(f"     Found mappings:")
                for code, row in found_mappings:
                    print(f"       {code} -> {row}")
    
    conn.close()

if __name__ == "__main__":
    find_name_mappings()