#!/usr/bin/env python3
"""
Add debug output to process_zmo to see what's happening with assignments
"""

import sqlite3
import subprocess
import sys
import os

# Add debug print statements to the transform function
def add_debug_to_transform():
    print("Adding debug output to process_zmo function...")
    
    # Read the current file
    with open('transform_production_data_v3_fixed.py', 'r') as f:
        content = f.read()
    
    # Add debug output after the provider/coordinator lookup
    old_code = """            # Provider lookup using ZMO name cleaning logic
            provider_id = None
            if assigned_prov:
                provider_id = find_provider_by_zmo_name(conn, assigned_prov)

            # Coordinator lookup using first name matching
            coordinator_id = None
            if assigned_cm:
                coordinator_id = find_coordinator_by_zmo_name(conn, assigned_cm)"""
    
    new_code = """            # Provider lookup using ZMO name cleaning logic
            provider_id = None
            if assigned_prov:
                provider_id = find_provider_by_zmo_name(conn, assigned_prov)
                if provider_id:
                    print(f"    Provider match: '{assigned_prov}' -> ID: {provider_id}")
                else:
                    print(f"    No provider match for: '{assigned_prov}'")

            # Coordinator lookup using first name matching
            coordinator_id = None
            if assigned_cm:
                coordinator_id = find_coordinator_by_zmo_name(conn, assigned_cm)
                if coordinator_id:
                    print(f"    Coordinator match: '{assigned_cm}' -> ID: {coordinator_id}")
                else:
                    print(f"    No coordinator match for: '{assigned_cm}'")"""
    
    # Replace the code
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        # Also add debug for assignments_data
        old_assign_code = """            # Assignments
            if provider_id or coordinator_id:
                assignments_data.append((patient_id, provider_id, coordinator_id))"""
        
        new_assign_code = """            # Assignments
            if provider_id or coordinator_id:
                assignments_data.append((patient_id, provider_id, coordinator_id))
                print(f"    Assignment created: patient={patient_id}, provider={provider_id}, coordinator={coordinator_id}")"""
        
        if old_assign_code in content:
            content = content.replace(old_assign_code, new_assign_code)
        
        # Write back to file
        with open('transform_production_data_v3_fixed.py', 'w') as f:
            f.write(content)
        
        print("Debug output added successfully!")
    else:
        print("Could not find the code to replace")

if __name__ == "__main__":
    add_debug_to_transform()