import sqlite3
import pandas as pd

db_path = 'sheets_data.db'

try:
    conn = sqlite3.connect(db_path)
    
    print("Checking staging_provider_tasks date range:")
    try:
        query = "SELECT MIN(activity_date), MAX(activity_date), COUNT(*) FROM staging_provider_tasks"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying staging_provider_tasks: {e}")

    print("\nChecking staging_coordinator_tasks date range:")
    try:
        query = "SELECT MIN(activity_date), MAX(activity_date), COUNT(*) FROM staging_coordinator_tasks"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying staging_coordinator_tasks: {e}")
        
    print("\nChecking SOURCE_PATIENT_DATA count:")
    try:
        query = "SELECT COUNT(*) FROM SOURCE_PATIENT_DATA"
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error querying SOURCE_PATIENT_DATA: {e}")

    conn.close()

except Exception as e:
    print(f"Failed to connect to database: {e}")
