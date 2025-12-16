import sqlite3

def main():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get all provider_tasks tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%' ORDER BY name")
    tables = cursor.fetchall()
    
    for table in tables[:3]:  # Check first 3 tables
        table_name = table[0]
        print(f"\n{table_name}:")
        cursor.execute(f"SELECT provider_task_id, task_date FROM {table_name} ORDER BY provider_task_id LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  ID: {row[0]}, Date: {row[1]}")
    
    conn.close()

if __name__ == '__main__':
    main()