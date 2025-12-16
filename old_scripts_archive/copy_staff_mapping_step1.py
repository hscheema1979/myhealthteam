#!/usr/bin/env python3
"""
STEP 1: Copy staff_code_mapping table from backup to production for review
"""

import sqlite3
import shutil
from datetime import datetime

def copy_staff_code_mapping_only():
    """Copy only the staff_code_mapping table from backup to production"""
    
    print("STEP 1: Copying staff_code_mapping table for review...")
    
    # Connect to both databases
    backup_conn = sqlite3.connect('production_backup_prototype_test.db')
    prod_conn = sqlite3.connect('production.db')
    
    try:
        # Step 1: Create staff_code_mapping table in production if it doesn't exist
        print("\nCreating staff_code_mapping table in production...")
        prod_conn.execute('''
            CREATE TABLE IF NOT EXISTS staff_code_mapping (
                staff_code TEXT PRIMARY KEY,
                user_id INTEGER,
                confidence_level TEXT CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'UNMATCHED')),
                mapping_type TEXT CHECK (mapping_type IN ('PROVIDER', 'COORDINATOR', 'SPECIAL_CASE')),
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES "users"(user_id)
            )
        ''')
        
        # Step 2: Copy staff_code_mapping data
        print("Copying staff code mappings...")
        backup_cursor = backup_conn.execute('SELECT * FROM staff_code_mapping')
        mappings = backup_cursor.fetchall()
        
        # Clear existing mappings first
        prod_conn.execute('DELETE FROM staff_code_mapping')
        
        # Insert new mappings
        for mapping in mappings:
            prod_conn.execute('''
                INSERT INTO staff_code_mapping (staff_code, user_id, confidence_level, mapping_type, notes, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', mapping)
        
        print(f"SUCCESS: Copied {len(mappings)} staff code mappings")
        
        # Commit changes
        prod_conn.commit()
        print("\nSUCCESS: staff_code_mapping table copied successfully!")
        
        # Display the mappings for review
        print("\nSTAFF CODE MAPPINGS FOR REVIEW:")
        print("=" * 60)
        cursor = prod_conn.execute('SELECT * FROM staff_code_mapping ORDER BY staff_code')
        all_mappings = cursor.fetchall()
        
        for mapping in all_mappings:
            print(f"Staff Code: {mapping[0]} → User ID: {mapping[1]} ({mapping[2]} confidence, {mapping[3]} type)")
            
        print("=" * 60)
        print(f"Total mappings: {len(all_mappings)}")
        
        # Check for our specific coordinator codes
        print("\nCOORDINATOR-SPECIFIC MAPPINGS:")
        coord_codes = ['AteDi000', 'HerHe000', 'SobJo000', 'EstJa000', 'PerJo000', 'RioMa000', 'SanBi000']
        for code in coord_codes:
            cursor = prod_conn.execute('SELECT * FROM staff_code_mapping WHERE staff_code = ?', (code,))
            mapping = cursor.fetchone()
            if mapping:
                print(f"FOUND: {code}: User ID {mapping[1]} ({mapping[3]})")
            else:
                print(f"MISSING: {code}: Not found")
        
    except Exception as e:
        prod_conn.rollback()
        print(f"❌ Error during copy: {e}")
        raise
    finally:
        backup_conn.close()
        prod_conn.close()

def main():
    """Main execution function"""
    
    print("STEP 1: COPY STAFF CODE MAPPING TABLE")
    print("=" * 60)
    print("This will copy the staff_code_mapping table from backup to production")
    print("for review before proceeding with the full restoration.")
    print("=" * 60)
    
    copy_staff_code_mapping_only()
    
    print("\nREVIEW COMPLETE!")
    print("SUCCESS: staff_code_mapping table copied to production")
    print("Review the mappings above to ensure they look correct")
    print("\nNEXT: Approve to proceed with full restoration (missing users + roles)")

if __name__ == "__main__":
    main()