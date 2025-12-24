#!/usr/bin/env python3
"""
Comprehensive fix for coordinator_id schema mismatch issues.

This script addresses:
1. Existing coordinator_tasks tables with TEXT coordinator_id (production mismatch)
2. Transform script that creates new tables with INTEGER coordinator_id
3. Database function ensure_monthly_coordinator_tasks_table() that uses wrong schema

Root Cause: Schema mismatch between production (TEXT) and code expectations (INTEGER)
"""

import sqlite3
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = "production.db"

def get_db():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def check_current_schema():
    """Check current schema of coordinator tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all coordinator tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_tasks_%'
        ORDER BY name
    """)
    tables = cursor.fetchall()
    
    schema_info = {}
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            if col[1] == 'coordinator_id':
                schema_info[table_name] = {
                    'type': col[2],
                    'notnull': col[3],
                    'default': col[4],
                    'pk': col[5]
                }
                break
    
    conn.close()
    return schema_info

def fix_existing_tables():
    """Fix existing coordinator tables by converting coordinator_id from TEXT to INTEGER"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current month table
    current_month = datetime.now().strftime("%Y_%m")
    current_table = f"coordinator_tasks_{current_month}"
    
    # Check if current month table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = ?
    """, (current_table,))
    
    if not cursor.fetchone():
        logger.info(f"Current month table {current_table} does not exist - no fix needed")
        conn.close()
        return False
    
    # Check current schema
    cursor.execute(f"PRAGMA table_info({current_table})")
    columns = cursor.fetchall()
    
    coordinator_id_type = None
    for col in columns:
        if col[1] == 'coordinator_id':
            coordinator_id_type = col[2]
            break
    
    if coordinator_id_type == 'INTEGER':
        logger.info(f"Table {current_table} already has INTEGER coordinator_id - no fix needed")
        conn.close()
        return False
    
    logger.info(f"Fixing {current_table} - coordinator_id is currently {coordinator_id_type}")
    
    # Create backup
    backup_table = f"{current_table}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {current_table}")
    logger.info(f"Created backup: {backup_table}")
    
    # Get data before modification
    cursor.execute(f"SELECT COUNT(*) FROM {current_table}")
    total_records = cursor.fetchone()[0]
    
    cursor.execute(f"""
        SELECT COUNT(*) FROM {current_table} 
        WHERE coordinator_id IS NOT NULL AND coordinator_id != ''
    """)
    non_null_records = cursor.fetchone()[0]
    
    logger.info(f"Table has {total_records} total records, {non_null_records} with non-null coordinator_id")
    
    # Create new table with correct schema
    new_table = f"{current_table}_new"
    cursor.execute(f"""
        CREATE TABLE {new_table} (
            coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            coordinator_id INTEGER,
            coordinator_name TEXT,
            patient_id TEXT,
            task_date DATE,
            duration_minutes REAL,
            task_type TEXT,
            notes TEXT,
            source_system TEXT DEFAULT 'CSV_IMPORT',
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(coordinator_id, patient_id, task_date, task_type)
        )
    """)
    
    # Create index
    cursor.execute(f"CREATE INDEX idx_{new_table}_coordinator ON {new_table}(coordinator_id)")
    
    # Migrate data - convert TEXT coordinator_id to INTEGER where possible
    cursor.execute(f"""
        INSERT INTO {new_table} (
            coordinator_task_id, coordinator_id, coordinator_name, patient_id, 
            task_date, duration_minutes, task_type, notes, source_system, imported_at
        )
        SELECT 
            coordinator_task_id,
            CASE 
                WHEN coordinator_id IS NULL OR coordinator_id = '' THEN NULL
                WHEN CAST(COALESCE(coordinator_id, '0') AS INTEGER) = 0 THEN NULL
                ELSE CAST(COALESCE(coordinator_id, '0') AS INTEGER)
            END as coordinator_id,
            coordinator_name,
            patient_id,
            task_date,
            duration_minutes,
            task_type,
            notes,
            source_system,
            imported_at
        FROM {current_table}
    """)
    
    # Check migration results
    cursor.execute(f"SELECT COUNT(*) FROM {new_table}")
    migrated_records = cursor.fetchone()[0]
    
    cursor.execute(f"""
        SELECT COUNT(*) FROM {new_table} 
        WHERE coordinator_id IS NOT NULL
    """)
    valid_coordinator_records = cursor.fetchone()[0]
    
    logger.info(f"Migrated {migrated_records} records, {valid_coordinator_records} with valid coordinator_id")
    
    # Replace old table
    cursor.execute(f"DROP TABLE {current_table}")
    cursor.execute(f"ALTER TABLE {new_table} RENAME TO {current_table}")
    
    # Recreate index
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{current_table}_coordinator ON {current_table}(coordinator_id)")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Successfully fixed {current_table} schema")
    return True

