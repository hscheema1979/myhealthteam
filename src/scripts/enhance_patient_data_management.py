#!/usr/bin/env python3
"""
Enhanced Patient Data Management Script
Purpose: Update patient metrics and copy patient status to notes columns
Tables: provider_tasks and ALL provider_tasks_YYYY_MM tables
Author: System Enhancement
Date: 2025-01-27
"""

import sqlite3
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the src directory to the path to import database module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def get_database_connection(db_path: str = "production.db") -> sqlite3.Connection:
    """Get database connection with proper configuration."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def get_provider_tables(conn: sqlite3.Connection) -> List[str]:
    """Get all provider_tasks tables including monthly partitions."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type = 'table' 
        AND (name = 'provider_tasks' OR name LIKE 'provider_tasks_____%%')
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]

def create_audit_table(conn: sqlite3.Connection) -> None:
    """Create audit log table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_data_audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            old_notes TEXT,
            new_notes TEXT,
            visit_completion_status TEXT,
            updated_by TEXT DEFAULT 'SYSTEM_ENHANCEMENT',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def generate_update_sql(table_name: str) -> str:
    """Generate UPDATE SQL for a specific provider_tasks table."""
    return f"""
    UPDATE {table_name} 
    SET 
        status = CASE 
            -- Update status based on visit completion patterns
            WHEN task_description LIKE '%PCP-Visit%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'PCP_VISIT_COMPLETED'
            WHEN task_description LIKE '%Telehealth%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'TELEHEALTH_COMPLETED'
            WHEN task_description LIKE '%Home%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'HOME_VISIT_COMPLETED'
            WHEN task_description LIKE '%Follow%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'FOLLOWUP_COMPLETED'
            WHEN task_description LIKE '%NEW%' AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'INITIAL_VISIT_COMPLETED'
            WHEN (task_description LIKE '%Graft%' OR task_description LIKE '%WC-%') AND (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SPECIALTY_CARE_COMPLETED'
            WHEN (status IS NULL OR status IN ('', 'N', '#REF!')) THEN 'SERVICE_COMPLETED'
            ELSE status -- Keep existing status if it's already meaningful
        END,
        notes = CASE 
            -- Append patient status to existing notes, avoiding duplicates
            WHEN notes IS NULL OR notes = '' THEN 
                'Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = {table_name}.patient_id), 'Unknown') ||
                ' | Updated: ' || datetime('now')
            WHEN notes NOT LIKE '%Patient Status:%' THEN 
                notes || ' | Patient Status: ' || COALESCE((SELECT p.status FROM patients p WHERE p.patient_id = {table_name}.patient_id), 'Unknown') ||
                ' | Updated: ' || datetime('now')
            ELSE notes -- Don't update if patient status already exists in notes
        END,
        updated_date = strftime('%s', 'now')
    WHERE 
        -- Only update records that need updating
        (status IS NULL OR status IN ('', 'N', '#REF!')) OR 
        (notes IS NULL OR notes = '' OR notes NOT LIKE '%Patient Status:%')
    """

def update_table(conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
    """Update a specific provider_tasks table and return statistics."""
    cursor = conn.cursor()
    
    # Get before statistics
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN status IS NULL OR status IN ('', 'N', '#REF!') THEN 1 END) as null_status_before,
            COUNT(CASE WHEN notes IS NULL OR notes = '' OR notes NOT LIKE '%Patient Status:%' THEN 1 END) as needs_notes_before
        FROM {table_name}
    """)
    before_stats = cursor.fetchone()
    
    # Execute update
    update_sql = generate_update_sql(table_name)
    cursor.execute(update_sql)
    rows_affected = cursor.rowcount
    
    # Get after statistics
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN status LIKE '%_COMPLETED' THEN 1 END) as updated_status_records,
            COUNT(CASE WHEN notes LIKE '%Patient Status:%' THEN 1 END) as updated_notes_records,
            COUNT(CASE WHEN status IS NULL OR status IN ('', 'N', '#REF!') THEN 1 END) as remaining_null_status
        FROM {table_name}
    """)
    after_stats = cursor.fetchone()
    
    return {
        'table_name': table_name,
        'rows_affected': rows_affected,
        'total_records': after_stats[0],
        'null_status_before': before_stats[1],
        'needs_notes_before': before_stats[2],
        'updated_status_records': after_stats[1],
        'updated_notes_records': after_stats[2],
        'remaining_null_status': after_stats[3]
    }

def create_audit_entries(conn: sqlite3.Connection, table_name: str) -> None:
    """Create audit log entries for the updated table."""
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO patient_data_audit_log (table_name, patient_id, operation_type, visit_completion_status)
        SELECT 
            '{table_name}' as table_name,
            patient_id,
            'BULK_UPDATE_METRICS_AND_NOTES' as operation_type,
            CASE 
                WHEN task_description LIKE '%PCP-Visit%' THEN 'PCP_VISIT_COMPLETED'
                WHEN task_description LIKE '%Telehealth%' THEN 'TELEHEALTH_COMPLETED'
                WHEN task_description LIKE '%Home%' THEN 'HOME_VISIT_COMPLETED'
                WHEN task_description LIKE '%Follow%' THEN 'FOLLOWUP_COMPLETED'
                WHEN task_description LIKE '%NEW%' THEN 'INITIAL_VISIT_COMPLETED'
                ELSE 'OTHER_SERVICE_COMPLETED'
            END as visit_completion_status
        FROM {table_name} 
        WHERE updated_date = strftime('%s', 'now')
    """)

