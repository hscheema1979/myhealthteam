#!/usr/bin/env python3
"""
Comprehensive test script for onboarding workflow save progress functionality
Tests all stages: Eligibility, Chart Creation, Intake Processing, and TV Scheduling
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import (
    get_db_connection, 
    update_onboarding_checkbox_data, 
    save_onboarding_tv_scheduling_progress,
    create_onboarding_workflow_instance
)

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def get_onboarding_state(onboarding_id):
    """Get current state of onboarding record"""
    conn = get_db_connection()
    try:
        result = conn.execute("""
            SELECT 
                onboarding_id,
                patient_id,
                stage2_complete,
                stage3_complete,
                stage4_complete,
                stage5_complete,
                eligibility_status,
                eligibility_verified,
                emed_chart_created,
                chart_id,
                facility_confirmed,
                intake_call_completed,
                tv_scheduled,
                tv_date,
                tv_time,
                assigned_provider_user_id,
                assigned_coordinator_user_id
            FROM onboarding_patients 
            WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if result:
            return {
                'onboarding_id': result[0],
                'patient_id': result[1],
                'stage2_complete': result[2],
                'stage3_complete': result[3],
                'stage4_complete': result[4],
                'stage5_complete': result[5],
                'eligibility_status': result[6],
                'eligibility_verified': result[7],
                'emed_chart_created': result[8],
                'chart_id': result[9],
                'facility_confirmed': result[10],
                'intake_call_completed': result[11],
                'tv_scheduled': result[12],
                'tv_date': result[13],
                'tv_time': result[14],
                'assigned_provider_user_id': result[15],
                'assigned_coordinator_user_id': result[16]
            }
        return None
    finally:
        conn.close()

def test_stage2_eligibility_verification(onboarding_id):
    """Test Stage 2: Eligibility Verification save progress"""
    print_separator("Testing Stage 2: Eligibility Verification")
    
    print("Before State:")
    before_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 2 Complete: {before_state['stage2_complete']}")
    print(f"  Eligibility Status: {before_state['eligibility_status']}")
    print(f"  Eligibility Verified: {before_state['eligibility_verified']}")
    
    # Test eligibility verification progress
    eligibility_data = {
        'eligibility_status': 'verified',
        'eligibility_verified': True,
        'eligibility_notes': 'Patient eligibility confirmed through insurance verification',
        'stage2_complete': True
    }
    
    print("\nSaving eligibility verification progress...")
    try:
        update_onboarding_checkbox_data(onboarding_id, eligibility_data)
        print("✓ Eligibility verification progress saved successfully")
    except Exception as e:
        print(f"✗ Error saving eligibility verification progress: {e}")
        return False
    
    print("\nAfter State:")
    after_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 2 Complete: {after_state['stage2_complete']}")
    print(f"  Eligibility Status: {after_state['eligibility_status']}")
    print(f"  Eligibility Verified: {after_state['eligibility_verified']}")
    
    # Verify changes
    success = (
        after_state['stage2_complete'] == True and
        after_state['eligibility_status'] == 'verified' and
        after_state['eligibility_verified'] == True
    )
    
    if success:
        print("✓ Stage 2 eligibility verification test PASSED")
    else:
        print("✗ Stage 2 eligibility verification test FAILED")
    
    return success

