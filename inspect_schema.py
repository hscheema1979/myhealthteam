import sqlite3

db_path = 'sheets_data.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Tables in sheets_data.db:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
        
    print("\nSchema for staging_provider_tasks:")
    try:
        cursor.execute("PRAGMA table_info(staging_provider_tasks)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error: {e}")

    print("\nSchema for staging_coordinator_tasks:")
    try:
        cursor.execute("PRAGMA table_info(staging_coordinator_tasks)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error: {e}")

    conn.close()

except Exception as e:
    print(f"Failed to connect to database: {e}")
