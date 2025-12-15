#!/usr/bin/env python3
"""
Check the transform function output and patient assignments
"""

import sqlite3
import subprocess
import sys
import os

def check_transform_output():
    print("Checking transform function results")
    print("=" * 50)
    
    # Check database state
    conn = sqlite3.connect('production.db')
    
    # Check patient_assignments
    cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
    assignment_count = cursor.fetchone()[0]
    print(f"Patient assignments count: {assignment_count}")
    
    if assignment_count > 0:
        # Show some sample assignments
        cursor = conn.execute("""
            SELECT pa.patient_id, pa.provider_id, pa.coordinator_id, u1.full_name as provider_name, u2.full_name as coordinator_name
            FROM patient_assignments pa
            LEFT JOIN users u1 ON pa.provider_id = u1.user_id
            LEFT JOIN users u2 ON pa.coordinator_id = u2.user_id
            LIMIT 5
        """)
        print("Sample assignments:")
        for row in cursor.fetchall():
            patient_id, prov_id, coord_id, prov_name, coord_name = row
            print(f"  Patient: {patient_id}")
            print(f"    Provider: {prov_name} (ID: {prov_id})")
            print(f"    Coordinator: {coord_name} (ID: {coord_id})")
    
    # Check patients table
    cursor = conn.execute("SELECT COUNT(*) FROM patients")
    patient_count = cursor.fetchone()[0]
    print(f"\nPatients count: {patient_count}")
    
    # Check users table
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE status != 'deleted'")
    user_count = cursor.fetchone()[0]
    print(f"Active users count: {user_count}")
    
    conn.close()

if __name__ == "__main__":
    check_transform_output()