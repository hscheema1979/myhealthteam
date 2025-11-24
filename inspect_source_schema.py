import sqlite3

db_path = 'sheets_data.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Schema for source_coordinator_tasks_history:")
    try:
        cursor.execute("PRAGMA table_info(source_coordinator_tasks_history)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error: {e}")

    conn.close()

except Exception as e:
    print(f"Failed to connect to database: {e}")