def create_performance_indexes(conn: sqlite3.Connection, table_name: str) -> None:
    """Create performance indexes for the table."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_patient_id ON {table_name}(patient_id)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_updated_date ON {table_name}(updated_date)")
    except sqlite3.Error as e:
        print(f"Warning: Could not create indexes for {table_name}: {e}")

def check_data_integrity(conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
    """Check data integrity for orphaned patient IDs."""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(DISTINCT pt.patient_id) as orphaned_count
        FROM {table_name} pt
        LEFT JOIN patients p ON pt.patient_id = p.patient_id
        WHERE p.patient_id IS NULL AND pt.patient_id IS NOT NULL AND pt.patient_id != ''
    """)
    orphaned_count = cursor.fetchone()[0]
    
    return {
        'table_name': table_name,
        'orphaned_patient_ids': orphaned_count
    }

def display_sample_records(conn: sqlite3.Connection, table_name: str, limit: int = 3) -> None:
    """Display sample updated records from the table."""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT 
            patient_id,
            status,
            substr(notes, 1, 60) || '...' as notes_preview,
            substr(task_description, 1, 40) || '...' as task_preview
        FROM {table_name} 
        WHERE notes LIKE '%Patient Status:%' 
        LIMIT {limit}
    """)
    
    records = cursor.fetchall()
    if records:
        print(f"\\nSample updated records from {table_name}:")
        for record in records:
            print(f"  Patient: {record[0]}, Status: {record[1]}")
            print(f"  Notes: {record[2]}")
            print(f"  Task: {record[3]}")
            print()

def main():
    """Main execution function."""
    print("Enhanced Patient Data Management Script")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")
    
    try:
        # Connect to database
        conn = get_database_connection()
        print("✓ Connected to production database")
        
        # Create audit table
        create_audit_table(conn)
        print("✓ Audit table ready")
        
        # Get all provider_tasks tables
        tables = get_provider_tables(conn)
        print(f"✓ Found {len(tables)} provider_tasks tables to update")
        
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        all_stats = []
        integrity_issues = []
        
        # Update each table
        for table_name in tables:
            print(f"\\nProcessing {table_name}...")
            
            try:
                # Update the table
                stats = update_table(conn, table_name)
                all_stats.append(stats)
                
                # Create audit entries
                create_audit_entries(conn, table_name)
                
                # Create performance indexes
                create_performance_indexes(conn, table_name)
                
                # Check data integrity
                integrity = check_data_integrity(conn, table_name)
                if integrity['orphaned_patient_ids'] > 0:
                    integrity_issues.append(integrity)
                
                print(f"  ✓ Updated {stats['rows_affected']} rows")
                print(f"  ✓ Status updates: {stats['updated_status_records']}")
                print(f"  ✓ Notes updates: {stats['updated_notes_records']}")
                
            except sqlite3.Error as e:
                print(f"  ✗ Error updating {table_name}: {e}")
                continue
        
        # Commit transaction
        conn.commit()
        print("\\n✓ All updates committed successfully")
        
        # Display comprehensive summary
        print("\\n" + "=" * 50)
        print("COMPREHENSIVE UPDATE SUMMARY")
        print("=" * 50)
        
        total_rows_affected = sum(stat['rows_affected'] for stat in all_stats)
        total_status_updates = sum(stat['updated_status_records'] for stat in all_stats)
        total_notes_updates = sum(stat['updated_notes_records'] for stat in all_stats)
        
        print(f"Total tables processed: {len(all_stats)}")
        print(f"Total rows affected: {total_rows_affected}")
        print(f"Total status updates: {total_status_updates}")
        print(f"Total notes updates: {total_notes_updates}")
        
        # Display detailed stats
        print("\\nDetailed Statistics by Table:")
        print("-" * 80)
        print(f"{'Table Name':<25} {'Rows Affected':<15} {'Status Updates':<15} {'Notes Updates':<15}")
        print("-" * 80)
        
        for stat in all_stats:
            print(f"{stat['table_name']:<25} {stat['rows_affected']:<15} {stat['updated_status_records']:<15} {stat['updated_notes_records']:<15}")
        
        # Display integrity issues
        if integrity_issues:
            print("\\n⚠️  DATA INTEGRITY WARNINGS:")
            for issue in integrity_issues:
                print(f"  {issue['table_name']}: {issue['orphaned_patient_ids']} orphaned patient IDs")
        else:
            print("\\n✓ No data integrity issues found")
        
        # Display sample records
        print("\\n" + "=" * 50)
        print("SAMPLE UPDATED RECORDS")
        print("=" * 50)
        
        # Show samples from main table and a few monthly tables
        sample_tables = ['provider_tasks', 'provider_tasks_2025_09', 'provider_tasks_2024_12']
        for table_name in sample_tables:
            if table_name in [stat['table_name'] for stat in all_stats]:
                display_sample_records(conn, table_name)
        
        print(f"\\nCompleted at: {datetime.now()}")
        print("✓ Enhanced Patient Data Management completed successfully!")
        
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()