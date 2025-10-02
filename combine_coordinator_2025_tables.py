import sqlite3
from datetime import datetime

def analyze_schemas():
    """Analyze the different schemas in 2025 tables"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get current coordinator_tasks schema
    cursor.execute("PRAGMA table_info(coordinator_tasks)")
    main_schema = cursor.fetchall()
    print("=== CURRENT COORDINATOR_TASKS SCHEMA ===")
    for col in main_schema:
        print(f"  {col[1]} ({col[2]})")
    
    # Get all 2025 tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_tasks_2025_%' AND name NOT LIKE 'source_%'")
    tables_2025 = [row[0] for row in cursor.fetchall()]
    tables_2025.sort()
    
    # Group tables by schema type
    schema_groups = {}
    
    for table in tables_2025:
        cursor.execute(f"PRAGMA table_info({table})")
        table_schema = cursor.fetchall()
        
        # Create schema signature
        schema_sig = tuple(sorted([(col[1], col[2]) for col in table_schema]))
        
        if schema_sig not in schema_groups:
            schema_groups[schema_sig] = []
        schema_groups[schema_sig].append(table)
    
    print(f"\n=== FOUND {len(schema_groups)} DIFFERENT SCHEMAS ===")
    
    for i, (schema_sig, tables) in enumerate(schema_groups.items(), 1):
        print(f"\nSchema Type {i}: {tables}")
        for col_name, col_type in sorted(schema_sig):
            print(f"  {col_name} ({col_type})")
    
    conn.close()
    return schema_groups, tables_2025

def backup_existing_table():
    """Backup the existing coordinator_tasks table"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_table = f"coordinator_tasks_backup_{timestamp}"
    
    print(f"=== BACKING UP EXISTING TABLE AS {backup_table} ===")
    
    # Create backup table
    cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM coordinator_tasks")
    
    # Verify backup
    cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
    backup_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM coordinator_tasks")
    original_count = cursor.fetchone()[0]
    
    print(f"Original table rows: {original_count}")
    print(f"Backup table rows: {backup_count}")
    
    if backup_count == original_count:
        print("✅ Backup successful")
        conn.commit()
        conn.close()
        return backup_table
    else:
        print("❌ Backup failed - row counts don't match")
        conn.close()
        return None

def combine_2025_tables_with_mapping(tables_2025):
    """Combine all 2025 tables with proper schema mapping"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("=== COMBINING 2025 TABLES WITH SCHEMA MAPPING ===")
    
    # Drop existing coordinator_tasks table
    cursor.execute("DROP TABLE IF EXISTS coordinator_tasks")
    
    # Create new coordinator_tasks table with the target schema
    # Using the schema from the main table but adapting for 2025 data
    cursor.execute("""
        CREATE TABLE coordinator_tasks (
            coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            patient_id TEXT,
            coordinator_id TEXT,
            task_date TEXT,
            duration_minutes INTEGER,
            task_type TEXT,
            notes TEXT
        )
    """)
    
    total_rows = 0
    
    for table in tables_2025:
        # Check what schema this table has
        cursor.execute(f"PRAGMA table_info({table})")
        table_schema = cursor.fetchall()
        table_cols = [col[1] for col in table_schema]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        table_count = cursor.fetchone()[0]
        
        if table_count == 0:
            print(f"Skipping empty table {table}")
            continue
        
        print(f"Processing {table} with {table_count} rows")
        
        # Map columns based on what's available
        if 'source_system' in table_cols and 'imported_at' in table_cols:
            # This is the newer format (Jan-Sep 2025)
            cursor.execute(f"""
                INSERT INTO coordinator_tasks (
                    task_id, patient_id, coordinator_id, task_date, 
                    duration_minutes, task_type, notes
                )
                SELECT 
                    NULL as task_id,
                    patient_id,
                    coordinator_id,
                    task_date,
                    duration_minutes,
                    task_type,
                    notes
                FROM {table}
            """)
        else:
            # This is the older format (Oct-Dec 2025, empty but with different schema)
            cursor.execute(f"""
                INSERT INTO coordinator_tasks (
                    task_id, patient_id, coordinator_id, task_date, 
                    duration_minutes, task_type, notes
                )
                SELECT 
                    task_id,
                    patient_id,
                    coordinator_id,
                    task_date,
                    duration_minutes,
                    task_type,
                    notes
                FROM {table}
            """)
        
        total_rows += table_count
        print(f"  ✅ Added {table_count} rows")
    
    # Verify final count
    cursor.execute("SELECT COUNT(*) FROM coordinator_tasks")
    final_count = cursor.fetchone()[0]
    
    print(f"\nTotal rows expected: {total_rows}")
    print(f"Total rows in new table: {final_count}")
    
    if total_rows == final_count:
        print("✅ Combination successful")
        conn.commit()
        conn.close()
        return True
    else:
        print("❌ Combination failed - row counts don't match")
        conn.close()
        return False

def verify_data_integrity():
    """Verify the combined data"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("=== VERIFYING DATA INTEGRITY ===")
    
    # Check total count
    cursor.execute("SELECT COUNT(*) FROM coordinator_tasks")
    total_count = cursor.fetchone()[0]
    print(f"Total rows in coordinator_tasks: {total_count}")
    
    # Check date range
    cursor.execute("SELECT MIN(task_date), MAX(task_date) FROM coordinator_tasks")
    date_range = cursor.fetchone()
    print(f"Date range: {date_range[0]} to {date_range[1]}")
    
    # Check by month
    cursor.execute("""
        SELECT substr(task_date, 1, 7) as month, COUNT(*) as count 
        FROM coordinator_tasks 
        GROUP BY substr(task_date, 1, 7) 
        ORDER BY month
    """)
    monthly_counts = cursor.fetchall()
    
    print("\nMonthly breakdown:")
    for month, count in monthly_counts:
        print(f"  {month}: {count} rows")
    
    # Check schema of final table
    cursor.execute("PRAGMA table_info(coordinator_tasks)")
    final_schema = cursor.fetchall()
    print("\nFinal table schema:")
    for col in final_schema:
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()

def main():
    print("COORDINATOR TASKS 2025 COMBINATION SCRIPT")
    print("=" * 50)
    
    # Step 1: Analyze schemas
    schema_groups, tables_2025 = analyze_schemas()
    
    # Step 2: Backup existing table
    backup_table = backup_existing_table()
    if not backup_table:
        print("\n❌ BACKUP FAILED - ABORTING")
        return
    
    # Step 3: Combine tables with mapping
    success = combine_2025_tables_with_mapping(tables_2025)
    if not success:
        print("\n❌ COMBINATION FAILED")
        return
    
    # Step 4: Verify data
    verify_data_integrity()
    
    print(f"\n✅ SUCCESS! Combined all 2025 coordinator tables")
    print(f"Backup saved as: {backup_table}")
    print("Monthly tables coordinator_tasks_2025_MM preserved as requested")

if __name__ == "__main__":
    main()