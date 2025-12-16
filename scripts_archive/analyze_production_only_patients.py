#!/usr/bin/env python3
"""
ANALYZE PRODUCTION-ONLY PATIENTS
Identify production patients not in staging (breaking superset principle)
"""

import sqlite3

def analyze_production_only_patients():
    """Find and analyze production patients not in staging"""
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
    
    # Find production patients NOT in staging (problematic ones)
    production_only = clean_production_patients - staging_patients
    
    print(f"🔍 PRODUCTION PATIENTS NOT IN STAGING: {len(production_only)}")
    print(f"   These break the superset principle!")
    print()
    
    # Analyze first 10 production-only patients
    sample_patients = list(production_only)[:10]
    
    print("📋 ANALYSIS OF PRODUCTION-ONLY PATIENTS:")
    print("=" * 60)
    
    for i, patient_id in enumerate(sample_patients):
        print(f"\n{i+1}. Production-only patient: {patient_id}")
        
        # Check production data quality
        production_cursor.execute("""
            SELECT first_name, last_name, date_of_birth, 
                   address_street, address_city, address_state, address_zip,
                   phone_primary, phone_secondary, email, created_date
            FROM patients 
            WHERE patient_id = ?
            LIMIT 1
        """, (patient_id,))
        production_data = production_cursor.fetchone()
        
        if production_data:
            print(f"   Name: {production_data[0]} {production_data[1]} {production_data[2]}")
            print(f"   Address: {production_data[3]} {production_data[4]}, {production_data[5]} {production_data[6]}")
            print(f"   Phone: {production_data[7]} {production_data[8]}")
            print(f"   Email: {production_data[9]}")
            print(f"   Created: {production_data[10]}")
            
            # Check data quality
            has_name = bool(production_data[0] and production_data[1])
            has_dob = bool(production_data[2])
            has_address = bool(production_data[3] and production_data[4])
            has_phone = bool(production_data[7])
            
            print(f"   Data Quality: Name={has_name} DOB={has_dob} Address={has_address} Phone={has_phone}")
            
            if not has_name and not has_dob:
                print("   🚨 LIKELY PLACEHOLDER/GHOST RECORD!")
    
    print()
    print("📊 SUMMARY STATISTICS:")
    print(f"   Production-only patients: {len(production_only):,}")
    print(f"   Staging patients: {len(staging_patients):,}")
    print(f"   Total production patients: {len(clean_production_patients):,}")
    
    # Get data quality summary for all production-only patients
    if production_only:
        production_cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN first_name IS NOT NULL AND first_name != '' AND 
                           last_name IS NOT NULL AND last_name != '' THEN 1 END) as has_name,
                COUNT(CASE WHEN date_of_birth IS NOT NULL AND date_of_birth != '' THEN 1 END) as has_dob,
                COUNT(CASE WHEN address_street IS NOT NULL AND address_street != '' THEN 1 END) as has_address,
                COUNT(CASE WHEN phone_primary IS NOT NULL AND phone_primary != '' THEN 1 END) as has_phone
            FROM patients 
            WHERE patient_id IN ({})
        """.format(','.join(['?' for _ in production_only])), list(production_only))
        
        quality_stats = production_cursor.fetchone()
        
        print()
        print("📈 DATA QUALITY BREAKDOWN:")
        print(f"   Total production-only patients: {quality_stats[0]:,}")
        print(f"   Have complete names: {quality_stats[1]:,} ({quality_stats[1]/quality_stats[0]*100:.1f}%)")
        print(f"   Have DOB: {quality_stats[2]:,} ({quality_stats[2]/quality_stats[0]*100:.1f}%)")
        print(f"   Have addresses: {quality_stats[3]:,} ({quality_stats[3]/quality_stats[0]*100:.1f}%)")
        print(f"   Have phone: {quality_stats[4]:,} ({quality_stats[4]/quality_stats[0]*100:.1f}%)")
    
    staging_conn.close()
    production_conn.close()

if __name__ == "__main__":
    analyze_production_only_patients()