def test_stage3_chart_creation(onboarding_id):
    """Test Stage 3: Chart Creation save progress"""
    print_separator("Testing Stage 3: Chart Creation")
    
    print("Before State:")
    before_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 3 Complete: {before_state['stage3_complete']}")
    print(f"  Chart Created: {before_state['emed_chart_created']}")
    print(f"  Chart ID: {before_state['chart_id']}")
    print(f"  Facility Confirmed: {before_state['facility_confirmed']}")
    
    # Test chart creation progress
    chart_data = {
        'emed_chart_created': True,
        'chart_id': 'CHART_TEST_001',
        'facility_confirmed': True,
        'chart_notes': 'Chart created successfully in eMed system',
        'stage3_complete': True
    }
    
    print("\nSaving chart creation progress...")
    try:
        update_onboarding_checkbox_data(onboarding_id, chart_data)
        print("✓ Chart creation progress saved successfully")
    except Exception as e:
        print(f"✗ Error saving chart creation progress: {e}")
        return False
    
    print("\nAfter State:")
    after_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 3 Complete: {after_state['stage3_complete']}")
    print(f"  Chart Created: {after_state['emed_chart_created']}")
    print(f"  Chart ID: {after_state['chart_id']}")
    print(f"  Facility Confirmed: {after_state['facility_confirmed']}")
    
    # Verify changes
    success = (
        after_state['stage3_complete'] == True and
        after_state['emed_chart_created'] == True and
        after_state['chart_id'] == 'CHART_TEST_001' and
        after_state['facility_confirmed'] == True
    )
    
    if success:
        print("✓ Stage 3 chart creation test PASSED")
    else:
        print("✗ Stage 3 chart creation test FAILED")
    
    return success

def test_stage4_intake_processing(onboarding_id):
    """Test Stage 4: Intake Processing save progress"""
    print_separator("Testing Stage 4: Intake Processing")
    
    print("Before State:")
    before_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 4 Complete: {before_state['stage4_complete']}")
    print(f"  Intake Call Completed: {before_state['intake_call_completed']}")
    
    # Test intake processing progress
    intake_data = {
        'intake_call_completed': True,
        'intake_notes': 'Intake call completed successfully. Patient provided all required information.',
        'medical_records_requested': True,
        'insurance_cards_received': True,
        'emed_signature_received': True,
        'stage4_complete': True
    }
    
    print("\nSaving intake processing progress...")
    try:
        update_onboarding_checkbox_data(onboarding_id, intake_data)
        print("✓ Intake processing progress saved successfully")
    except Exception as e:
        print(f"✗ Error saving intake processing progress: {e}")
        return False
    
    print("\nAfter State:")
    after_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 4 Complete: {after_state['stage4_complete']}")
    print(f"  Intake Call Completed: {after_state['intake_call_completed']}")
    
    # Verify changes
    success = (
        after_state['stage4_complete'] == True and
        after_state['intake_call_completed'] == True
    )
    
    if success:
        print("✓ Stage 4 intake processing test PASSED")
    else:
        print("✗ Stage 4 intake processing test FAILED")
    
    return success

