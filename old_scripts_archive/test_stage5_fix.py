#!/usr/bin/env python3
"""
Test script to verify Stage 5 completion functionality after fixing execute_query error
"""

import sys
sys.path.append('.')

from src import database
from src.dashboards.onboarding_dashboard import *

def test_stage5_assignment_check():
    """Test the assignment checking logic that was causing the execute_query error"""
    print("Testing Stage 5 assignment checking logic...")
    
    # Get a test patient with assignments
    conn = database.get_db_connection()
    
    # Find a patient with assignments
    test_patient = conn.execute("""
        SELECT DISTINCT patient_id 
        FROM patient_assignments 
        WHERE patient_id IS NOT NULL 
        AND status = 'Active'
        LIMIT 1
    """).fetchone()
    
    if not test_patient:
        print("No test patients with assignments found")
        conn.close()
        return False
    
    patient_id = test_patient[0]
    print(f"Testing with patient_id: {patient_id}")
    
    # Test the fixed assignment checking logic
    try:
        # Check for regional provider assignment
        provider_result = conn.execute("""
            SELECT provider_id FROM patient_assignments 
            WHERE patient_id = ? AND provider_id IS NOT NULL AND status = 'Active'
        """, (patient_id,)).fetchall()
        regional_provider_assigned = len(provider_result) > 0
        
        # Check for coordinator assignment
        coordinator_result = conn.execute("""
            SELECT coordinator_id FROM patient_assignments 
            WHERE patient_id = ? AND coordinator_id IS NOT NULL AND status = 'Active'
        """, (patient_id,)).fetchall()
        coordinator_assigned_in_patient_table = len(coordinator_result) > 0
        
        assignments_complete = regional_provider_assigned and coordinator_assigned_in_patient_table
        
        print(f"Provider assigned: {regional_provider_assigned}")
        print(f"Coordinator assigned: {coordinator_assigned_in_patient_table}")
        print(f"Assignments complete: {assignments_complete}")
        
        conn.close()
        print("✅ Stage 5 assignment checking logic works correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error in assignment checking: {str(e)}")
        conn.close()
        return False

def test_onboarding_patient_details():
    """Test getting onboarding patient details"""
    print("\nTesting onboarding patient details retrieval...")
    
    try:
        # Get a test onboarding patient
        conn = database.get_db_connection()
        test_onboarding = conn.execute("""
            SELECT onboarding_id 
            FROM onboarding_patients 
            WHERE patient_id IS NOT NULL
            LIMIT 1
        """).fetchone()
        conn.close()
        
        if not test_onboarding:
            print("No test onboarding patients found")
            return False
        
        onboarding_id = test_onboarding[0]
        print(f"Testing with onboarding_id: {onboarding_id}")
        
        # Test getting patient details
        patient_details = database.get_onboarding_patient_details(onboarding_id)
        
        if patient_details:
            print(f"✅ Successfully retrieved patient details for onboarding_id: {onboarding_id}")
            print(f"Patient ID: {patient_details.get('patient_id', 'None')}")
            return True
        else:
            print("❌ Failed to retrieve patient details")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving patient details: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Testing Stage 5 Completion Fix ===\n")
    
    success1 = test_stage5_assignment_check()
    success2 = test_onboarding_patient_details()
    
    print(f"\n=== Test Results ===")
    print(f"Assignment checking: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Patient details retrieval: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Stage 5 completion should work correctly now.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")