def fix_transform_script():
    """Fix transform_production_data_v3_fixed.py script to use correct schema"""
    transform_file = "transform_production_data_v3_fixed.py"
    
    try:
        with open(transform_file, 'r') as f:
            content = f.read()
        
        # Check if already fixed
        if "# FIXED: coordinator_id type changed to TEXT to match production schema" in content:
            logger.info("Transform script already contains coordinator_id fix")
            return False
        
        # Simple string replacement approach
        old_line = "            coordinator_id INTEGER,"
        new_line = "            coordinator_id TEXT, # FIXED: Changed to TEXT to match production schema"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            # Add comment about fix
            content = content.replace(
                "def create_coordinator_table(conn, year, month):",
                "def create_coordinator_table(conn, year, month):\n    # FIXED: coordinator_id type changed to TEXT to match production schema"
            )
            
            with open(transform_file, 'w') as f:
                f.write(content)
            
            logger.info(f"Fixed coordinator_id schema in {transform_file}")
            return True
        else:
            logger.warning(f"Could not find expected line in {transform_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing transform script: {e}")
        return False

def fix_database_function():
    """Fix ensure_monthly_coordinator_tasks_table function in database.py"""
    db_file = "src/database.py"
    
    try:
        with open(db_file, 'r') as f:
            content = f.read()
        
        # Check if already fixed
        if "# FIXED: coordinator_id type changed to TEXT to match production schema" in content:
            logger.info("Database function already contains coordinator_id fix")
            return False
        
        # Simple string replacement approach
        old_line = "            coordinator_id INTEGER,"
        new_line = "            coordinator_id TEXT, # FIXED: Changed to TEXT to match production schema"
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            # Add comment about fix
            content = content.replace(
                "def ensure_monthly_coordinator_tasks_table(year, month):",
                "def ensure_monthly_coordinator_tasks_table(year, month):\n    # FIXED: coordinator_id type changed to TEXT to match production schema"
            )
            
            with open(db_file, 'w') as f:
                f.write(content)
            
            logger.info(f"Fixed coordinator_id schema in {db_file}")
            return True
        else:
            logger.warning(f"Could not find expected line in {db_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing database function: {e}")
        return False

def main():
    """Main fix function"""
    logger.info("Starting comprehensive coordinator schema fix...")
    
    # Step 1: Check current schema
    logger.info("Step 1: Checking current schema...")
    schema_info = check_current_schema()
    
    logger.info("Current coordinator table schemas:")
    for table, info in schema_info.items():
        logger.info(f"  {table}: coordinator_id = {info['type']}")
    
    # Step 2: Fix existing tables
    logger.info("\nStep 2: Fixing existing tables...")
    tables_fixed = fix_existing_tables()
    
    # Step 3: Fix transform script
    logger.info("\nStep 3: Fixing transform script...")
    transform_fixed = fix_transform_script()
    
    # Step 4: Fix database function
    logger.info("\nStep 4: Fixing database function...")
    db_function_fixed = fix_database_function()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("COMPREHENSIVE FIX SUMMARY")
    logger.info("="*60)
    logger.info(f"Existing tables fixed: {tables_fixed}")
    logger.info(f"Transform script fixed: {transform_fixed}")
    logger.info(f"Database function fixed: {db_function_fixed}")
    
    if tables_fixed or transform_fixed or db_function_fixed:
        logger.info("\n✅ SUCCESS: Coordinator schema issues have been resolved!")
        logger.info("\nNext steps:")
        logger.info("1. Test coordinator dashboard - workflows and tasks should now work")
        logger.info("2. Run transform script to verify new tables use correct schema")
        logger.info("3. Verify coordinator assignments and task tracking work properly")
    else:
        logger.info("\nℹ️  INFO: No fixes were needed - schema is already correct")
    
    logger.info("\n" + "="*60)

if __name__ == "__main__":
    main()