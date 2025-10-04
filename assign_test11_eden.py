#!/usr/bin/env python3

import sqlite3
import sys
import os

# Add the src directory to the path so we can import database
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import database

def find_eden_user():
    """Find Eden's user information"""
    conn = database.get_db_connection()
    try:
        # Search for users with 'eden' in their name or username
        cursor = conn.execute("""
            SELECT user_id, username, full_name, role 
            FROM users 
            WHERE LOWER(full_name) LIKE '%eden%' OR LOWER(username) LIKE '%eden%'
        """)
        users = cursor.fetchall()
        
        print("Users matching 'Eden':")
        for user in users:
            print(f"  User ID: {user[0]}, Username: {user[1]}, Full Name: {user[2]}, Role: {user[3]}")
        
        return users
    finally:
        conn.close()

def get_test11_info():
    """Get Test11's current information"""
    conn = database.get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT onboarding_id, patient_id, first_name, last_name, 
                   assigned_provider_user_id, assigned_coordinator_user_id,
                   stage1_complete, stage2_complete, stage3_complete, 
                   stage4_complete, stage5_complete, facility_assignment
            FROM onboarding_patients 
            WHERE first_name = 'Test11' AND last_name = 'Test11'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"\nTest11 Test11 Current Info:")
            print(f"  Onboarding ID: {result[0]}")
            print(f"  Patient ID: {result[1]}")
            print(f"  Name: {result[2]} {result[3]}")
            print(f"  Assigned Provider User ID: {result[4]}")
            print(f"  Assigned Coordinator User ID: {result[5]}")
            print(f"  Stages Complete: 1:{result[6]}, 2:{result[7]}, 3:{result[8]}, 4:{result[9]}, 5:{result[10]}")
            print(f"  Facility Assignment: {result[11]}")
            return result
        else:
            print("Test11 Test11 not found!")
            return None
    finally:
        conn.close()

def assign_eden_to_test11(eden_user_id, test11_onboarding_id):
    """Assign Eden as regional provider to Test11"""
    conn = database.get_db_connection()
    try:
        # Update the onboarding_patients table
        conn.execute("""
            UPDATE onboarding_patients 
            SET assigned_provider_user_id = ?, 
                updated_date = CURRENT_TIMESTAMP
            WHERE onboarding_id = ?
        """, (eden_user_id, test11_onboarding_id))
        
        # Also update patient_assignments if it exists
        patient_cursor = conn.execute("""
            SELECT patient_id FROM onboarding_patients WHERE onboarding_id = ?
        """, (test11_onboarding_id,))
        patient_result = patient_cursor.fetchone()
        
        if patient_result:
            patient_id = patient_result[0]
            
            # Check if assignment exists
            existing = conn.execute("""
                SELECT assignment_id FROM patient_assignments 
                WHERE patient_id = ? AND assignment_type = 'onboarding' AND status = 'active'
            """, (patient_id,)).fetchone()
            
            if existing:
                # Update existing assignment
                conn.execute("""
                    UPDATE patient_assignments 
                    SET provider_id = ?, 
                        notes = 'Updated - assigned Eden as regional provider', 
                        updated_date = datetime('now')
                    WHERE assignment_id = ?
                """, (eden_user_id, existing[0]))
                print(f"Updated existing patient assignment {existing[0]}")
            else:
                # Create new assignment
                conn.execute("""
                    INSERT INTO patient_assignments (
                        patient_id, provider_id, assignment_date, 
                        assignment_type, status, priority_level, notes, 
                        created_date, updated_date
                    ) VALUES (?, ?, datetime('now'), 'onboarding', 'active', 'medium', 
                             'Assigned Eden as regional provider', 
                             datetime('now'), datetime('now'))
                """, (patient_id, eden_user_id))
                print(f"Created new patient assignment for patient {patient_id}")
        
        conn.commit()
        print(f"Successfully assigned Eden (User ID: {eden_user_id}) to Test11 Test11")
        return True
        
    except Exception as e:
        print(f"Error assigning Eden to Test11: {e}")
        return False
    finally:
        conn.close()

def main():
    print("=== Assigning Test11 Test11 to Eden ===\n")
    
    # Find Eden
    eden_users = find_eden_user()
    if not eden_users:
        print("No users found matching 'Eden'")
        return
    
    # Get Test11 info
    test11_info = get_test11_info()
    if not test11_info:
        return
    
    # Use the first Eden user found (assuming there's only one)
    eden_user_id = eden_users[0][0]
    eden_name = eden_users[0][2]
    test11_onboarding_id = test11_info[0]
    
    print(f"\nAssigning {eden_name} (ID: {eden_user_id}) to Test11 Test11 (Onboarding ID: {test11_onboarding_id})")
    
    # Perform the assignment
    success = assign_eden_to_test11(eden_user_id, test11_onboarding_id)
    
    if success:
        print("\n=== Updated Test11 Info ===")
        get_test11_info()

if __name__ == "__main__":
    main()