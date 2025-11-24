#!/usr/bin/env python3
"""
Debug GOC value issue - check both patients and patient_panel tables
"""

import sqlite3
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection

def debug_goc_issue():
    """Debug why GOC value shows as None in patient panel"""
    conn = get_db_connection()
    try:
        # First, check Patient Brar in patients table
        print("=== PATIENTS TABLE ===")
        cursor = conn.execute("""
            SELECT 
                patient_id,
                first_name,
                last_name,
                goc_value,
                code_status,
                goals_of_care
            FROM patients 
            WHERE last_name LIKE '%Brar%'
        """)
        
        patients_data = cursor.fetchall()
        for row in patients_data:
            print(f"Patient ID: {row[0]}")
            print(f"Name: {row[1]} {row[2]}")
            print(f"GOC Value: {row[3]}")
            print(f"Code Status: {row[4]}")
            print(f"Goals of Care: {row[5]}")
            print("-" * 40)
        
        # Check Patient Brar in patient_panel table
        print("\n=== PATIENT_PANEL TABLE ===")
        cursor = conn.execute("""
            SELECT 
                patient_id,
                first_name,
                last_name,
                goc_value,
                code_status,
                goals_of_care
            FROM patient_panel 
            WHERE last_name LIKE '%Brar%'
        """)
        
        panel_data = cursor.fetchall()
        if panel_data:
            for row in panel_data:
                print(f"Patient ID: {row[0]}")
                print(f"Name: {row[1]} {row[2]}")
                print(f"GOC Value: {row[3]}")
                print(f"Code Status: {row[4]}")
                print(f"Goals of Care: {row[5]}")
                print("-" * 40)
        else:
            print("No Patient Brar found in patient_panel table")
        
        # Check what the actual query returns for Genevieve's patients
        print("\n=== PROVIDER PANEL QUERY RESULT (Genevieve) ===")
        
        # Get Genevieve's user_id first
        cursor = conn.execute("""
            SELECT user_id, full_name 
            FROM users 
            WHERE full_name LIKE '%Genevieve%'
        """)
        
        genevieve_data = cursor.fetchone()
        if genevieve_data:
            genevieve_id = genevieve_data[0]
            print(f"Genevieve's user_id: {genevieve_id}")
            
            # Run the exact query from get_provider_patient_panel_enhanced
            cursor = conn.execute("""
                SELECT
                    p.patient_id,
                    p.first_name,
                    p.last_name,
                    p.goc_value as patients_goc,
                    pp.goc_value as panel_goc,
                    COALESCE(pp.goc_value, p.goc_value) as final_goc,
                    p.code_status as patients_code,
                    pp.code_status as panel_code,
                    COALESCE(pp.code_status, p.code_status) as final_code
                FROM patient_assignments pa
                JOIN patients p ON pa.patient_id = p.patient_id
                LEFT JOIN patient_panel pp ON p.patient_id = pp.patient_id
                WHERE pa.provider_id = ? AND p.last_name LIKE '%Brar%'
                ORDER BY p.last_name, p.first_name
            """, (genevieve_id,))
            
            query_results = cursor.fetchall()
            if query_results:
                for row in query_results:
                    print(f"Patient ID: {row[0]}")
                    print(f"Name: {row[1]} {row[2]}")
                    print(f"Patients table GOC: {row[3]}")
                    print(f"Patient_panel table GOC: {row[4]}")
                    print(f"Final GOC (COALESCE): {row[5]}")
                    print(f"Patients table Code: {row[6]}")
                    print(f"Patient_panel table Code: {row[7]}")
                    print(f"Final Code (COALESCE): {row[8]}")
                    print("-" * 40)
            else:
                print("No Patient Brar found in provider panel query")
        else:
            print("Genevieve not found in users table")
            
        # Check patient_assignments table
        print("\n=== PATIENT_ASSIGNMENTS TABLE ===")
        cursor = conn.execute("""
            SELECT 
                pa.patient_id,
                pa.provider_id,
                pa.coordinator_id,
                pa.assignment_type,
                u.full_name as provider_name
            FROM patient_assignments pa
            LEFT JOIN users u ON pa.provider_id = u.user_id
            WHERE pa.patient_id LIKE '%BRAR%'
        """)
        
        assignments = cursor.fetchall()
        if assignments:
            for row in assignments:
                print(f"Patient ID: {row[0]}")
                print(f"Provider ID: {row[1]}")
                print(f"Coordinator ID: {row[2]}")
                print(f"Assignment Type: {row[3]}")
                print(f"Provider Name: {row[4]}")
                print("-" * 40)
        else:
            print("No assignments found for Patient Brar")
                
    except Exception as e:
        print(f"Error debugging GOC issue: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_goc_issue()