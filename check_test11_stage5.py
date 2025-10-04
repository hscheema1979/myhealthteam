#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import get_db_connection

def check_test11_stage5():
    conn = get_db_connection()
    
    print("=== Test11 Stage 5 Completion Check ===")
    
    # Get Test11 onboarding data
    cursor = conn.execute("""
        SELECT onboarding_id, first_name || ' ' || last_name as patient_name, 
               stage1_complete, stage2_complete, stage3_complete, stage4_complete, stage5_complete,
               assigned_provider_user_id, assigned_coordinator_user_id,
               tv_date, tv_time, initial_tv_provider,
               created_date, updated_date
        FROM onboarding_patients 
        WHERE first_name || ' ' || last_name = 'Test11 Test11'
    """)
    
    test11_data = cursor.fetchone()
    if test11_data:
        print(f"Onboarding ID: {test11_data[0]}")
        print(f"Patient Name: {test11_data[1]}")
        print(f"Stage 1 Complete: {test11_data[2]}")
        print(f"Stage 2 Complete: {test11_data[3]}")
        print(f"Stage 3 Complete: {test11_data[4]}")
        print(f"Stage 4 Complete: {test11_data[5]}")
        print(f"Stage 5 Complete: {test11_data[6]}")
        print(f"Assigned Provider User ID: {test11_data[7]}")
        print(f"Assigned Coordinator User ID: {test11_data[8]}")
        print(f"TV Date: {test11_data[9]}")
        print(f"TV Time: {test11_data[10]}")
        print(f"Initial TV Provider: {test11_data[11]}")
        print(f"Created Date: {test11_data[12]}")
        print(f"Updated Date: {test11_data[13]}")
        
        onboarding_id = test11_data[0]
        
        # Check patient assignments for this onboarding
        print("\n=== Patient Assignments ===")
        assignments_cursor = conn.execute("""
            SELECT pa.assignment_id, pa.patient_id, pa.provider_id, pa.coordinator_id,
                   pa.assignment_date, pa.assignment_type, pa.status, pa.notes,
                   p_prov.full_name as provider_name, p_coord.full_name as coordinator_name
            FROM patient_assignments pa
            LEFT JOIN users p_prov ON pa.provider_id = p_prov.user_id
            LEFT JOIN users p_coord ON pa.coordinator_id = p_coord.user_id
            WHERE pa.patient_id = (SELECT patient_id FROM onboarding_patients WHERE onboarding_id = ?)
            ORDER BY pa.assignment_date DESC
        """, (onboarding_id,))
        
        assignments = assignments_cursor.fetchall()
        if assignments:
            for assignment in assignments:
                print(f"Assignment ID: {assignment[0]}")
                print(f"Patient ID: {assignment[1]}")
                print(f"Provider ID: {assignment[2]} ({assignment[8]})")
                print(f"Coordinator ID: {assignment[3]} ({assignment[9]})")
                print(f"Assignment Date: {assignment[4]}")
                print(f"Type: {assignment[5]}")
                print(f"Status: {assignment[6]}")
                print(f"Notes: {assignment[7]}")
                print("---")
        else:
            print("No patient assignments found")
            
        # Check if there are any workflow stage completions
        print("\n=== Workflow Stage Completions ===")
        stages_cursor = conn.execute("""
            SELECT stage_number, completion_date, completed_by, notes
            FROM onboarding_workflow_stages 
            WHERE onboarding_id = ?
            ORDER BY stage_number
        """, (onboarding_id,))
        
        stages = stages_cursor.fetchall()
        if stages:
            for stage in stages:
                print(f"Stage {stage[0]}: Completed on {stage[1]} by {stage[2]}")
                if stage[3]:
                    print(f"  Notes: {stage[3]}")
        else:
            print("No workflow stage completions found")
    else:
        print("Test11 not found in onboarding_patients table")
    
    conn.close()

if __name__ == "__main__":
    check_test11_stage5()