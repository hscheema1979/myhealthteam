import sqlite3
import pandas as pd

db_path = 'sheets_data.db'

try:
    conn = sqlite3.connect(db_path)
    
    print("Checking staging_provider_tasks date range:")
    try:
        query = "SELECT MIN(task_date), MAX(task_date), COUNT(*) FROM staging_provider_tasks"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying staging_provider_tasks: {e}")

    print("\nChecking staging_coordinator_tasks date range:")
    try:
        query = "SELECT MIN(task_date), MAX(task_date), COUNT(*) FROM staging_coordinator_tasks"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying staging_coordinator_tasks: {e}")
        
    print("\nChecking staging_patients count:")
    try:
        query = "SELECT COUNT(*) FROM staging_patients"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying staging_patients: {e}")

    conn.close()

except Exception as e:
    print(f"Failed to connect to database: {e}")
