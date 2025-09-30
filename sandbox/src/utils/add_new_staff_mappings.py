import sqlite3
from datetime import datetime

def add_new_staff_mappings():
    """
    Add new unmapped staff codes found in CSV files to staff_code_mapping table.
    These need to be mapped before running the transformation scripts.
    """
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("=== ADDING NEW STAFF CODE MAPPINGS ===")
    print()
    
    # New staff codes that were found in CSVs but not in staff_code_mapping
    new_staff_codes = [
        {
            'staff_code': 'AteDi000',
            'mapping_type': 'COORDINATOR', 
            'confidence': 'UNMATCHED',
            'notes': 'New coordinator found in CMLog_AteDi000.csv - needs manual user mapping'
        },
        {
            'staff_code': 'ZEN-DAG',
            'mapping_type': 'PROVIDER',
            'confidence': 'UNMATCHED', 
            'notes': 'New provider found in PSL_ZEN-DAG.csv - needs manual user mapping'
        },
        {
            'staff_code': 'ZEN-JAA',
            'mapping_type': 'PROVIDER',
            'confidence': 'UNMATCHED',
            'notes': 'New provider found in PSL_ZEN-JAA.csv - needs manual user mapping'
        },
        {
            'staff_code': 'ZEN-KAJ', 
            'mapping_type': 'PROVIDER',
            'confidence': 'UNMATCHED',
            'notes': 'New provider found in PSL_ZEN-KAJ.csv - needs manual user mapping'
        },
        {
            'staff_code': 'ZEN-MEC',
            'mapping_type': 'PROVIDER', 
            'confidence': 'UNMATCHED',
            'notes': 'New provider found in PSL_ZEN-MEC.csv - needs manual user mapping'
        }
    ]
    
    # Check which codes are already in the mapping table
    existing_codes = []
    for code_info in new_staff_codes:
        cursor.execute(
            "SELECT staff_code FROM staff_code_mapping WHERE staff_code = ?", 
            (code_info['staff_code'],)
        )
        if cursor.fetchone():
            existing_codes.append(code_info['staff_code'])
            print(f"⚠ {code_info['staff_code']} already exists in mapping table")
    
    # Add new codes that don't exist
    added_count = 0
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for code_info in new_staff_codes:
        if code_info['staff_code'] not in existing_codes:
            try:
                cursor.execute("""
                    INSERT INTO staff_code_mapping 
                    (staff_code, user_id, confidence_level, mapping_type, notes, created_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    code_info['staff_code'],
                    None,  # user_id is NULL for unmatched codes
                    code_info['confidence'], 
                    code_info['mapping_type'],
                    code_info['notes'],
                    current_time
                ))
                
                print(f"✓ Added {code_info['staff_code']} ({code_info['mapping_type']})")
                added_count += 1
                
            except Exception as e:
                print(f"✗ Error adding {code_info['staff_code']}: {e}")
    
    # Commit changes
    conn.commit()
    
    print()
    print(f"Added {added_count} new staff code mappings")
    
    # Show current mapping status
    print()
    print("=== CURRENT MAPPING STATUS FOR NEW CODES ===")
    cursor.execute("""
        SELECT staff_code, user_id, confidence_level, mapping_type, notes 
        FROM staff_code_mapping 
        WHERE staff_code IN ('AteDi000', 'ZEN-DAG', 'ZEN-JAA', 'ZEN-KAJ', 'ZEN-MEC')
        ORDER BY mapping_type, staff_code
    """)
    
    results = cursor.fetchall()
    for row in results:
        staff_code, user_id, confidence, mapping_type, notes = row
        status = f"→ User ID {user_id}" if user_id else "→ UNMAPPED"
        print(f"{staff_code} ({mapping_type}): {confidence} {status}")
    
    print()
    print("⚠ WARNING: These codes have NULL user_id values.")
    print("   The transformation scripts will:")
    print("   - Use the raw staff_code as the coordinator_id/provider_id")
    print("   - Use the raw staff_code as the provider_name")
    print()
    print("🔧 TO FIX: Update staff_code_mapping with proper user_id values")
    print("   or create new users in the users/coordinators/providers tables")
    
    conn.close()

if __name__ == "__main__":
    add_new_staff_mappings()