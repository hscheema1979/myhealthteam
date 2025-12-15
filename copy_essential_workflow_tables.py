#!/usr/bin/env python3
"""
Copy essential workflow infrastructure tables from backup database to current production.db
This ensures dashboards have access to required static tables that were cleaned up.
"""

import sqlite3
import sys
from datetime import datetime

def get_db_connection(db_path):
    """Return a SQLite connection with row_factory"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def copy_table_structure_and_data(source_conn, target_conn, table_name):
    """Copy table structure and data from source to target"""
    try:
        # Get table schema
        cursor = source_conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"  ⚠️  Table {table_name} not found in source database")
            return False
            
        # Build CREATE TABLE statement
        column_defs = []
        for col in columns:
            col_name = col['name']
            col_type = col['type']
            col_notnull = "NOT NULL" if col['notnull'] else ""
            col_default = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] else ""
            col_pk = "PRIMARY KEY" if col['pk'] else ""
            
            col_def = f"{col_name} {col_type} {col_notnull} {col_default} {col_pk}".strip()
            column_defs.append(col_def)
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
        
        # Execute CREATE TABLE
        target_conn.execute(create_sql)
        
        # Copy data
        source_data = source_conn.execute(f"SELECT * FROM {table_name}").fetchall()
        
        if source_data:
            # Build INSERT statement
            col_names = [col['name'] for col in columns]
            placeholders = ', '.join(['?' for _ in col_names])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({placeholders})"
            
            # Insert data
            for row in source_data:
                values = [row[col_name] for col_name in col_names]
                target_conn.execute(insert_sql, values)
            
            print(f"  ✅ Copied {len(source_data)} rows to {table_name}")
        else:
            print(f"  ✅ Created empty table {table_name}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error copying {table_name}: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("Copying Essential Workflow Infrastructure Tables")
    print("=" * 60)
    print(f"Source: production_backup_prototype_test.db")
    print(f"Target: production.db")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Essential workflow tables that dashboards depend on
    essential_tables = [
        # Core workflow infrastructure
        'onboarding_tasks',
        'workflow_instances', 
        'workflow_steps',
        'workflow_templates',
        
        # Reference tables
        'coordinator_billing_codes',
        'coordinator_code_map',
        'patient_status_types',
        'provider_code_map',
        'provider_specialties',
        'region_providers',
        'regions',
        'specialties',
        'staff_code_mapping',
        'staff_codes',
        
        # Dashboard summary tables (structure only, will be repopulated)
        'coordinator_monthly_summary',
        'provider_monthly_summary',
        'provider_weekly_summary_with_billing'
    ]
    
    source_db = "production_backup_prototype_test.db"
    target_db = "production.db"
    
    try:
        # Connect to databases
        source_conn = get_db_connection(source_db)
        target_conn = get_db_connection(target_db)
        
        print(f"Connected to source: {source_db}")
        print(f"Connected to target: {target_db}")
        print()
        
        success_count = 0
        total_count = len(essential_tables)
        
        for table_name in essential_tables:
            print(f"Processing: {table_name}")
            if copy_table_structure_and_data(source_conn, target_conn, table_name):
                success_count += 1
            print()
        
        # Commit changes
        target_conn.commit()
        
        print("=" * 60)
        print(f"SUMMARY: {success_count}/{total_count} tables copied successfully")
        
        if success_count == total_count:
            print("✅ All essential workflow tables copied successfully!")
        else:
            print("⚠️  Some tables failed to copy - review errors above")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
        
    finally:
        # Close connections
        if 'source_conn' in locals():
            source_conn.close()
        if 'target_conn' in locals():
            target_conn.close()

if __name__ == "__main__":
    main()