import sqlite3

conn = sqlite3.connect('production.db')
try:
    # Get coordinator task tables
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%coordinator_tasks%'").fetchall()]
    print('Coordinator task tables:', tables)
    
    if tables:
        # Check schema of first table
        table_name = tables[0]
        print(f'\nSchema for {table_name}:')
        columns = [desc[0] for desc in conn.execute(f'PRAGMA table_info({table_name})').fetchall()]
        print('Columns:', columns)
        
        # Check if coordinator_tasks_2025_09 exists specifically
        if 'coordinator_tasks_2025_09' in tables:
            print('\ncoordinator_tasks_2025_09 columns:')
            columns_2025_09 = [desc[0] for desc in conn.execute('PRAGMA table_info(coordinator_tasks_2025_09)').fetchall()]
            print('Columns:', columns_2025_09)
finally:
    conn.close()