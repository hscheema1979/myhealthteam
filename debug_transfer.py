#!/usr/bin/env python3
"""
Debug script to check assignment creation in transfer function.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection

def debug_transfer():
    """Debug the transfer function assignment creation"""
    
    conn = get_db_connection()
    try:
        # Check if there are any test assignments
        assignments = conn.execute("""
            SELECT * FROM patient_assignments 
            WHERE patient_id LIKE '%PATIENT%' OR patient_id LIKE '%TESTTRANSFER%'
        """).fetchall()
        
        print(f"Found {len(assignments)} test assignments:")
        for assignment in assignments:
            print(f"  - {dict(assignment)}")
        
        # Check if there are any test patients
        patients = conn.execute("""
            SELECT * FROM patients 
            WHERE patient_id LIKE '%PATIENT%' OR patient_id LIKE '%TESTTRANSFER%'
        """).fetchall()
        
        print(f"\nFound {len(patients)} test patients:")
        for patient in patients:
            print(f"  - {dict(patient)}")
        
        # Check if there are any test onboarding records
        onboarding = conn.execute("""
            SELECT * FROM onboarding_patients 
            WHERE first_name = 'TestTransfer' OR last_name = 'Patient'
        """).fetchall()
        
        print(f"\nFound {len(onboarding)} test onboarding records:")
        for record in onboarding:
            print(f"  - ID: {record['onboarding_id']}, Name: {record['first_name']} {record['last_name']}")
            print(f"    Provider: {record['assigned_provider_user_id']}, Coordinator: {record['assigned_coordinator_user_id']}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    debug_transfer()