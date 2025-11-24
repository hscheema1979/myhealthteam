import sqlite3
import pandas as pd

db_path = 'scripts/sheets_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*80)
print("DIAGNOSING MISSING COORDINATOR DATA")
print("="*80)

# 1. Check max date in the main history table
print("\n1. Checking source_coordinator_tasks_history max date:")
try:
    cursor.execute('SELECT MAX("Date Only") FROM source_coordinator_tasks_history')
    print(f"   Max Date: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM source_coordinator_tasks_history')
    print(f"   Total Rows: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Check the monthly tables we imported
print("\n2. Checking SOURCE_CM_TASKS_2025_10:")
try:
    cursor.execute('SELECT COUNT(*) FROM SOURCE_CM_TASKS_2025_10')
    print(f"   Rows: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. Checking SOURCE_CM_TASKS_2025_11:")
try:
    cursor.execute('SELECT COUNT(*) FROM SOURCE_CM_TASKS_2025_11')
    print(f"   Rows: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"   Error: {e}")

# 3. FIX: Append data if needed
print("\n4. ATTEMPTING FIX: Appending monthly data to history table...")

# Get columns from history table to ensure matching
cursor.execute("PRAGMA table_info(source_coordinator_tasks_history)")
columns = [info[1] for info in cursor.fetchall()]
col_str = '", "'.join(columns)
col_str = f'"{col_str}"'

# Append Oct
try:
    print("   Appending October data...")
    sql = f'INSERT INTO source_coordinator_tasks_history ({col_str}) SELECT {col_str} FROM SOURCE_CM_TASKS_2025_10'
    cursor.execute(sql)
    print(f"   Inserted {cursor.rowcount} rows.")
except Exception as e:
    print(f"   Error appending October: {e}")

# Append Nov
try:
    print("   Appending November data...")
    sql = f'INSERT INTO source_coordinator_tasks_history ({col_str}) SELECT {col_str} FROM SOURCE_CM_TASKS_2025_11'
    cursor.execute(sql)
    print(f"   Inserted {cursor.rowcount} rows.")
except Exception as e:
    print(f"   Error appending November: {e}")

conn.commit()
print("\nFix applied. Data should now be in source_coordinator_tasks_history.")
conn.close()
