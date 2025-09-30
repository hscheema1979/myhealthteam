import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection

def check_schema():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all workflow-related tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%workflow%'")
        tables = cursor.fetchall()
        
        print('Workflow-related tables:')
        for table in tables:
            table_name = table[0]
            print(f'\n  Table: {table_name}')
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()
            for col in columns:
                print(f'    {col[1]} ({col[2]})')
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()