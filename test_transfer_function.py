#!/usr/bin/env python3
"""
Test script to verify that transfer_onboarding_to_patient_table function
correctly creates patient assignments with text-based patient_id.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import (
    get_db_connection, 
    transfer_onboarding_to_patient_table,
    generate_patient_id
)

def test_transfer_function():
    """Test the updated transfer_onboarding_to_patient_table function"""
    
    print("Testing transfer_onboarding_to_patient_table function...")
    
    # First, let's create a test onboarding record
    conn = get_db_connection()
    try:
        # Insert a test onboarding record
        cursor = conn.execute("""
            INSERT INTO onboarding_patients (
                first_name, last_name, date_of_birth, phone_primary, email,
                assigned_provider_user_id, assigned_coordinator_user_id,
                stage1_complete, stage2_complete, stage3_complete, 
                stage4_complete, stage5_complete
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, 1, 1, 1)
        """, (
            'TestTransfer', 'Patient', '1990-05-15', '555-0199', 'testtransfer@test.com',
            1, 1  # Albert's user_id for both provider and coordinator
        ))
        
        test_onboarding_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created test onboarding record with ID: {test_onboarding_id}")
        
        # Generate expected patient_id (first_name, last_name, date_of_birth)
        expected_patient_id = generate_patient_id('TestTransfer', 'Patient', '1990-05-15')
        print(f"Expected patient_id: {expected_patient_id}")
        
        # Call the transfer function
        returned_patient_id = transfer_onboarding_to_patient_table(test_onboarding_id)
        print(f"Returned patient_id: {returned_patient_id}")
        
        # Verify the returned patient_id is text-based
        assert returned_patient_id == expected_patient_id, f"Expected {expected_patient_id}, got {returned_patient_id}"
        print("✓ Function returns correct text-based patient_id")
        
        # Verify patient was created in patients table with correct patient_id
        patient_record = conn.execute("""
            SELECT patient_id, first_name, last_name, date_of_birth 
            FROM patients 
            WHERE patient_id = ?
        """, (expected_patient_id,)).fetchone()
        
        assert patient_record is not None, "Patient record not found in patients table"
        assert patient_record['patient_id'] == expected_patient_id, "Patient_id mismatch in patients table"
        print("✓ Patient created in patients table with correct text-based patient_id")
        
        # Debug: Check all assignments for this patient_id
        all_assignments = conn.execute("""
            SELECT patient_id, provider_id, coordinator_id, assignment_type, status
            FROM patient_assignments 
            WHERE patient_id = ?
        """, (expected_patient_id,)).fetchall()
        
        print(f"All assignments for patient_id '{expected_patient_id}': {len(all_assignments)}")
        for assignment in all_assignments:
            print(f"  - {dict(assignment)}")
        
        # Verify patient assignment was created with correct text-based patient_id
        assignment_record = conn.execute("""
            SELECT patient_id, provider_id, coordinator_id, assignment_type, status
            FROM patient_assignments 
            WHERE patient_id = ? AND assignment_type = 'onboarding'
        """, (expected_patient_id,)).fetchone()
        
        assert assignment_record is not None, f"Patient assignment not found. Expected patient_id: {expected_patient_id}"
        assert assignment_record['patient_id'] == expected_patient_id, "Patient_id mismatch in patient_assignments"
        assert assignment_record['provider_id'] == 1, "Provider_id mismatch"
        assert assignment_record['coordinator_id'] == 1, "Coordinator_id mismatch"
        assert assignment_record['assignment_type'] == 'onboarding', "Assignment_type mismatch"
        assert assignment_record['status'] == 'active', "Status mismatch"
        print("✓ Patient assignment created with correct text-based patient_id")
        
        print("\n🎉 All tests passed! The transfer function now correctly uses text-based patient_id for assignments.")
        
        # Cleanup test data
        conn.execute("DELETE FROM patient_assignments WHERE patient_id = ?", (expected_patient_id,))
        conn.execute("DELETE FROM patients WHERE patient_id = ?", (expected_patient_id,))
        conn.execute("DELETE FROM onboarding_patients WHERE onboarding_id = ?", (test_onboarding_id,))
        conn.commit()
        print("✓ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        # Cleanup on failure
        try:
            conn.execute("DELETE FROM patient_assignments WHERE patient_id LIKE '%TestTransfer%'")
            conn.execute("DELETE FROM patients WHERE patient_id LIKE '%TestTransfer%'")
            conn.execute("DELETE FROM onboarding_patients WHERE first_name = 'TestTransfer'")
            conn.commit()
        except:
            pass
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    test_transfer_function()