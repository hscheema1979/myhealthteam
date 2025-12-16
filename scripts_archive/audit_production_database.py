#!/usr/bin/env python3
"""
CRITICAL PRODUCTION DATABASE AUDIT
Identifies and diagnoses data contamination issues in production database
"""

import sqlite3
import os
from datetime import datetime
from collections import defaultdict

def audit_production_database():
    """Comprehensive audit of production database contamination"""
    print("🚨 CRITICAL PRODUCTION DATABASE AUDIT")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    production_conn = sqlite3.connect('../production.db')
    staging_conn = sqlite3.connect('sheets_data.db')
    
    production_cursor = production_conn.cursor()
    staging_cursor = staging_conn.cursor()
    
    # 1. DUPLICATE PATIENT ANALYSIS
    print("1. DUPLICATE PATIENT ANALYSIS")
    print("-" * 40)
    
    production_cursor.execute("""
        SELECT patient_id, COUNT(*) as count 
        FROM patients 
        GROUP BY patient_id 
        HAVING COUNT(*) > 1
        ORDER BY count DESC, patient_id
    """)
    
    duplicates = production_cursor.fetchall()
    
    print(f"🚨 FOUND {len(duplicates)} DUPLICATE PATIENT IDS:")
    print()
    
    total_duplicate_records = 0
    contamination_analysis = []
    
    for patient_id, count in duplicates:
        total_duplicate_records += count
        
        # Get all records for this duplicate patient
        production_cursor.execute("""
            SELECT ROWID, patient_id, first_name, last_name, date_of_birth, created_date
            FROM patients 
            WHERE patient_id = ?
            ORDER BY ROWID
        """, (patient_id,))
        
        records = production_cursor.fetchall()
        
        # Check if this patient exists in staging
        staging_cursor.execute("""
            SELECT COUNT(*) FROM staging_patients WHERE patient_id = ?
        """, (patient_id,))
        staging_exists = staging_cursor.fetchone()[0] > 0
        
        contamination_analysis.append({
            'patient_id': patient_id,
            'production_count': count,
            'staging_exists': staging_exists,
            'records': records
        })
        
        print(f"Patient: {patient_id}")
        print(f"  Production copies: {count}")
        print(f"  In staging data: {'✅ YES' if staging_exists else '❌ NO'}")
        print("  Records:")
        
        for record in records:
            print(f"    ROWID {record[0]}: {record[2]} {record[3]} {record[4]} ({record[5]})")
        print()
    
    print(f"SUMMARY:")
    print(f"  Total duplicate patients: {len(duplicates)}")
    print(f"  Total duplicate records: {total_duplicate_records}")
    print(f"  Extra records created: {total_duplicate_records - len(duplicates)}")
    print()
    
    # 2. STAGING PATIENT COVERAGE ANALYSIS
    print("2. STAGING PATIENT COVERAGE")
    print("-" * 40)
    
    staging_cursor.execute("SELECT DISTINCT patient_id FROM staging_patients")
    staging_patients = {row[0] for row in staging_cursor.fetchall()}
    
    production_cursor.execute("SELECT DISTINCT patient_id FROM patients")
    production_patients = {row[0] for row in production_cursor.fetchall()}
    
    # Clean production patients (no duplicates)
    clean_production = set()
    duplicate_patients = set()
    
    for patient_id in production_patients:
        production_cursor.execute("""
            SELECT COUNT(*) FROM patients WHERE patient_id = ?
        """, (patient_id,))
        count = production_cursor.fetchone()[0]
        
        if count == 1:
            clean_production.add(patient_id)
        else:
            duplicate_patients.add(patient_id)
    
    # Coverage analysis
    staging_in_clean_production = staging_patients & clean_production
    staging_in_duplicate_production = staging_patients & duplicate_patients
    staging_not_in_production = staging_patients - production_patients
    
    print(f"Staging patients: {len(staging_patients):,}")
    print(f"Clean production patients: {len(clean_production):,}")
    print(f"Duplicate production patients: {len(duplicate_patients):,}")
    print()
    
    print("COVERAGE ANALYSIS:")
    print(f"  Staging patients in clean production: {len(staging_in_clean_production):,} ({len(staging_in_clean_production)/len(staging_patients)*100:.1f}%)")
    print(f"  Staging patients in duplicate production: {len(staging_in_duplicate_production):,} ({len(staging_in_duplicate_production)/len(staging_patients)*100:.1f}%)")
    print(f"  Staging patients NOT in production: {len(staging_not_in_production):,} ({len(staging_not_in_production)/len(staging_patients)*100:.1f}%)")
    print()
    
    # 3. DATA INTEGRITY CHECK
    print("3. DATA INTEGRITY CHECK")
    print("-" * 40)
    
    # Check patient name consistency for duplicate patients
    consistency_issues = []
    
    for patient_id in duplicate_patients:
        production_cursor.execute("""
            SELECT first_name, last_name, date_of_birth 
            FROM patients 
            WHERE patient_id = ?
        """, (patient_id,))
        
        records = production_cursor.fetchall()
        
        # Check if all records have same name/DOB
        first_record = records[0]
        inconsistent = False
        
        for record in records[1:]:
            if (record[0] != first_record[0] or 
                record[1] != first_record[1] or 
                record[2] != first_record[2]):
                inconsistent = True
                break
        
        if inconsistent:
            consistency_issues.append({
                'patient_id': patient_id,
                'records': records
            })
    
    print(f"CONSISTENCY ANALYSIS:")
    print(f"  Total duplicate patients: {len(duplicate_patients)}")
    print(f"  Inconsistent duplicate records: {len(consistency_issues)}")
    
    if consistency_issues:
        print(f"  🚨 CRITICAL: Found {len(consistency_issues)} patients with inconsistent duplicate records!")
        for issue in consistency_issues:
            print(f"    Patient: {issue['patient_id']}")
            for record in issue['records']:
                print(f"      {record[0]} {record[1]} {record[2]}")
    print()
    
    # 4. RECOMMENDED CLEANUP STRATEGY
    print("4. RECOMMENDED CLEANUP STRATEGY")
    print("-" * 40)
    
    print("🔧 CLEANUP ACTIONS REQUIRED:")
    print()
    
    print("A. CLEAN DUPLICATE PATIENT RECORDS:")
    print(f"   • Identify {len(duplicate_patients)} patients with duplicates")
    print(f"   • Keep only ONE record per patient")
    print(f"   • Prefer record with most complete data")
    print(f"   • Backup contaminated records before deletion")
    print()
    
    print("B. VERIFY DATA INTEGRITY:")
    if consistency_issues:
        print(f"   • CRITICAL: {len(consistency_issues)} patients have inconsistent duplicates")
        print(f"   • Manual review required before cleanup")
    else:
        print(f"   • ✅ All duplicate records have consistent name/DOB")
    print()
    
    print("C. RESTORE CORRECT PRODUCTION STATE:")
    print(f"   • Remove {total_duplicate_records - len(duplicates)} contaminated records")
    print(f"   • Production should contain ~{len(clean_production)} clean patients")
    print(f"   • Then staging can properly transfer +{len(staging_not_in_production)} new patients")
    print()
    
    # 5. SAMPLE DATA FOR MANUAL VERIFICATION
    print("5. SAMPLE CONTAMINATED DATA")
    print("-" * 40)
    
    print("First 5 duplicate patients (for manual verification):")
    for i, analysis in enumerate(contamination_analysis[:5]):
        print(f"{i+1}. {analysis['patient_id']} ({analysis['production_count']} copies)")
        for j, record in enumerate(analysis['records']):
            print(f"   Copy {j+1}: {record[2]} {record[3]} {record[4]}")
    
    production_conn.close()
    staging_conn.close()
    
    print()
    print("=" * 60)
    print("🚨 AUDIT COMPLETE - IMMEDIATE ACTION REQUIRED")
    print()
    print("❌ CRITICAL FINDINGS:")
    print(f"   • {len(duplicate_patients)} patients have duplicate records")
    print(f"   • {total_duplicate_records - len(duplicates)} extra records created")
    if consistency_issues:
        print(f"   • {len(consistency_issues)} patients have inconsistent data")
    print()
    print("⚠️  TRANSFER CANNOT PROCEED until production database is cleaned")

def main():
    """Main audit function"""
    if not os.path.exists('../production.db'):
        print("❌ ERROR: Production database not found")
        return
    
    audit_production_database()

if __name__ == "__main__":
    main()