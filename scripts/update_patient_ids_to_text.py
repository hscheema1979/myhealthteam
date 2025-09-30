#!/usr/bin/env python3
"""
Script to update existing patient records from integer patient_ids to proper text-based format.
This script will:
1. Find all patients with integer patient_ids
2. Generate proper text-based patient_ids using the generate_patient_id function
3. Update the patients table with the new patient_ids
4. Update related tables (onboarding_patients, patient_panel, patient_assignments) with the new patient_ids
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_db_connection, generate_patient_id

def update_patient_ids_to_text():
    """Update all integer patient_ids to proper text-based format"""
    conn = get_db_connection()
    try:
        # Get all patients with integer patient_ids
        patients_to_update = conn.execute("""
            SELECT rowid, patient_id, first_name, last_name, date_of_birth 
            FROM patients 
            WHERE patient_id GLOB '[0-9]*'
        """).fetchall()
        
        print(f"Found {len(patients_to_update)} patients with integer patient_ids to update")
        
        for patient in patients_to_update:
            rowid, old_patient_id, first_name, last_name, date_of_birth = patient
            
            # Generate new text-based patient_id
            new_patient_id = generate_patient_id(first_name or '', last_name or '', date_of_birth or '')
            
            print(f"Updating patient: {first_name} {last_name} ({date_of_birth})")
            print(f"  Old patient_id: {old_patient_id}")
            print(f"  New patient_id: {new_patient_id}")
            
            # Check if the new patient_id already exists
            existing = conn.execute("SELECT patient_id FROM patients WHERE patient_id = ?", (new_patient_id,)).fetchone()
            if existing:
                print(f"  WARNING: New patient_id {new_patient_id} already exists! Skipping...")
                continue
            
            # Update patients table
            conn.execute("UPDATE patients SET patient_id = ? WHERE rowid = ?", (new_patient_id, rowid))
            
            # Update onboarding_patients table
            conn.execute("UPDATE onboarding_patients SET patient_id = ? WHERE patient_id = ?", (new_patient_id, old_patient_id))
            
            # Update patient_panel table
            conn.execute("UPDATE patient_panel SET patient_id = ? WHERE patient_id = ?", (new_patient_id, old_patient_id))
            
            # Update patient_assignments table
            conn.execute("UPDATE patient_assignments SET patient_id = ? WHERE patient_id = ?", (new_patient_id, old_patient_id))
            
            # Update any other tables that might reference patient_id
            # Check for patient_visits table
            try:
                conn.execute("UPDATE patient_visits SET patient_id = ? WHERE patient_id = ?", (new_patient_id, old_patient_id))
            except Exception as e:
                print(f"  Note: Could not update patient_visits table: {e}")
            
            print(f"  ✓ Successfully updated to: {new_patient_id}")
        
        conn.commit()
        print(f"\nSuccessfully updated {len(patients_to_update)} patient records")
        
        # Verify the updates
        remaining_integer_ids = conn.execute("SELECT COUNT(*) FROM patients WHERE patient_id GLOB '[0-9]*'").fetchone()[0]
        print(f"Remaining integer patient_ids: {remaining_integer_ids}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating patient IDs: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_patient_ids_to_text()