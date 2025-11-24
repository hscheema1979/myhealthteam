#!/usr/bin/env python3
"""
PRODUCTION DATABASE CLEANUP SCRIPT
Removes contaminated duplicate records and ghost records from production database
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_production_database():
    """Create backup of production database before cleanup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"../production_backup_{timestamp}.db"
    
    print(f"🔒 Creating backup: {backup_path}")
    shutil.copy2('../production.db', backup_path)
    print("✅ Backup created successfully")
    return backup_path

def cleanup_duplicate_patients():
    """Remove duplicate and ghost patient records from production"""
    print("🧹 CLEANING PRODUCTION DATABASE")
    print("=" * 50)
    
    # Create backup first
    backup_path = backup_production_database()
    print()
    
    conn = sqlite3.connect('../production.db')
    cursor = conn.cursor()
    
    # Find all duplicate patients
    cursor.execute("""
        SELECT patient_id, COUNT(*) as count 
        FROM patients 
        GROUP BY patient_id 
        HAVING COUNT(*) > 1
        ORDER BY count DESC, patient_id
    """)
    
    duplicates = cursor.fetchall()
    
    print(f"📊 Found {len(duplicates)} patients with duplicates")
    print()
    
    total_removed = 0
    cleanup_log = []
    
    for patient_id, count in duplicates:
        print(f"🗑️  Cleaning patient: {patient_id} ({count} copies)")
        
        # Get all records for this patient
        cursor.execute("""
            SELECT ROWID, first_name, last_name, date_of_birth, created_date
            FROM patients 
            WHERE patient_id = ?
            ORDER BY ROWID
        """, (patient_id,))
        
        records = cursor.fetchall()
        
        # Determine which record to keep
        if len(records) == 1:
            continue  # Shouldn't happen, but safety check
        
        # Keep the record with the most complete data
        def completeness_score(record):
            score = 0
            if record[1]:  # first_name
                score += 1
            if record[2]:  # last_name
                score += 1
            if record[3]:  # date_of_birth
                score += 1
            if record[4]:  # created_date
                score += 1
            return score
        
        # Sort by completeness and ROWID (keep older record if equal)
        records.sort(key=lambda r: (-completeness_score(r), r[0]))
        keep_record = records[0]
        remove_records = records[1:]
        
        print(f"    ✅ Keeping: ROWID {keep_record[0]} - {keep_record[1]} {keep_record[2]} {keep_record[3]}")
        
        # Remove extra records
        for record in remove_records:
            cursor.execute('DELETE FROM patients WHERE ROWID = ?', (record[0],))
            total_removed += 1
            print(f"    ❌ Removed: ROWID {record[0]} - {record[1]} {record[2]} {record[3]}")
            
            cleanup_log.append({
                'patient_id': patient_id,
                'removed_rowid': record[0],
                'data': f"{record[1]} {record[2]} {record[3]}",
                'reason': 'duplicate_removed'
            })
        
        print()
    
    # Commit changes
    conn.commit()
    
    print(f"✅ CLEANUP COMPLETE")
    print(f"📊 Summary:")
    print(f"   • Total duplicate patients cleaned: {len(duplicates)}")
    print(f"   • Total contaminated records removed: {total_removed}")
    print(f"   • Backup created: {backup_path}")
    print()
    
    # Verify cleanup
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM patients 
        GROUP BY patient_id 
        HAVING COUNT(*) > 1
    """)
    remaining_duplicates = cursor.fetchall()
    
    print(f"🔍 Post-cleanup verification:")
    print(f"   • Total patients in production: {total_patients:,}")
    print(f"   • Remaining duplicates: {len(remaining_duplicates)}")
    print()
    
    if len(remaining_duplicates) > 0:
        print("⚠️  WARNING: Some duplicates may still exist!")
        for dup in remaining_duplicates:
            print(f"   • {dup[0]} duplicates")
    
    conn.close()
    
    # Generate cleanup report
    generate_cleanup_report(cleanup_log, backup_path, total_removed, len(duplicates))
    
    return total_removed, len(duplicates)

def generate_cleanup_report(cleanup_log, backup_path, total_removed, duplicate_count):
    """Generate detailed cleanup report"""
    print("📋 CLEANUP REPORT")
    print("=" * 50)
    
    print(f"Backup file: {backup_path}")
    print(f"Cleanup date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total records removed: {total_removed}")
    print(f"Total duplicate patients cleaned: {duplicate_count}")
    print()
    
    # Analyze removal reasons
    ghost_records = [log for log in cleanup_log if log['data'].strip() == 'None None None']
    real_duplicates = [log for log in cleanup_log if log['data'].strip() != 'None None None']
    
    print("📊 Removal Analysis:")
    print(f"   • Ghost records (NULL data): {len(ghost_records)}")
    print(f"   • Real duplicate records: {len(real_duplicates)}")
    print()
    
    if ghost_records:
        print("👻 GHOST RECORDS REMOVED:")
        for log in ghost_records[:5]:  # Show first 5
            print(f"   • {log['patient_id']} (ROWID {log['removed_rowid']})")
        if len(ghost_records) > 5:
            print(f"   ... and {len(ghost_records) - 5} more ghost records")
        print()
    
    if real_duplicates:
        print("🔄 REAL DUPLICATES REMOVED:")
        for log in real_duplicates[:5]:  # Show first 5
            print(f"   • {log['patient_id']} (ROWID {log['removed_rowid']}): {log['data']}")
        if len(real_duplicates) > 5:
            print(f"   ... and {len(real_duplicates) - 5} more duplicates")
        print()

def verify_production_cleanup():
    """Verify production database is ready for staging transfer"""
    print("🔍 FINAL VERIFICATION")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get staging patients
    staging_cursor.execute("SELECT DISTINCT patient_id FROM staging_patients")
    staging_patients = {row[0] for row in staging_cursor.fetchall()}
    
    # Get clean production patients (no duplicates)
    production_cursor.execute("""
        SELECT DISTINCT p1.patient_id
        FROM patients p1
        LEFT JOIN patients p2 ON p1.patient_id = p2.patient_id AND p1.ROWID < p2.ROWID
        WHERE p2.patient_id IS NULL
    """)
    clean_production_patients = {row[0] for row in production_cursor.fetchall()}
    
    # Coverage analysis
    new_patients = staging_patients - clean_production_patients
    existing_patients = staging_patients & clean_production_patients
    
    print(f"✅ PRODUCTION DATABASE CLEANED:")
    print(f"   • Clean production patients: {len(clean_production_patients):,}")
    print(f"   • Staging patients: {len(staging_patients):,}")
    print(f"   • New patients to add: {len(new_patients):,}")
    print(f"   • Existing patients to update: {len(existing_patients):,}")
    print()
    
    if len(new_patients) > 0:
        print("🎯 TRANSFER READY:")
        print(f"   • Can safely add {len(new_patients)} new patients")
        print(f"   • Can safely update {len(existing_patients)} existing patients")
        print("   • No duplicate conflicts expected")
        print()
        return True
    else:
        print("⚠️  TRANSFER ISSUE:")
        print("   • No new patients found - review staging data")
        print()
        return False
    
    staging_conn.close()
    production_conn.close()

def main():
    """Main cleanup function"""
    if not os.path.exists('../production.db'):
        print("❌ ERROR: Production database not found")
        return False
    
    try:
        # Step 1: Clean the production database
        total_removed, duplicate_count = cleanup_duplicate_patients()
        
        # Step 2: Verify cleanup success
        transfer_ready = verify_production_cleanup()
        
        print("=" * 50)
        if transfer_ready:
            print("🎉 PRODUCTION DATABASE CLEANUP SUCCESSFUL!")
            print("✅ Ready for staging data transfer")
        else:
            print("⚠️  CLEANUP COMPLETE - Review required")
        
        return transfer_ready
        
    except Exception as e:
        print(f"❌ CLEANUP FAILED: {str(e)}")
        print("🛑 DO NOT proceed with data transfer")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Next step: Proceed with data transfer")
    else:
        print("\n🛑 Fix issues before proceeding")