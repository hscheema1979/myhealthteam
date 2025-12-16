#!/usr/bin/env python3
"""
SIMPLIFIED PATIENT TRANSFER
Transfers only core common patient fields between staging and production
"""

import sqlite3
import shutil
from datetime import datetime

def transfer_patients_simplified():
    """Transfer patients using only core common columns"""
    print("🚀 SIMPLIFIED PATIENT TRANSFER")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get new patients
    staging_cursor.execute("SELECT DISTINCT patient_id FROM staging_patients")
    staging_patients = {row[0] for row in staging_cursor.fetchall()}
    
    production_cursor.execute("SELECT DISTINCT patient_id FROM patients")
    production_patients = {row[0] for row in production_cursor.fetchall()}
    
    new_patients = staging_patients - production_patients
    
    print(f"📊 New patients to transfer: {len(new_patients)}")
    
    if len(new_patients) == 0:
        print("✅ No new patients to transfer")
        staging_conn.close()
        production_conn.close()
        return 0
    
    # Transfer with minimal core columns
    transferred_count = 0
    
    for patient_id in new_patients:
        try:
            staging_cursor.execute("""
                SELECT patient_id, first_name, last_name, date_of_birth, gender,
                       phone_primary, address_street, address_city, address_state, address_zip,
                       insurance_primary, created_date, last_first_dob
                FROM staging_patients 
                WHERE patient_id = ?
            """, (patient_id,))
            
            patient_data = staging_cursor.fetchone()
            
            if patient_data:
                production_cursor.execute("""
                    INSERT INTO patients (
                        patient_id, first_name, last_name, date_of_birth, gender,
                        phone_primary, address_street, address_city, address_state, address_zip,
                        insurance_primary, created_date, last_first_dob
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, patient_data)
                transferred_count += 1
                
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping patient {patient_id}: {e}")
        except Exception as e:
            print(f"   ❌ Error transferring patient {patient_id}: {e}")
    
    production_conn.commit()
    
    print(f"✅ Transferred {transferred_count} new patients")
    
    staging_conn.close()
    production_conn.close()
    
    return transferred_count

def quick_transfer_verification():
    """Quick verification of transfer"""
    print(f"\n🔍 QUICK VERIFICATION")
    print("=" * 50)
    
    production_conn = sqlite3.connect('../production.db')
    cursor = production_conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]
    
    print(f"📊 Total patients in production: {total_patients:,}")
    
    # Expected: 512 original + 101 new = 613 total
    expected = 613
    if total_patients == expected:
        print(f"✅ Transfer successful: {total_patients:,} patients (expected {expected:,})")
    else:
        print(f"⚠️  Patient count mismatch: {total_patients:,} (expected {expected:,})")
    
    production_conn.close()

def main():
    """Main simplified transfer"""
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"../production_backup_simplified_{timestamp}.db"
        shutil.copy2('../production.db', backup_path)
        print(f"🔒 Backup created: {backup_path}")
        
        # Transfer patients
        transferred = transfer_patients_simplified()
        
        # Quick verification
        quick_transfer_verification()
        
        print(f"\n🎉 SIMPLIFIED TRANSFER COMPLETE!")
        if transferred > 0:
            print(f"✅ {transferred} new patients added to production")
            print(f"🚀 Ready for October 2025 task transfer")
        else:
            print(f"⚠️  No patients transferred - may need investigation")
            
    except Exception as e:
        print(f"❌ Transfer failed: {e}")

if __name__ == "__main__":
    main()