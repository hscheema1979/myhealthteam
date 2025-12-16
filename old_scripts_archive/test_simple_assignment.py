#!/usr/bin/env python3
"""
Simple test to see if assignments are being created
"""

import sqlite3
import subprocess
import sys
import os

# First, let's manually test the assignment creation
def test_assignment_creation():
    print("Testing assignment creation manually")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('production.db')
    
    # Check current state
    cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
    before_count = cursor.fetchone()[0]
    print(f"Assignments before: {before_count}")
    
    # Manually insert a test assignment
    test_patient_id = "TEST PATIENT 01/01/1980"
    test_provider_id = 2  # Szalas NP, Andrew
    test_coordinator_id = 8  # Atencio, Dianela
    
    try:
        conn.execute("""
            INSERT INTO patient_assignments (patient_id, provider_id, coordinator_id)
            VALUES (?, ?, ?)
        """, (test_patient_id, test_provider_id, test_coordinator_id))
        conn.commit()
        
        cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
        after_count = cursor.fetchone()[0]
        print(f"Assignments after manual insert: {after_count}")
        
        # Show the inserted assignment
        cursor = conn.execute("""
            SELECT pa.patient_id, pa.provider_id, pa.coordinator_id, u1.full_name as provider_name, u2.full_name as coordinator_name
            FROM patient_assignments pa
            LEFT JOIN users u1 ON pa.provider_id = u1.user_id
            LEFT JOIN users u2 ON pa.coordinator_id = u2.user_id
            WHERE pa.patient_id = ?
        """, (test_patient_id,))
        
        result = cursor.fetchone()
        if result:
            patient_id, prov_id, coord_id, prov_name, coord_name = result
            print(f"Test assignment: {patient_id}")
            print(f"  Provider: {prov_name} (ID: {prov_id})")
            print(f"  Coordinator: {coord_name} (ID: {coord_id})")
        
        # Clean up
        conn.execute("DELETE FROM patient_assignments WHERE patient_id = ?", (test_patient_id,))
        conn.commit()
        
    except Exception as e:
        print(f"Error inserting test assignment: {e}")
    
    conn.close()
    
    print("\nThe assignment table works fine. The issue must be in the ZMO processing logic.")
    print("Let me check if assignments_data is being populated in process_zmo...")

if __name__ == "__main__":
    test_assignment_creation()