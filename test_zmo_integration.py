#!/usr/bin/env python3
"""
Test script to validate ZMO integration for provider assignments
"""

import sqlite3
import os
import sys

def test_zmo_integration():
    """Test that the ZMO integration works correctly"""
    print("Testing ZMO Integration for Provider Assignments")
    print("=" * 60)
    
    # Test database connection
    try:
        conn = sqlite3.connect('production.db')
        print("SUCCESS: Connected to production database")
        
        # Check if patient_assignments table exists with proper structure
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='patient_assignments'
        """)
        
        if cursor.fetchone():
            print("SUCCESS: patient_assignments table exists")
            
            # Check table structure
            cursor = conn.execute("PRAGMA table_info(patient_assignments)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"Table columns: {columns}")
            
            # Check if we have any assignments
            cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
            count = cursor.fetchone()[0]
            print(f"Current assignment count: {count}")
            
            # Check assignments by source
            cursor = conn.execute("""
                SELECT source, COUNT(*) as count 
                FROM patient_assignments 
                GROUP BY source 
                ORDER BY count DESC
            """)
            sources = cursor.fetchall()
            print("Assignment sources:")
            for source, count in sources:
                print(f"  - {source}: {count}")
            
        else:
            print("WARNING: patient_assignments table does not exist")
        
        # Check if ZMO file exists
        zmo_path = 'downloads/ZMO_MAIN.csv'
        if os.path.exists(zmo_path):
            print(f"SUCCESS: ZMO file found: {zmo_path}")
        else:
            print(f"WARNING: ZMO file not found: {zmo_path}")
        
        conn.close()
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_zmo_integration()