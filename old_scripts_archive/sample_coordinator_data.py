import sqlite3
import pandas as pd

db_path = 'sheets_data.db'

try:
    conn = sqlite3.connect(db_path)
    
    print("Sample from staging_coordinator_tasks:")
    try:
        query = "SELECT * FROM staging_coordinator_tasks LIMIT 10"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying staging_coordinator_tasks: {e}")

    print("\nSample from source_coordinator_tasks_history:")
    try:
        query = "SELECT * FROM source_coordinator_tasks_history LIMIT 10"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying source_coordinator_tasks_history: {e}")

    conn.close()

except Exception as e:
    print(f"Failed to connect to database: {e}")
