#!/usr/bin/env python3
"""
Test script for direct import of September 27-30, 2025 data
Creates sample CSV files and tests the import process
"""

import pandas as pd
import sqlite3
import tempfile
import os
from datetime import datetime
from direct_import_sept_2025 import DirectImportSept2025

def create_sample_coordinator_csv():
    """Create sample coordinator tasks CSV for testing"""
    data = [
        {
            'staff_code': 'CM001',
            'patient_id': 'MRN123456',
            'task_date': '2025-09-27',
            'duration_minutes': 30,
            'task_type': 'Phone Call',
            'notes': 'Follow-up call regarding medication compliance'
        },
        {
            'staff_code': 'CM002', 
            'patient_id': 'MRN789012',
            'task_date': '2025-09-28',
            'duration_minutes': 45,
            'task_type': 'Care Plan Review',
            'notes': 'Reviewed care plan with patient and family'
        },
        {
            'staff_code': 'CM001',
            'patient_id': 'MRN345678',
            'task_date': '2025-09-29',
            'duration_minutes': 25,
            'task_type': 'Documentation',
            'notes': 'Updated patient records'
        },
        {
            'staff_code': 'CM003',
            'patient_id': 'MRN901234',
            'task_date': '2025-09-30',
            'duration_minutes': 60,
            'task_type': 'Assessment',
            'notes': 'Comprehensive health assessment'
        }
    ]
    
    df = pd.DataFrame(data)
    csv_path = 'test_coordinator_tasks_sept_27_30.csv'
    df.to_csv(csv_path, index=False)
    return csv_path

def create_sample_provider_csv():
    """Create sample provider tasks CSV for testing"""
    data = [
        {
            'staff_code': 'PRV001',
            'patient_id': 'MRN123456',
            'task_date': '2025-09-27',
            'task_id': 1001,
            'provider_id': 101,
            'provider_name': 'Dr. Smith',
            'patient_name': 'John Doe',
            'status': 'completed',
            'notes': 'Annual wellness visit',
            'minutes_of_service': 60,
            'billing_code_id': 201,
            'billing_code': '99213',
            'billing_code_description': 'Office visit',
            'task_description': 'Routine checkup'
        },
        {
            'staff_code': 'PRV002',
            'patient_id': 'MRN789012',
            'task_date': '2025-09-28',
            'task_id': 1002,
            'provider_id': 102,
            'provider_name': 'Dr. Johnson',
            'patient_name': 'Jane Smith',
            'status': 'completed',
            'notes': 'Follow-up visit',
            'minutes_of_service': 30,
            'billing_code_id': 202,
            'billing_code': '99212',
            'billing_code_description': 'Brief office visit',
            'task_description': 'Follow-up care'
        },
        {
            'staff_code': 'PRV001',
            'patient_id': 'MRN345678',
            'task_date': '2025-09-29',
            'task_id': 1003,
            'provider_id': 101,
            'provider_name': 'Dr. Smith',
            'patient_name': 'Bob Wilson',
            'status': 'completed',
            'notes': 'Medication review',
            'minutes_of_service': 45,
            'billing_code_id': 203,
            'billing_code': '99214',
            'billing_code_description': 'Extended office visit',
            'task_description': 'Medication management'
        }
    ]
    
    df = pd.DataFrame(data)
    csv_path = 'test_provider_tasks_sept_27_30.csv'
    df.to_csv(csv_path, index=False)
    return csv_path

