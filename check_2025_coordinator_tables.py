import sqlite3

def check_all_2025_coordinator_tables():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    # Filter for coordinator_tasks_2025_MM pattern
    coordinator_2025_tables = [table for table in all_tables if 'coordinator_tasks_2025_' in table and not table.startswith('source_')]
    coordinator_2025_tables.sort()
    
    print("=== ALL COORDINATOR_TASKS_2025_MM TABLES ===")
    total_rows = 0
    
    expected_months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    found_months = []
    
    for table in coordinator_2025_tables:
        print(f"\nTable: {table}")
        
        # Extract month from table name
        if '_2025_' in table:
            month = table.split('_2025_')[1]
            found_months.append(month)
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_rows += count
        print(f"Row count: {count}")
        
        # Get date range
        cursor.execute(f"SELECT MIN(task_date), MAX(task_date) FROM {table}")
        date_range = cursor.fetchone()
        print(f"Date range: {date_range[0]} to {date_range[1]}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total 2025 coordinator tables found: {len(coordinator_2025_tables)}")
    print(f"Total rows across all 2025 tables: {total_rows}")
    
    print(f"\nMonths found: {sorted(found_months)}")
    missing_months = [month for month in expected_months if month not in found_months]
    print(f"Missing months: {missing_months}")
    
    # Also check for any source tables that might contain the missing months
    print(f"\n=== SOURCE TABLES FOR MISSING MONTHS ===")
    source_tables = [table for table in all_tables if table.startswith('source_coordinator_tasks_2025_')]
    source_tables.sort()
    
    for table in source_tables:
        if '_2025_' in table:
            month = table.split('_2025_')[1]
            if month in missing_months:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"Found source table: {table} with {count} rows")
    
    conn.close()

if __name__ == "__main__":
    check_all_2025_coordinator_tables()