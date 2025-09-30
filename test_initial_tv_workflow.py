#!/usr/bin/env python3
"""
Test Initial TV Workflow - Proper Sequence
Tests the complete Initial TV workflow in the correct order:
1. Create onboarding record
2. Schedule Initial TV visit (assign provider, date, time)
3. Provider sees visit in their dashboard
4. Provider completes the visit
5. Mark visit as complete
"""

import sqlite3
import sys
import os
from datetime import datetime, date, time

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import database

def get_test_provider_and_coordinator():
    """Get test provider and coordinator user IDs"""
    conn = database.get_db_connection()
    try:
        # Get first two users to serve as provider and coordinator
        users = conn.execute("SELECT user_id, username, full_name FROM users LIMIT 2").fetchall()
        if len(users) < 2:
            print("❌ Need at least 2 users in database for testing")
            return None, None
        
        provider_user_id = users[0][0]
        coordinator_user_id = users[1][0]
        
        print(f"✅ Test Provider: {users[0][2]} (ID: {provider_user_id})")
        print(f"✅ Test Coordinator: {users[1][2]} (ID: {coordinator_user_id})")
        
        return provider_user_id, coordinator_user_id
    finally:
        conn.close()

def create_test_onboarding_record():
    """Create a test onboarding record"""
    print("\n=== STEP 1: Creating Test Onboarding Record ===")
    
    # Create test patient data
    patient_data = {
        'first_name': 'John',
        'last_name': 'TestPatient',
        'date_of_birth': '1980-01-01',
        'phone_primary': '555-0123',
        'email': 'john.test@example.com',
        'address': '123 Test St',
        'city': 'Test City',
        'state': 'TS',
        'zip_code': '12345',
        'hypertension': True,
        'mental_health_concerns': False,
        'dementia': False,
        'annual_well_visit': True
    }
    
    # Create onboarding workflow instance
    onboarding_id = database.create_onboarding_workflow_instance(patient_data, pot_user_id=1)
    
    if onboarding_id:
        print(f"✅ Created onboarding record with ID: {onboarding_id}")
        
        # Complete stages 1-4 to get to TV scheduling
        stages_data = [
            {'stage2_complete': True, 'eligibility_verified': True, 'eligibility_status': 'Verified'},
            {'stage3_complete': True, 'emed_chart_created': True, 'chart_id': 'TEST123'},
            {'stage4_complete': True, 'intake_call_completed': True, 'intake_notes': 'Test intake completed'}
        ]
        
        for stage_data in stages_data:
            database.update_onboarding_checkbox_data(onboarding_id, stage_data)
        
        print("✅ Completed stages 1-4 (Registration through Intake)")
        return onboarding_id
    else:
        print("❌ Failed to create onboarding record")
        return None

def schedule_initial_tv_visit(onboarding_id, provider_user_id, coordinator_user_id):
    """Schedule Initial TV visit - Step 2"""
    print("\n=== STEP 2: Scheduling Initial TV Visit ===")
    
    # Get actual usernames from database
    conn = database.get_db_connection()
    try:
        provider_info = conn.execute("SELECT username, full_name FROM users WHERE user_id = ?", (provider_user_id,)).fetchone()
        coordinator_info = conn.execute("SELECT username, full_name FROM users WHERE user_id = ?", (coordinator_user_id,)).fetchone()
    finally:
        conn.close()
    
    # Schedule TV visit using save_onboarding_tv_scheduling_progress
    form_data = {
        'tv_date': date(2025, 2, 15),
        'tv_time': time(10, 30),
        'assigned_provider': f"{provider_info[1]} ({provider_info[0]})",
        'assigned_coordinator': f"{coordinator_info[1]} ({coordinator_info[0]})"
    }
    
    try:
        database.save_onboarding_tv_scheduling_progress(onboarding_id, form_data)
        print("✅ TV visit scheduled successfully")
        
        # Also mark stage 5 as complete (TV scheduled)
        stage5_data = {
            'stage5_complete': True,
            'tv_scheduled': True,
            'patient_notified': True
        }
        database.update_onboarding_checkbox_data(onboarding_id, stage5_data)
        print("✅ Stage 5 marked complete (TV scheduled)")
        
        return True
    except Exception as e:
        print(f"❌ Failed to schedule TV visit: {e}")
        return False

