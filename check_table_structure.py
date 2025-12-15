import sqlite3

def main():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Check provider_tasks_2025_11
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provider_tasks_2025_11'")
    tables = cursor.fetchall()
    if tables:
        table_name = tables[0][0]
        print(f"Table {table_name} exists.")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check a few rows
        cursor.execute(f"SELECT provider_task_id, task_date FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        print("\nSample rows (provider_task_id, task_date):")
        for row in rows:
            print(f"  {row}")
    else:
        print("provider_tasks_2025_11 does not exist")
    
    conn.close()

if __name__ == '__main__':
    main()