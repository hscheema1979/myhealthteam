#!/usr/bin/env python3
"""
Fix all coordinator-related table schemas to use TEXT for coordinator_id instead of INTEGER
"""
import sqlite3
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "production.db"

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def get_coordinator_tables(conn):
    """Get all coordinator-related tables"""
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]

def fix_table_schema(conn, table_name):
    """Fix coordinator_id column in a table to be TEXT instead of INTEGER"""
    try:
        # Check current schema
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Find coordinator_id column
        coordinator_id_info = None
        for col in columns:
            if col[1] == 'coordinator_id':
                coordinator_id_info = col
                break
        
        if not coordinator_id_info:
            logger.info(f"  No coordinator_id column found in {table_name}")
            return False
            
        # Check if it's already TEXT
        if coordinator_id_info[2].upper() == 'TEXT':
            logger.info(f"  {table_name} already has TEXT coordinator_id")
            return False
            
        logger.info(f"  Fixing {table_name}: changing coordinator_id from {coordinator_id_info[2]} to TEXT")
        
        # Get all column names and types
        column_defs = []
        for col in columns:
            if col[1] == 'coordinator_id':
                # Change to TEXT
                nullable = "" if col[3] else " NOT NULL"
                default_clause = f" DEFAULT {col[4]}" if col[4] is not None else ""
                column_defs.append(f"coordinator_id TEXT{nullable}{default_clause}")
            else:
                nullable = "" if col[3] else " NOT NULL"
                default_clause = f" DEFAULT {col[4]}" if col[4] is not None else ""
                column_defs.append(f"{col[1]} {col[2]}{nullable}{default_clause}")
        
        # Create new table with correct schema
        new_table_name = f"{table_name}_new"
        column_def_str = ",\n    ".join(column_defs)
        
        # Drop new table if exists
        conn.execute(f"DROP TABLE IF EXISTS {new_table_name}")
        
        # Create new table
        conn.execute(f"""
            CREATE TABLE {new_table_name} (
                {column_def_str}
            )
        """)
        
        # Copy data from old table to new table
        column_names = [col[1] for col in columns]
        columns_str = ", ".join(column_names)
        conn.execute(f"INSERT INTO {new_table_name} SELECT {columns_str} FROM {table_name}")
        
        # Drop old table and rename new table
        conn.execute(f"DROP TABLE {table_name}")
        conn.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")
        
        logger.info(f"  Successfully fixed {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"  Error fixing {table_name}: {e}")
        return False

def fix_transform_script():
    """Fix the transform script to create tables with TEXT coordinator_id"""
    try:
        script_path = "transform_production_data_v3_fixed.py"
        if not os.path.exists(script_path):
            logger.warning(f"Transform script {script_path} not found")
            return False
            
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix coordinator table creation
        old_pattern = "coordinator_id INTEGER,"
        new_pattern = "coordinator_id TEXT,"
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("  Fixed transform script")
            return True
        else:
            logger.info("  Transform script already has correct coordinator_id type")
            return False
            
    except Exception as e:
        logger.error(f"  Error fixing transform script: {e}")
        return False

def fix_post_import_sql():
    """Fix the post import SQL script to create tables with TEXT coordinator_id"""
    try:
        script_path = "src/sql/post_import_processing.sql"
        if not os.path.exists(script_path):
            logger.warning(f"Post import SQL script {script_path} not found")
            return False
            
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix coordinator_monthly_summary table creation
        old_pattern = "coordinator_id INTEGER,"
        new_pattern = "coordinator_id TEXT,"
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("  Fixed post import SQL script")
            return True
        else:
            logger.info("  Post import SQL script already has correct coordinator_id type")
            return False
            
    except Exception as e:
        logger.error(f"  Error fixing post import SQL script: {e}")
        return False

def main():
    logger.info("Starting comprehensive coordinator schema fix...")
    
    # Fix existing database tables
    conn = get_db_connection()
    try:
        # Get all coordinator tables
        tables = get_coordinator_tables(conn)
        logger.info(f"Found {len(tables)} coordinator tables to check")
        
        fixed_count = 0
        for table in tables:
            if fix_table_schema(conn, table):
                fixed_count += 1
                
        conn.commit()
        logger.info(f"Fixed {fixed_count} tables")
        
    except Exception as e:
        logger.error(f"Error fixing database tables: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    # Fix transform script
    transform_fixed = fix_transform_script()
    
    # Fix post import SQL script
    sql_fixed = fix_post_import_sql()
    
    logger.info("============================================================")
    logger.info("COMPREHENSIVE FIX SUMMARY")
    logger.info("============================================================")
    logger.info(f"Database tables fixed: {fixed_count > 0}")
    logger.info(f"Transform script fixed: {transform_fixed}")
    logger.info(f"Post import SQL fixed: {sql_fixed}")
    logger.info("")
    logger.info("✅ Coordinator schema fix completed!")

if __name__ == "__main__":
    main()