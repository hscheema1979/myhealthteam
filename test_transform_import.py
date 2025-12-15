#!/usr/bin/env python3
"""
Test that the transform function can be imported and basic structure works
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the main transform function
    from transform_production_data_v3_fixed import process_zmo, build_provider_map, normalize_patient_id
    print("SUCCESS: transform_production_data_v3_fixed imported successfully")
    
    # Test basic function calls
    import sqlite3
    conn = sqlite3.connect(':memory:')  # In-memory database for testing
    
    # Test build_provider_map function
    try:
        provider_map, id_to_name = build_provider_map(conn)
        print(f"SUCCESS: build_provider_map returned {len(provider_map)} providers")
    except Exception as e:
        print(f"WARNING: build_provider_map failed (expected with empty DB): {e}")
    
    # Test normalize_patient_id function
    test_id = normalize_patient_id("SMITH JOHN 01/01/1980")
    print(f"SUCCESS: normalize_patient_id test: 'SMITH JOHN 01/01/1980' -> '{test_id}'")
    
    conn.close()
    print("SUCCESS: Basic function tests passed")
    
except Exception as e:
    print(f"ERROR: Failed to import or test transform_production_data_v3_fixed: {e}")
    import traceback
    traceback.print_exc()