#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import get_db_connection

def check_patients():
    conn = get_db_connection()
    
    print("=== Patients in Onboarding Table ===")
    
    cursor = conn.execute("""
        SELECT onboarding_id, first_name, last_name, 
               first_name || ' ' || last_name as full_name,
               assigned_provider_user_id, assigned_coordinator_user_id
        FROM onboarding_patients 
        ORDER BY onboarding_id
    """)
    
    patients = cursor.fetchall()
    for patient in patients:
        print(f"ID: {patient[0]}, First: '{patient[1]}', Last: '{patient[2]}', Full: '{patient[3]}'")
        print(f"  Provider ID: {patient[4]}, Coordinator ID: {patient[5]}")
        print("---")
    
    conn.close()

if __name__ == "__main__":
    check_patients()