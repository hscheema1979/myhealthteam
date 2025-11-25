#!/usr/bin/env python3
"""
Find the test data containing "TEST_FRESH" and "Cedar"
"""
import sqlite3

def find_test_data():
    conn = sqlite3.connect('production.db')
    try:
        cursor = conn.cursor()
        
        # Look for the specific test entry mentioned
        print("=== SEARCHING FOR TEST_FRESH ENTRY ===")
        cursor.execute("""
            SELECT patient_id, first_name, last_name, facility, current_facility_id, status
            FROM patients
            WHERE patient_id LIKE '%TEST_FRESH%' 
            OR first_name LIKE '%TEST%' 
            OR last_name LIKE '%TEST%'
            OR facility LIKE '%TEST%'
        """)
        
        test_patients = cursor.fetchall()
        
        if test_patients:
            print(f"Found {len(test_patients)} test patients:")
            for pid, fname, lname, facility, current_fid, status in test_patients:
                print(f"  ID: {pid}")
                print(f"  Name: {fname} {lname}")
                print(f"  Facility: {facility}, current_facility_id: {current_fid}")
                print(f"  Status: {status}")
                print()
        else:
            print("No test patients found with simple patterns")
        
        # Search for any patient with facility or name containing "Cedar"
        print("=== SEARCHING FOR CEDAR REFERENCES ===")
        cursor.execute("""
            SELECT patient_id, first_name, last_name, facility, current_facility_id, status
            FROM patients
            WHERE patient_id LIKE '%Cedar%'
            OR first_name LIKE '%Cedar%'
            OR last_name LIKE '%Cedar%'
            OR facility LIKE '%Cedar%'
        """)
        
        cedar_patients = cursor.fetchall()
        
        if cedar_patients:
            print(f"Found {len(cedar_patients)} patients with Cedar references:")
            for pid, fname, lname, facility, current_fid, status in cedar_patients:
                print(f"  ID: {pid}")
                print(f"  Name: {fname} {lname}")
                print(f"  Facility: {facility}, current_facility_id: {current_fid}")
                print(f"  Status: {status}")
                print()
        else:
            print("No patients found with Cedar references")
        
        # Let's also check if there are any recently created test records
        print("=== CHECKING FOR RECENT TEST DATA ===")
        cursor.execute("""
            SELECT patient_id, first_name, last_name, status, created_date
            FROM patients
            WHERE created_date IS NOT NULL 
            AND (patient_id LIKE '%TEST%' OR patient_id LIKE '%test%')
            ORDER BY created_date DESC
            LIMIT 10
        """)
        
        recent_test = cursor.fetchall()
        if recent_test:
            print("Recent test data:")
            for pid, fname, lname, status, created in recent_test:
                print(f"  {pid} - {fname} {lname} - Status: {status} - Created: {created}")
        else:
            print("No recent test data found")
        
        # Check for any facility IDs that don't match our main facilities
        print("\n=== CHECKING FOR ORPHAN FACILITY IDs ===")
        cursor.execute("""
            SELECT DISTINCT current_facility_id, facility
            FROM patients
            WHERE current_facility_id IS NOT NULL
            AND current_facility_id NOT IN (SELECT facility_id FROM facilities)
        """)
        
        orphan_facilities = cursor.fetchall()
        if orphan_facilities:
            print("Found orphan facility IDs (not in facilities table):")
            for fid, facility in orphan_facilities:
                print(f"  ID: {fid}, Facility text: '{facility}'")
        else:
            print("No orphan facility IDs found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    find_test_data()