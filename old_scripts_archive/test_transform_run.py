#!/usr/bin/env python3
"""
Test running the transform function to see if ZMO-only processing works
"""

import os
import sys
import subprocess
import sqlite3

def test_transform_run():
    print("Testing transform function with current ZMO-only setup")
    print("=" * 60)
    
    # Check database state before
    conn = sqlite3.connect('production.db')
    cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
    before_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM patients")
    before_patients = cursor.fetchone()[0]
    conn.close()
    
    print(f"Before transform:")
    print(f"  - Patient assignments: {before_count}")
    print(f"  - Patients: {before_patients}")
    
    # Run the transform function
    print("\nRunning transform_production_data_v3_fixed.py...")
    try:
        result = subprocess.run([
            sys.executable, 
            'transform_production_data_v3_fixed.py'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        
    except Exception as e:
        print(f"Error running transform: {e}")
        return False
    
    # Check database state after
    conn = sqlite3.connect('production.db')
    cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
    after_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM patients")
    after_patients = cursor.fetchone()[0]
    conn.close()
    
    print(f"\nAfter transform:")
    print(f"  - Patient assignments: {after_count}")
    print(f"  - Patients: {after_patients}")
    print(f"  - Assignments added: {after_count - before_count}")
    print(f"  - Patients added: {after_patients - before_patients}")
    
    # Check if assignments were created from ZMO data
    if after_count > before_count:
        print("\n✅ SUCCESS: Assignments were created from ZMO data!")
        print("This confirms the system works without separate provider CSV files.")
        return True
    else:
        print("\n⚠️  No new assignments were created.")
        return False

if __name__ == "__main__":
    test_transform_run()