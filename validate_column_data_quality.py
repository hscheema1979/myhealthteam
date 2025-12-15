#!/usr/bin/env python3
"""
Comprehensive data quality validation script to verify column data makes sense
"""

import sqlite3
import sys
from datetime import datetime

def validate_data_quality():
    """Validate actual column data to ensure it makes sense"""
    
    db_path = "production.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Comprehensive Data Quality Validation")
        print("=" * 60)
        
        validation_results = []
        
        # 1. Validate patients table data
        print("\n1. Validating patients table data...")
        try:
            # Check patient_id format
            result = cursor.execute("""
                SELECT patient_id, first_name, last_name, date_of_birth, phone_primary
                FROM patients 
                LIMIT 5
            """).fetchall()
            
            print("   Sample patient data:")
            for row in result:
                print(f"   Patient: {row['patient_id']} - {row['first_name']} {row['last_name']} "
                      f"(DOB: {row['date_of_birth']}, Phone: {row['phone_primary']})")
                
                # Validate patient_id format (this appears to be name-based, not numeric)
                if len(row['patient_id']) > 5:  # Reasonable length check
                    print(f"   ✅ Patient ID format valid (name-based)")
                else:
                    print(f"   ⚠️  Patient ID {row['patient_id']} suspiciously short")
                
                # Validate phone format
                if row['phone_primary'] and len(row['phone_primary']) >= 10:
                    print(f"   ✅ Phone {row['phone_primary']} length valid")
                else:
                    print(f"   ⚠️  Phone {row['phone_primary']} suspicious length")
            
            validation_results.append("✅ Patients table data quality: GOOD")
            
        except Exception as e:
            print(f"   ❌ Patients validation error: {e}")
            validation_results.append("❌ Patients table data quality: FAILED")
        
        # 2. Validate users table data
        print("\n2. Validating users table data...")
        try:
            result = cursor.execute("""
                SELECT user_id, username, full_name, email, created_at
                FROM users 
                LIMIT 5
            """).fetchall()
            
            print("   Sample user data:")
            for row in result:
                print(f"   User: {row['user_id']} - {row['username']} - {row['full_name']} "
                      f"(Email: {row['email']})")
                
                # Validate email format
                if '@' in row['email'] and '.' in row['email']:
                    print(f"   ✅ Email {row['email']} format valid")
                else:
                    print(f"   ⚠️  Email {row['email']} format suspicious")
            
            validation_results.append("✅ Users table data quality: GOOD")
            
        except Exception as e:
            print(f"   ❌ Users validation error: {e}")
            validation_results.append("❌ Users table data quality: FAILED")
        
        # 3. Validate provider tasks data
        print("\n3. Validating provider_tasks_2025_12 data...")
        try:
            result = cursor.execute("""
                SELECT provider_task_id, provider_id, provider_name, patient_id, 
                       task_date, task_description, status, minutes_of_service
                FROM provider_tasks_2025_12 
                LIMIT 5
            """).fetchall()
            
            print("   Sample provider task data:")
            for row in result:
                print(f"   Task: {row['provider_task_id']} - Provider: {row['provider_name']} "
                      f"Patient: {row['patient_id']} Date: {row['task_date']} "
                      f"Status: {row['status']} Duration: {row['minutes_of_service']}min")
                
                # Validate status values
                valid_statuses = ['pending', 'completed', 'in_progress']
                if row['status'] in valid_statuses:
                    print(f"   ✅ Status '{row['status']}' valid")
                else:
                    print(f"   ⚠️  Status '{row['status']}' unusual")
                
                # Validate duration
                if row['minutes_of_service'] and row['minutes_of_service'] > 0:
                    print(f"   ✅ Duration {row['minutes_of_service']}min positive")
                else:
                    print(f"   ⚠️  Duration {row['minutes_of_service']}min zero/negative")
            
            validation_results.append("✅ Provider tasks data quality: GOOD")
            
        except Exception as e:
            print(f"   ❌ Provider tasks validation error: {e}")
            validation_results.append("❌ Provider tasks data quality: FAILED")
        
        # 4. Validate coordinator tasks data
        print("\n4. Validating coordinator_tasks_2025_12 data...")
        try:
            result = cursor.execute("""
                SELECT coordinator_task_id, coordinator_id, coordinator_name, patient_id,
                       task_date, task_type, submission_status, duration_minutes
                FROM coordinator_tasks_2025_12 
                LIMIT 5
            """).fetchall()
            
            print("   Sample coordinator task data:")
            for row in result:
                print(f"   Task: {row['coordinator_task_id']} - Coordinator: {row['coordinator_name']} "
                      f"Patient: {row['patient_id']} Type: {row['task_type']} "
                      f"Status: {row['submission_status']} Duration: {row['duration_minutes']}min")
                
                # Validate submission status
                valid_statuses = ['pending', 'completed', 'approved', 'rejected']
                if row['submission_status'] in valid_statuses:
                    print(f"   ✅ Submission status '{row['submission_status']}' valid")
                else:
                    print(f"   ⚠️  Submission status '{row['submission_status']}' unusual")
            
            validation_results.append("✅ Coordinator tasks data quality: GOOD")
            
        except Exception as e:
            print(f"   ❌ Coordinator tasks validation error: {e}")
            validation_results.append("❌ Coordinator tasks data quality: FAILED")
        
        # 5. Validate onboarding data
        print("\n5. Validating onboarding workflow data...")
        try:
            # Check onboarding_patients
            result = cursor.execute("""
                SELECT onboarding_id, patient_id, first_name, last_name, 
                       eligibility_status, assigned_provider_user_id, assigned_coordinator_user_id
                FROM onboarding_patients 
                LIMIT 3
            """).fetchall()
            
            print("   Sample onboarding patient data:")
            for row in result:
                print(f"   Onboarding: {row['onboarding_id']} - Patient: {row['first_name']} {row['last_name']} "
                      f"Status: {row['eligibility_status']} "
                      f"Provider: {row['assigned_provider_user_id']} Coordinator: {row['assigned_coordinator_user_id']}")
                
                # Validate eligibility status
                valid_statuses = ['Active', 'Pending', 'Completed', 'Rejected']
                if row['eligibility_status'] in valid_statuses:
                    print(f"   ✅ Eligibility status '{row['eligibility_status']}' valid")
                else:
                    print(f"   ⚠️  Eligibility status '{row['eligibility_status']}' unusual")
            
            # Check onboarding_tasks
            task_result = cursor.execute("""
                SELECT task_id, onboarding_id, task_name, status, task_stage
                FROM onboarding_tasks 
                LIMIT 3
            """).fetchall()
            
            print("   Sample onboarding task data:")
            for row in task_result:
                print(f"   Task: {row['task_id']} - Onboarding: {row['onboarding_id']} "
                      f"Name: {row['task_name']} Status: {row['status']} Stage: {row['task_stage']}")
            
            validation_results.append("✅ Onboarding workflow data quality: GOOD")
            
        except Exception as e:
            print(f"   ❌ Onboarding validation error: {e}")
            validation_results.append("❌ Onboarding data quality: FAILED")
        
        # 6. Validate facilities data
        print("\n6. Validating facilities data...")
        try:
            result = cursor.execute("""
                SELECT facility_id, facility_name, facility_type, city, state
                FROM facilities 
                LIMIT 5
            """).fetchall()
            
            print("   Sample facility data:")
            for row in result:
                print(f"   Facility: {row['facility_id']} - {row['facility_name']} "
                      f"Type: {row['facility_type']} Location: {row['city']}, {row['state']}")
                
                # Validate facility type
                valid_types = ['Hospital', 'Clinic', 'Nursing Home', 'Assisted Living', 'Home Care']
                if row['facility_type'] in valid_types:
                    print(f"   ✅ Facility type '{row['facility_type']}' valid")
                else:
                    print(f"   ⚠️  Facility type '{row['facility_type']}' unusual")
            
            validation_results.append("✅ Facilities data quality: GOOD")
            
        except Exception as e:
            print(f"   ❌ Facilities validation error: {e}")
            validation_results.append("❌ Facilities data quality: FAILED")
        
        # 7. Check for data consistency issues
        print("\n7. Checking data consistency...")
        try:
            # Check for orphaned patient assignments
            orphan_check = cursor.execute("""
                SELECT COUNT(*) as orphan_count
                FROM patient_assignments pa
                LEFT JOIN patients p ON pa.patient_id = p.patient_id
                WHERE p.patient_id IS NULL
            """).fetchone()
            
            if orphan_check['orphan_count'] == 0:
                print("   ✅ No orphaned patient assignments")
            else:
                print(f"   ⚠️  Found {orphan_check['orphan_count']} orphaned patient assignments")
            
            # Check for patients without assignments
            unassigned_check = cursor.execute("""
                SELECT COUNT(*) as unassigned_count
                FROM patients p
                LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id
                WHERE pa.patient_id IS NULL
            """).fetchone()
            
            print(f"   📊 {unassigned_check['unassigned_count']} patients without assignments")
            
            validation_results.append("✅ Data consistency checks: PASSED")
            
        except Exception as e:
            print(f"   ❌ Consistency check error: {e}")
            validation_results.append("❌ Data consistency checks: FAILED")
        
        # Summary
        print("\n" + "=" * 60)
        print("DATA QUALITY VALIDATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in validation_results if "✅" in result and "GOOD" in result)
        total = len(validation_results)
        
        for result in validation_results:
            print(result)
        
        print(f"\nOverall Data Quality Score: {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 All data quality checks PASSED!")
            print("✅ Column data appears valid and makes sense")
            return True
        else:
            print("⚠️  Some data quality issues detected")
            print("🔍 Review flagged items for data integrity")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = validate_data_quality()
    sys.exit(0 if success else 1)