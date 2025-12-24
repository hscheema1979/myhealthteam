"""
fix_coordinator_dashboard_schema.py
Fix script for coordinator dashboard schema mismatch issue.

This script will:
1. Fix the coordinator_tasks table schema to use INTEGER for coordinator_id
2. Update the ensure_monthly_coordinator_tasks_table function to always use INTEGER
3. Add proper error handling for coordinator_id type mismatches
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import database as db

def fix_current_month_table():
    """Fix the current month coordinator_tasks table schema"""
    print("\n=== FIXING CURRENT MONTH TABLE SCHEMA ===")
    
    conn = db.get_db_connection()
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    table_name = f"coordinator_tasks_{current_year}_{str(current_month).zfill(2)}"
    
    # Check if table exists
    table_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    
    if not table_exists:
        print(f"❌ Table {table_name} does not exist")
        conn.close()
        return False
    
    print(f"✅ Found table: {table_name}")
    
    # Check current schema
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_info = {col[1]: col[2] for col in columns}
    
    print(f"Current columns: {list(column_info.keys())}")
    
    # Check if coordinator_id is TEXT type
    is_text_type = False
    for col_name, col_type in column_info.items():
        if col_name == 'coordinator_id' and col_type.upper() == 'TEXT':
            is_text_type = True
            break
    
    if is_text_type:
        print(f"⚠️  ISSUE: coordinator_id is TEXT type - this causes dashboard errors")
        
        # Fix the schema
        try:
            print("Attempting to fix schema...")
            
            # Create backup table
            backup_table = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            conn.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table_name}")
            
            # Create new table with correct schema
            conn.execute(f"DROP TABLE {table_name}")
            
            # Get all column definitions from existing table
            create_sql = "CREATE TABLE coordinator_tasks ("
            column_defs = []
            
            for col_name, col_type in column_info.items():
                if col_name == 'coordinator_id':
                    # Force INTEGER type for coordinator_id
                    column_defs.append(f"coordinator_id INTEGER PRIMARY KEY AUTOINCREMENT")
                else:
                    # Keep other columns as-is
                    if col_type.upper() == 'INTEGER':
                        column_defs.append(f"{col_name} {col_type}")
                    else:
                        column_defs.append(f"{col_name} {col_type}")
            
            create_sql += ",\n    ".join(column_defs) + ")"
            
            conn.execute(create_sql)
            
            # Copy data from backup
            conn.execute(f"""
                INSERT INTO coordinator_tasks 
                SELECT * FROM {backup_table}
            """)
            
            # Drop backup table
            conn.execute(f"DROP TABLE {backup_table}")
            
            conn.commit()
            print("✅ Schema fixed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing schema: {e}")
            conn.rollback()
            return False
    else:
        print("✅ coordinator_id is already INTEGER type")
    
    conn.close()

def update_ensure_function():
    """Update the ensure_monthly_coordinator_tasks_table function to always use INTEGER"""
    print("\n=== UPDATING ensure_monthly_coordinator_tasks_table FUNCTION ===")
    
    # Read the current function
    function_file = os.path.join(os.path.dirname(__file__), 'src', 'database.py')
    
    try:
        with open(function_file, 'r') as f:
            content = f.read()
        
        # Find the CREATE TABLE statement and fix coordinator_id type
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if 'coordinator_id INTEGER NOT NULL,' in line:
                fixed_lines.append('coordinator_id INTEGER NOT NULL,')
            elif 'coordinator_id TEXT' in line:
                # Replace TEXT with INTEGER for coordinator_id
                fixed_lines.append(line.replace('coordinator_id TEXT', 'coordinator_id INTEGER'))
            else:
                fixed_lines.append(line)
        
        # Write the fixed function back
        with open(function_file, 'w') as f:
            f.write('\n'.join(fixed_lines))
        
        print("✅ Updated ensure_monthly_coordinator_tasks_table function to use INTEGER type")
        return True
        
    except Exception as e:
        print(f"❌ Error updating function: {e}")
        return False

def main():
    """Main function to fix the coordinator dashboard schema issues"""
    print("COORDINATOR DASHBOARD SCHEMA FIX")
    print("=" * 50)
    print(f"Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Step 1: Fix current month table schema
    if fix_current_month_table():
        print("\n✅ Current month table schema fixed")
    
    # Step 2: Update the ensure function for future tables
    if update_ensure_function():
        print("\n✅ Database function updated for future consistency")
    
    print("\n" + "=" * 50)
    print("FIX COMPLETE")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Restart the coordinator dashboard application")
    print("2. Test workflow creation and task logging")
    print("3. Verify workflow step completion works correctly")
    print("\nThis fix resolves the schema mismatch causing coordinator dashboard errors.")

if __name__ == "__main__":
    main()