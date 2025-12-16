#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION DATABASE CLEANUP
Removes all contaminated placeholder records and restores database integrity
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_production_database():
    """Create timestamped backup of production database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"../production_backup_contaminated_{timestamp}.db"
    
    print(f"🔒 Creating backup: {backup_path}")
    shutil.copy2('../production.db', backup_path)
    print(f"✅ Backup created successfully: {backup_path}")
    return backup_path

def identify_contaminated_records():
    """Identify all contaminated patient records to remove"""
    print("🔍 IDENTIFYING CONTAMINATED RECORDS")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get staging patients (legitimate data)
    staging_cursor.execute("SELECT DISTINCT patient_id FROM staging_patients")
    staging_patients = {row[0] for row in staging_cursor.fetchall()}
    
    # Get all production patients
    production_cursor.execute("SELECT DISTINCT patient_id FROM patients")
    production_patients = {row[0] for row in production_cursor.fetchall()}
    
    # Find production-only patients (contaminated records)
    contaminated_patients = production_patients - staging_patients
    
    print(f"📊 ANALYSIS RESULTS:")
    print(f"   • Staging patients (legitimate): {len(staging_patients):,}")
    print(f"   • Production patients (total): {len(production_patients):,}")
    print(f"   • Contaminated patients to remove: {len(contaminated_patients):,}")
    
    staging_conn.close()
    production_conn.close()
    
    return contaminated_patients

def cleanup_contaminated_records(contaminated_patients):
    """Remove all contaminated patient records from production"""
    print(f"\n🧹 CLEANING CONTAMINATED RECORDS")
    print("=" * 50)
    
    # Create backup first
    backup_path = backup_production_database()
    print()
    
    conn = sqlite3.connect('../production.db')
    cursor = conn.cursor()
    
    # Remove contaminated patient records
    print(f"🗑️  Removing {len(contaminated_patients)} contaminated patients...")
    
    # Convert set to list for SQL IN clause
    patient_list = list(contaminated_patients)
    
    # Remove patients in batches to avoid SQL limits
    batch_size = 100
    removed_count = 0
    
    for i in range(0, len(patient_list), batch_size):
        batch = patient_list[i:i + batch_size]
        placeholders = ','.join(['?' for _ in batch])
        
        cursor.execute(f"""
            DELETE FROM patients 
            WHERE patient_id IN ({placeholders})
        """, batch)
        
        batch_removed = cursor.rowcount
        removed_count += batch_removed
        
        print(f"   • Removed batch {i//batch_size + 1}: {batch_removed} records")
    
    # Also remove any duplicate records that weren't caught
    cursor.execute("""
        SELECT patient_id, COUNT(*) as count 
        FROM patients 
        GROUP BY patient_id 
        HAVING COUNT(*) > 1
    """)
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"   • Removing additional duplicate records...")
        for patient_id, count in duplicates:
            # Keep one record, remove others
            cursor.execute("""
                DELETE FROM patients 
                WHERE patient_id = ? AND ROWID NOT IN (
                    SELECT MIN(ROWID) FROM patients WHERE patient_id = ?
                )
            """, (patient_id, patient_id))
            removed_count += cursor.rowcount
    
    conn.commit()
    
    print(f"\n✅ CLEANUP COMPLETE")
    print(f"📊 Total contaminated records removed: {removed_count:,}")
    
    # Verify cleanup success
    cursor.execute("SELECT COUNT(*) FROM patients")
    remaining_patients = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM patients 
        GROUP BY patient_id 
        HAVING COUNT(*) > 1
    """)
    remaining_duplicates = cursor.fetchall()
    
    print(f"🔍 Post-cleanup verification:")
    print(f"   • Remaining patients in production: {remaining_patients:,}")
    print(f"   • Remaining duplicates: {len(remaining_duplicates)}")
    
    conn.close()
    
    return removed_count

def verify_superset_principle():
    """Verify that staging is now a proper superset of production"""
    print(f"\n🔍 VERIFYING SUPERSET PRINCIPLE")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get clean patient sets
    staging_cursor.execute("SELECT DISTINCT patient_id FROM staging_patients")
    staging_patients = {row[0] for row in staging_cursor.fetchall()}
    
    production_cursor.execute("SELECT DISTINCT patient_id FROM patients")
    production_patients = {row[0] for row in production_cursor.fetchall()}
    
    # Check superset relationship
    production_only = production_patients - staging_patients
    new_patients = staging_patients - production_patients
    
    print(f"📊 SUPERSET VERIFICATION:")
    print(f"   • Staging patients: {len(staging_patients):,}")
    print(f"   • Production patients: {len(production_patients):,}")
    print(f"   • Production-only patients: {len(production_only):,}")
    print(f"   • New patients in staging: {len(new_patients):,}")
    print()
    
    if len(production_only) == 0:
        print("✅ SUPERSET PRINCIPLE RESTORED!")
        print("   • Staging contains ALL production patients")
        print("   • Production contains NO patients outside staging")
        print("   • Database is now clean and ready for transfer")
        result = True
    else:
        print("❌ SUPERSET PRINCIPLE VIOLATION!")
        print(f"   • {len(production_only)} patients still exist only in production")
        print("   • Additional cleanup required")
        result = False
    
    staging_conn.close()
    production_conn.close()
    
    return result

def generate_cleanup_summary(backup_path, removed_count, success):
    """Generate summary of cleanup operation"""
    print(f"\n📋 CLEANUP SUMMARY")
    print("=" * 50)
    
    print(f"Operation date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backup file: {backup_path}")
    print(f"Records removed: {removed_count:,}")
    
    if success:
        print(f"Status: ✅ SUCCESSFUL")
        print(f"Database state: CLEAN AND READY FOR TRANSFER")
    else:
        print(f"Status: ❌ INCOMPLETE")
        print(f"Database state: REQUIRES ADDITIONAL CLEANUP")
    
    print()
    print("🚀 NEXT STEPS:")
    if success:
        print("   1. ✅ Proceed with October 2025 data transfer")
        print("   2. 🔍 Verify billing views work correctly")
        print("   3. 📊 Monitor system performance post-transfer")
    else:
        print("   1. 🔍 Investigate remaining production-only patients")
        print("   2. 🧹 Continue cleanup until superset principle is restored")
        print("   3. ✅ Only then proceed with data transfer")

def main():
    """Execute comprehensive production database cleanup"""
    print("🚀 COMPREHENSIVE PRODUCTION DATABASE CLEANUP")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not os.path.exists('../production.db'):
        print("❌ ERROR: Production database not found")
        return False
    
    try:
        # Step 1: Identify contaminated records
        contaminated_patients = identify_contaminated_records()
        
        if len(contaminated_patients) == 0:
            print("✅ No contaminated records found - database appears clean")
            return verify_superset_principle()
        
        # Step 2: Remove contaminated records
        removed_count = cleanup_contaminated_records(contaminated_patients)
        
        # Step 3: Verify superset principle restored
        success = verify_superset_principle()
        
        # Step 4: Generate summary
        backup_path = f"../production_backup_contaminated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        generate_cleanup_summary(backup_path, removed_count, success)
        
        return success
        
    except Exception as e:
        print(f"❌ CLEANUP FAILED: {str(e)}")
        print("🛑 DO NOT proceed with data transfer")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 DATABASE CLEANUP SUCCESSFUL!")
        print("🚀 Ready for October 2025 data transfer")
    else:
        print("\n🛑 CLEANUP INCOMPLETE - Manual intervention required")