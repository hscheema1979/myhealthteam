#!/usr/bin/env python3
"""
Test the ZMO processing flow without running the full transform
"""

import sqlite3
import os
import pandas as pd
import sys

# Create a minimal test database
def create_test_db():
    conn = sqlite3.connect('test_zmo.db')
    
    # Create users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # Insert test providers
    test_providers = [
        (1, 'ZEN-ANE', 'Anela', 'Lourdes', 'Anela Lourdes'),
        (2, 'ZEN-DIA', 'Diana', 'Gomez', 'Diana Gomez'),
        (3, 'ZEN-MEC', 'Meghan', 'Craig', 'Meghan Craig'),
    ]
    
    for provider in test_providers:
        conn.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?, 'active')", provider)
    
    # Create patients table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            date_of_birth DATE
        )
    """)
    
    # Create patient_assignments table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patient_assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            provider_id INTEGER,
            coordinator_id INTEGER,
            assignment_date TEXT DEFAULT (datetime('now'))
        )
    """)
    
    conn.commit()
    return conn

# Create a minimal ZMO test file
def create_test_zmo():
    test_data = {
        'Last': ['SMITH', 'JOHNSON', 'WILLIAMS'],
        'First': ['JOHN', 'JANE', 'BOB'],
        'DOB': ['01/01/1980', '02/02/1985', '03/03/1990'],
        'Assigned Reg Prov': ['ZEN-ANE', 'ZEN-DIA', 'ZEN-MEC'],
        'Assigned CM': ['ZEN-DIA', 'ZEN-MEC', 'ZEN-ANE'],
        'Fac': ['FACILITY1', 'FACILITY2', 'FACILITY3'],
        'Phone': ['555-0101', '555-0102', '555-0103'],
        'Street': ['123 Main St', '456 Oak Ave', '789 Pine Rd'],
        'City': ['Anytown', 'Somewhere', 'Elsewhere'],
        'State': ['CA', 'NY', 'TX'],
        'Zip': ['12345', '67890', '54321'],
        'Ins1': ['Insurance1', 'Insurance2', 'Insurance3'],
        'Policy': ['POL001', 'POL002', 'POL003'],
        'Pt Status': ['Active', 'Active', 'Active'],
        'Initial TV\nDate': ['', '', ''],
        'Initial TV\nNotes': ['', '', ''],
        'Initial TV\nProv': ['', '', ''],
        'Assigned \nReg Prov': ['ZEN-ANE', 'ZEN-DIA', 'ZEN-MEC'],
        'Assigned\nCM': ['ZEN-DIA', 'ZEN-MEC', 'ZEN-ANE']
    }
    
    df = pd.DataFrame(test_data)
    df.to_csv('test_zmo_main.csv', index=False)
    print("Created test ZMO file: test_zmo_main.csv")
    return 'test_zmo_main.csv'

# Test the flow
def test_flow():
    print("Testing ZMO Processing Flow")
    print("=" * 50)
    
    # Create test database
    conn = create_test_db()
    print("Created test database with sample providers")
    
    # Create test ZMO file
    zmo_file = create_test_zmo()
    
    # Import the process_zmo function
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from transform_production_data_v3_fixed import process_zmo, build_provider_map, normalize_patient_id
    
    # Build provider map
    provider_map, id_to_name = build_provider_map(conn)
    print(f"Built provider map with {len(provider_map)} entries")
    
    # Test patient ID normalization
    test_patient = normalize_patient_id("SMITH JOHN 01/01/1980")
    print(f"Normalized patient ID: {test_patient}")
    
    # Process ZMO (this should create patients and assignments)
    try:
        patients_count, assignments_count = process_zmo(zmo_file, conn, provider_map)
        print(f"ZMO processing results:")
        print(f"  - Patients created: {patients_count}")
        print(f"  - Assignments created: {assignments_count}")
        
        # Verify assignments
        cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
        total_assignments = cursor.fetchone()[0]
        print(f"Total assignments in database: {total_assignments}")
        
        # Show sample assignments
        cursor = conn.execute("""
            SELECT pa.patient_id, pa.provider_id, pa.coordinator_id, u1.full_name as provider_name, u2.full_name as coordinator_name
            FROM patient_assignments pa
            LEFT JOIN users u1 ON pa.provider_id = u1.user_id
            LEFT JOIN users u2 ON pa.coordinator_id = u2.user_id
            LIMIT 5
        """)
        
        print("Sample assignments:")
        for row in cursor.fetchall():
            patient_id, prov_id, coord_id, prov_name, coord_name = row
            print(f"  Patient: {patient_id}")
            print(f"    Provider: {prov_name} (ID: {prov_id})")
            print(f"    Coordinator: {coord_name} (ID: {coord_id})")
        
    except Exception as e:
        print(f"Error processing ZMO: {e}")
        import traceback
        traceback.print_exc()
    
    conn.close()
    print("\nTest completed!")

if __name__ == "__main__":
    test_flow()