def verify_provider_dashboard(provider_user_id):
    """Step 3: Verify provider can see the visit in their dashboard"""
    print("\n=== STEP 3: Verifying Provider Dashboard ===")
    
    try:
        onboarding_queue = database.get_provider_onboarding_queue(provider_user_id)
        
        if onboarding_queue:
            print(f"✅ Provider dashboard shows {len(onboarding_queue)} Initial TV visit(s)")
            
            for visit in onboarding_queue:
                print(f"   📅 Patient: {visit['first_name']} {visit['last_name']}")
                print(f"   📅 TV Date: {visit['tv_date']}")
                print(f"   📅 TV Time: {visit['tv_time']}")
                print(f"   📅 Initial TV Completed: {visit['initial_tv_completed']}")
                
            return onboarding_queue[0]  # Return first visit for next step
        else:
            print("❌ No Initial TV visits found in provider dashboard")
            return None
            
    except Exception as e:
        print(f"❌ Error checking provider dashboard: {e}")
        return None

def complete_initial_tv_visit(onboarding_id):
    """Step 4: Provider completes the Initial TV visit"""
    print("\n=== STEP 4: Provider Completes Initial TV Visit ===")
    
    completion_data = {
        'initial_tv_completed': True,
        'initial_tv_completed_date': datetime.now().strftime('%Y-%m-%d'),
        'initial_tv_notes': 'Initial TV visit completed successfully. Patient assessment complete.',
        'initial_tv_provider': 'Test Provider'
    }
    
    try:
        database.update_onboarding_checkbox_data(onboarding_id, completion_data)
        print("✅ Initial TV visit marked as completed")
        return True
    except Exception as e:
        print(f"❌ Failed to complete Initial TV visit: {e}")
        return False

def verify_completion_and_dashboard_update(provider_user_id, onboarding_id):
    """Step 5: Verify visit is completed and no longer appears in provider dashboard"""
    print("\n=== STEP 5: Verifying Completion and Dashboard Update ===")
    
    try:
        # Check that visit no longer appears in provider dashboard
        onboarding_queue = database.get_provider_onboarding_queue(provider_user_id)
        
        # Should not contain our completed visit
        our_visit = [v for v in onboarding_queue if v['onboarding_id'] == onboarding_id]
        
        if not our_visit:
            print("✅ Completed visit no longer appears in provider dashboard")
        else:
            print("❌ Completed visit still appears in provider dashboard")
            return False
        
        # Verify completion in database
        conn = database.get_db_connection()
        try:
            result = conn.execute("""
                SELECT initial_tv_completed, initial_tv_completed_date, initial_tv_notes
                FROM onboarding_patients 
                WHERE onboarding_id = ?
            """, (onboarding_id,)).fetchone()
            
            if result and result[0]:
                print("✅ Visit completion recorded in database")
                print(f"   📅 Completed Date: {result[1]}")
                print(f"   📝 Notes: {result[2]}")
                return True
            else:
                print("❌ Visit completion not recorded in database")
                return False
                
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Error verifying completion: {e}")
        return False

def cleanup_test_data(onboarding_id):
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    
    conn = database.get_db_connection()
    try:
        conn.execute("DELETE FROM onboarding_patients WHERE onboarding_id = ?", (onboarding_id,))
        conn.commit()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
    finally:
        conn.close()

def main():
    """Run the complete Initial TV workflow test"""
    print("🧪 Testing Initial TV Workflow - Proper Sequence")
    print("=" * 60)
    
    # Get test users
    provider_user_id, coordinator_user_id = get_test_provider_and_coordinator()
    if not provider_user_id or not coordinator_user_id:
        return
    
    # Step 1: Create onboarding record
    onboarding_id = create_test_onboarding_record()
    if not onboarding_id:
        return
    
    try:
        # Step 2: Schedule Initial TV visit
        if not schedule_initial_tv_visit(onboarding_id, provider_user_id, coordinator_user_id):
            return
        
        # Step 3: Verify provider dashboard shows the visit
        visit_info = verify_provider_dashboard(provider_user_id)
        if not visit_info:
            return
        
        # Step 4: Provider completes the visit
        if not complete_initial_tv_visit(onboarding_id):
            return
        
        # Step 5: Verify completion and dashboard update
        if verify_completion_and_dashboard_update(provider_user_id, onboarding_id):
            print("\n🎉 WORKFLOW TEST PASSED!")
            print("✅ All steps completed successfully")
        else:
            print("\n❌ WORKFLOW TEST FAILED!")
            print("❌ Completion verification failed")
    
    finally:
        # Clean up
        cleanup_test_data(onboarding_id)

if __name__ == "__main__":
    main()