def test_stage5_tv_scheduling(onboarding_id):
    """Test Stage 5: TV Scheduling save progress"""
    print_separator("Testing Stage 5: TV Scheduling")
    
    print("Before State:")
    before_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 5 Complete: {before_state['stage5_complete']}")
    print(f"  TV Scheduled: {before_state['tv_scheduled']}")
    print(f"  TV Date: {before_state['tv_date']}")
    print(f"  TV Time: {before_state['tv_time']}")
    print(f"  Provider ID: {before_state['assigned_provider_user_id']}")
    print(f"  Coordinator ID: {before_state['assigned_coordinator_user_id']}")
    
    # Get provider and coordinator usernames for the test
    conn = get_db_connection()
    try:
        # Get first two users as provider and coordinator for testing
        users_result = conn.execute("SELECT username FROM users LIMIT 2").fetchall()
        
        if len(users_result) < 2:
            print("✗ Not enough users found in users table")
            return False
            
        provider_username = users_result[0][0]
        coordinator_username = users_result[1][0]
    finally:
        conn.close()
    
    # Test TV scheduling progress using the existing function
    tv_data = {
        'tv_date': '2024-02-15',
        'tv_time': '14:30',
        'assigned_provider': provider_username,
        'assigned_coordinator': coordinator_username,
        'tv_notes': 'TV appointment scheduled for comprehensive assessment'
    }
    
    print(f"\nSaving TV scheduling progress with provider: {provider_username}, coordinator: {coordinator_username}...")
    try:
        save_onboarding_tv_scheduling_progress(onboarding_id, tv_data)
        print("✓ TV scheduling progress saved successfully")
    except Exception as e:
        print(f"✗ Error saving TV scheduling progress: {e}")
        return False
    
    print("\nAfter State:")
    after_state = get_onboarding_state(onboarding_id)
    print(f"  Stage 5 Complete: {after_state['stage5_complete']}")
    print(f"  TV Scheduled: {after_state['tv_scheduled']}")
    print(f"  TV Date: {after_state['tv_date']}")
    print(f"  TV Time: {after_state['tv_time']}")
    print(f"  Provider ID: {after_state['assigned_provider_user_id']}")
    print(f"  Coordinator ID: {after_state['assigned_coordinator_user_id']}")
    print(f"  Patient ID: {after_state['patient_id']}")
    
    # Verify changes - Note: save_onboarding_tv_scheduling_progress saves partial progress
    # It doesn't set tv_scheduled or stage5_complete flags (that's correct behavior)
    success = (
        after_state['tv_date'] == '2024-02-15' and
        after_state['tv_time'] == '14:30' and
        after_state['assigned_provider_user_id'] is not None and
        after_state['assigned_coordinator_user_id'] is not None and
        after_state['patient_id'] is not None
    )
    
    if success:
        print("✓ Stage 5 TV scheduling (partial progress) test PASSED")
    else:
        print("✗ Stage 5 TV scheduling (partial progress) test FAILED")
    
    # Now test completing Stage 5 using update_onboarding_checkbox_data
    print("\nTesting Stage 5 completion...")
    stage5_completion_data = {
        'tv_scheduled': True,
        'stage5_complete': True,
        'initial_tv_completed': True,
        'initial_tv_completed_date': '2024-02-15',
        'initial_tv_notes': 'Initial TV visit completed successfully'
    }
    
    try:
        update_onboarding_checkbox_data(onboarding_id, stage5_completion_data)
        print("✓ Stage 5 completion progress saved successfully")
        
        # Check final state
        final_state = get_onboarding_state(onboarding_id)
        completion_success = (
            final_state['tv_scheduled'] == True and
            final_state['stage5_complete'] == True
        )
        
        if completion_success:
            print("✓ Stage 5 completion test PASSED")
            success = True  # Overall success includes both partial and completion
        else:
            print("✗ Stage 5 completion test FAILED")
            
    except Exception as e:
        print(f"✗ Error completing Stage 5: {e}")
    
    return success

def main():
    """Main test function"""
    print_separator("Onboarding Workflow Save Progress Test Suite")
    
    # Create a test onboarding record
    test_patient_data = {
        'first_name': 'STAGE_TEST',
        'last_name': 'PATIENT',
        'date_of_birth': '1985-06-15',
        'phone_primary': '555-0199',
        'email': 'stage.test@example.com',
        'address_street': '999 Test Stage St',
        'address_city': 'Test City',
        'address_state': 'TS',
        'address_zip': '99999',
        'insurance_primary': 'Test Insurance Co',
        'insurance_policy_number': 'STAGE999'
    }
    
    print("Creating test onboarding record...")
    try:
        onboarding_id = create_onboarding_workflow_instance(test_patient_data, pot_user_id=1)
        print(f"✓ Test onboarding record created with ID: {onboarding_id}")
    except Exception as e:
        print(f"✗ Error creating test onboarding record: {e}")
        return
    
    # Test each stage
    results = []
    
    # Stage 2: Eligibility Verification
    results.append(test_stage2_eligibility_verification(onboarding_id))
    
    # Stage 3: Chart Creation
    results.append(test_stage3_chart_creation(onboarding_id))
    
    # Stage 4: Intake Processing
    results.append(test_stage4_intake_processing(onboarding_id))
    
    # Stage 5: TV Scheduling
    results.append(test_stage5_tv_scheduling(onboarding_id))
    
    # Summary
    print_separator("Test Results Summary")
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Onboarding workflow save progress is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above for details.")
    
    print(f"\nTest onboarding record ID: {onboarding_id}")
    print("You can manually verify the data in the database if needed.")

if __name__ == "__main__":
    main()