def create_sample_patient_csv():
    """Create sample patient CSV for testing"""
    data = [
        {
            'patient_id': 'MRN123456',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1980-05-15',
            'gender': 'M',
            'phone': '555-0101',
            'email': 'john.doe@email.com',
            'address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '90210',
            'insurance_info': 'Blue Cross',
            'medical_conditions': 'Hypertension, Diabetes'
        },
        {
            'patient_id': 'MRN789012',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1975-08-22',
            'gender': 'F',
            'phone': '555-0102',
            'email': 'jane.smith@email.com',
            'address': '456 Oak Ave',
            'city': 'Somewhere',
            'state': 'NY',
            'zip_code': '10001',
            'insurance_info': 'Aetna',
            'medical_conditions': 'Asthma'
        },
        {
            'patient_id': 'MRN345678',
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'date_of_birth': '1990-12-03',
            'gender': 'M',
            'phone': '555-0103',
            'email': 'bob.wilson@email.com',
            'address': '789 Pine Rd',
            'city': 'Elsewhere',
            'state': 'TX',
            'zip_code': '75001',
            'insurance_info': 'United Healthcare',
            'medical_conditions': 'None'
        }
    ]
    
    df = pd.DataFrame(data)
    csv_path = 'test_patients_sept_27_30.csv'
    df.to_csv(csv_path, index=False)
    return csv_path

def check_import_results():
    """Check the results of the import in the database"""
    print("\n=== Checking Import Results ===")
    
    with sqlite3.connect('production.db') as conn:
        # Check coordinator tasks
        coord_query = "SELECT COUNT(*) FROM coordinator_tasks_2025_09 WHERE task_date BETWEEN '2025-09-27' AND '2025-09-30'"
        coord_count = conn.execute(coord_query).fetchone()[0]
        print(f"Coordinator tasks imported: {coord_count}")
        
        # Check provider tasks
        prov_query = "SELECT COUNT(*) FROM provider_tasks_2025_09 WHERE task_date BETWEEN 1727395200 AND 1727654400"  # Unix timestamps for Sept 27-30
        prov_count = conn.execute(prov_query).fetchone()[0]
        print(f"Provider tasks imported: {prov_count}")
        
        # Check patients
        patient_query = "SELECT COUNT(*) FROM patients WHERE patient_id IN ('123456', '789012', '345678')"
        patient_count = conn.execute(patient_query).fetchone()[0]
        print(f"Patients imported: {patient_count}")
        
        # Show sample data
        print("\n=== Sample Coordinator Tasks ===")
        coord_sample = conn.execute("""
            SELECT coordinator_id, patient_id, task_date, duration_minutes, task_type 
            FROM coordinator_tasks_2025_09 
            WHERE task_date BETWEEN '2025-09-27' AND '2025-09-30'
            LIMIT 3
        """).fetchall()
        
        for row in coord_sample:
            print(f"Coordinator: {row[0]}, Patient: {row[1]}, Date: {row[2]}, Duration: {row[3]}, Type: {row[4]}")
        
        print("\n=== Sample Provider Tasks ===")
        prov_sample = conn.execute("""
            SELECT provider_name, patient_name, billing_code, minutes_of_service
            FROM provider_tasks_2025_09 
            WHERE month = 9 AND year = 2025
            LIMIT 3
        """).fetchall()
        
        for row in prov_sample:
            print(f"Provider: {row[0]}, Patient: {row[1]}, Code: {row[2]}, Minutes: {row[3]}")

def run_test():
    """Run the complete test"""
    print("=== Testing Direct Import for September 27-30, 2025 ===")
    
    try:
        # Create sample CSV files
        print("Creating sample CSV files...")
        coord_csv = create_sample_coordinator_csv()
        provider_csv = create_sample_provider_csv()
        patient_csv = create_sample_patient_csv()
        
        print(f"Created: {coord_csv}, {provider_csv}, {patient_csv}")
        
        # Initialize importer
        importer = DirectImportSept2025()
        
        # Run import
        print("Running import...")
        importer.run_import(
            coordinator_csv=coord_csv,
            provider_csv=provider_csv,
            patient_csv=patient_csv
        )
        
        # Check results
        check_import_results()
        
        # Cleanup test files
        for file in [coord_csv, provider_csv, patient_csv]:
            if os.path.exists(file):
                os.remove(file)
        
        print("\n=== Test Completed Successfully ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    run_test()