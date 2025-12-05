#!/usr/bin/env python3

import sqlite3

def check_staff_mapping():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print('Checking staff_code_mapping table columns...')
    cursor.execute('PRAGMA table_info(staff_code_mapping);')
    cols = cursor.fetchall()
    print('Columns:', [col[1] for col in cols])
    
    print('\nSample data from staff_code_mapping:')
    cursor.execute('SELECT * FROM staff_code_mapping WHERE staff_code LIKE "ZEN-%" LIMIT 5;')
    sample = cursor.fetchall()
    for row in sample:
        print(row)
    
    print('\nAll ZEN staff codes:')
    cursor.execute('SELECT * FROM staff_code_mapping WHERE staff_code LIKE "ZEN-%";')
    zen_codes = cursor.fetchall()
    for row in zen_codes:
        print(row)
    
    conn.close()

if __name__ == "__main__":
    check_staff_mapping()