#!/usr/bin/env python3
"""
Analyze schema gaps between care provider dashboard requirements and current database schema.
"""

import sqlite3
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

from src import database

def get_table_columns(conn, table_name):
    """Get all columns for a table"""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return columns

def analyze_schema_gaps():
    """Analyze gaps between dashboard requirements and current schema"""
    
    # Fields used in care provider dashboard
    dashboard_fields = {
        # Basic task fields
        'task_date': 'DATE',
        'notes': 'TEXT',
        
        # Clinical fields from dashboard
        'er_count_1yr': 'INTEGER',
        'hospitalization_count_1yr': 'INTEGER', 
        'subjective_risk_level': 'TEXT',  # Changed from INTEGER to TEXT to store full description
        'mental_health_concerns': 'INTEGER',
        'provider_mh_schizophrenia': 'BOOLEAN',
        'provider_mh_depression': 'BOOLEAN',
        'provider_mh_anxiety': 'BOOLEAN',
        'provider_mh_stress': 'BOOLEAN',
        'provider_mh_adhd': 'BOOLEAN',
        'provider_mh_bipolar': 'BOOLEAN',
        'provider_mh_suicidal': 'BOOLEAN',
        'active_specialists': 'TEXT',
        'code_status': 'TEXT',
        'cognitive_function': 'TEXT',
        'functional_status': 'TEXT',
        'goals_of_care': 'TEXT',
        'active_concerns': 'TEXT',
        'chronic_conditions_provider': 'TEXT',
        'last_visit_date': 'DATE',
        
        # Additional fields that may be needed
        'goc_value': 'TEXT',  # Goals of Care dropdown value
    }
    
    conn = database.get_db_connection()
    
    try:
        # Get current patients table columns
        patients_columns = get_table_columns(conn, 'patients')
        print("=== SCHEMA GAP ANALYSIS ===\n")
        print(f"Current patients table has {len(patients_columns)} columns")
        print(f"Dashboard requires {len(dashboard_fields)} clinical fields")
        
        # Check which fields are missing
        missing_fields = []
        existing_fields = []
        
        for field, field_type in dashboard_fields.items():
            if field in patients_columns:
                existing_fields.append(field)
            else:
                missing_fields.append((field, field_type))
        
        print(f"\n=== EXISTING FIELDS ({len(existing_fields)}) ===")
        for field in existing_fields:
            print(f"  ✓ {field}")
        
        print(f"\n=== MISSING FIELDS ({len(missing_fields)}) ===")
        for field, field_type in missing_fields:
            print(f"  ✗ {field} ({field_type})")
        
        # Check patient_panel table as well
        try:
            panel_columns = get_table_columns(conn, 'patient_panel')
            print(f"\n=== PATIENT_PANEL TABLE ({len(panel_columns)} columns) ===")
            
            panel_missing = []
            panel_existing = []
            
            for field, field_type in dashboard_fields.items():
                if field in panel_columns:
                    panel_existing.append(field)
                else:
                    panel_missing.append((field, field_type))
            
            print(f"Existing in patient_panel: {len(panel_existing)}")
            print(f"Missing from patient_panel: {len(panel_missing)}")
            
        except Exception as e:
            print(f"Could not analyze patient_panel table: {e}")
        
        # Generate SQL for missing fields
        if missing_fields:
            print(f"\n=== SUGGESTED SQL MIGRATION ===")
            print("-- Add missing columns to patients table")
            for field, field_type in missing_fields:
                default_value = ""
                if field_type == "BOOLEAN":
                    default_value = " DEFAULT FALSE"
                elif field_type == "INTEGER":
                    default_value = " DEFAULT 0"
                elif field_type == "TEXT":
                    default_value = " DEFAULT NULL"
                elif field_type == "DATE":
                    default_value = " DEFAULT NULL"
                    
                print(f"ALTER TABLE patients ADD COLUMN {field} {field_type}{default_value};")
            
            # Also suggest patient_panel updates
            print("\n-- Add missing columns to patient_panel table")
            for field, field_type in missing_fields:
                default_value = ""
                if field_type == "BOOLEAN":
                    default_value = " DEFAULT FALSE"
                elif field_type == "INTEGER":
                    default_value = " DEFAULT 0"
                elif field_type == "TEXT":
                    default_value = " DEFAULT NULL"
                elif field_type == "DATE":
                    default_value = " DEFAULT NULL"
                    
                print(f"ALTER TABLE patient_panel ADD COLUMN {field} {field_type}{default_value};")
        
        return missing_fields, existing_fields
        
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_schema_gaps()