#!/usr/bin/env python3
"""
Diagnostic script to identify why patient_panel table has NULL provider/coordinator names
when the data exists in patient_assignments and users tables.
"""

import sqlite3
import sys

def get_db():
    return sqlite3.connect("production.db")

def diagnose_patient_panel_issue():
    """Diagnose the patient_panel population issue"""
    conn = get_db()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DIAGNOSING PATIENT_PANEL ISSUE")
    print("=" * 80)
    
    # 1. Check total records
    cursor.execute("SELECT COUNT(*) FROM patient_panel")
    total_panel = cursor.fetchone()[0]
    print(f"Total patient_panel records: {total_panel}")
    
    # 2. Check records with missing names
    cursor.execute("""
        SELECT COUNT(*) FROM patient_panel 
        WHERE care_provider_name IS NULL OR care_provider_name = ''
           OR care_coordinator_name IS NULL OR care_coordinator_name = ''
    """)
    missing_names = cursor.fetchone()[0]
    print(f"Records with missing provider/coordinator names: {missing_names}")
    
    # 3. Check specific problematic records
    cursor.execute("""
        SELECT patient_id, provider_id, coordinator_id, care_provider_name, care_coordinator_name
        FROM patient_panel 
        WHERE care_provider_name IS NULL OR care_provider_name = ''
           OR care_coordinator_name IS NULL OR care_coordinator_name = ''
        LIMIT 5
    """)
    
    print("\nProblematic records in patient_panel:")
    for row in cursor.fetchall():
        patient_id, provider_id, coordinator_id, provider_name, coordinator_name = row
        print(f"  {patient_id}: provider_id={provider_id}, coordinator_id={coordinator_id}")
        print(f"    provider_name='{provider_name}', coordinator_name='{coordinator_name}'")
        
        # Check what should be the correct names
        cursor.execute("""
            SELECT pa.provider_id, pa.coordinator_id, u_prov.full_name, u_coord.full_name
            FROM patient_assignments pa
            LEFT JOIN users u_prov ON pa.provider_id = u_prov.user_id
            LEFT JOIN users u_coord ON pa.coordinator_id = u_coord.user_id
            WHERE pa.patient_id = ? AND pa.status = 'active'
        """, (patient_id,))
        
        assignment = cursor.fetchone()
        if assignment:
            pa_provider_id, pa_coordinator_id, correct_provider_name, correct_coordinator_name = assignment
            print(f"    SHOULD BE: provider_id={pa_provider_id}, coordinator_id={pa_coordinator_id}")
            print(f"    SHOULD BE: provider_name='{correct_provider_name}', coordinator_name='{correct_coordinator_name}'")
        else:
            print(f"    NO ASSIGNMENT FOUND!")
        print()
    
    # 4. Test the exact SQL query from transformation script
    print("Testing transformation script SQL query...")
    test_query = """
    SELECT
        p.patient_id,
        COALESCE(pa.provider_id, 0) as provider_id,
        COALESCE(pa.coordinator_id, 0) as coordinator_id,
        CASE WHEN pa.provider_id > 0 THEN u_prov.full_name ELSE NULL END as care_provider_name,
        CASE WHEN pa.coordinator_id > 0 THEN u_coord.full_name ELSE NULL END as care_coordinator_name
    FROM patients p
    LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id AND pa.status = 'active'
    LEFT JOIN users u_prov ON pa.provider_id = u_prov.user_id
    LEFT JOIN users u_coord ON pa.coordinator_id = u_coord.user_id
    WHERE p.patient_id IN (
        SELECT patient_id FROM patient_panel 
        WHERE care_provider_name IS NULL OR care_provider_name = ''
           OR care_coordinator_name IS NULL OR care_coordinator_name = ''
        LIMIT 3
    )
    """
    
    cursor.execute(test_query)
    print("Results from transformation SQL query:")
    for row in cursor.fetchall():
        patient_id, provider_id, coordinator_id, provider_name, coordinator_name = row
        print(f"  {patient_id}: provider_id={provider_id}, coordinator_id={coordinator_id}")
        print(f"    provider_name='{provider_name}', coordinator_name='{coordinator_name}'")
    
    # 5. Check if there are multiple assignments per patient
    print("\nChecking for multiple assignments per patient...")
    cursor.execute("""
        SELECT patient_id, COUNT(*) as assignment_count
        FROM patient_assignments 
        WHERE status = 'active'
        GROUP BY patient_id 
        HAVING COUNT(*) > 1
        LIMIT 5
    """)
    
    multiple_assignments = cursor.fetchall()
    if multiple_assignments:
        print("Patients with multiple assignments:")
        for patient_id, count in multiple_assignments:
            print(f"  {patient_id}: {count} assignments")
            
            # Show all assignments for this patient
            cursor.execute("""
                SELECT provider_id, coordinator_id, provider_name, coordinator_name
                FROM patient_assignments pa
                LEFT JOIN users u_prov ON pa.provider_id = u_prov.user_id
                LEFT JOIN users u_coord ON pa.coordinator_id = u_coord.user_id
                WHERE pa.patient_id = ? AND pa.status = 'active'
            """, (patient_id,))
            
            for pa_provider_id, pa_coordinator_id, pa_provider_name, pa_coordinator_name in cursor.fetchall():
                print(f"    Assignment: provider_id={pa_provider_id}, coordinator_id={pa_coordinator_id}")
                print(f"    Names: provider='{pa_provider_name}', coordinator='{pa_coordinator_name}'")
    else:
        print("No patients with multiple assignments found.")
    
    conn.close()

if __name__ == "__main__":
    diagnose_patient_panel_issue()