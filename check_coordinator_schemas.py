import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Get all table names with coordinator
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%coordinator%' ORDER BY name")
tables = cursor.fetchall()

print('=== COORDINATOR-RELATED TABLES ===')
for table in tables:
    print(table[0])

print('\n=== CURRENT COORDINATOR_TASKS SCHEMA ===')
cursor.execute('PRAGMA table_info(coordinator_tasks)')
current_schema = cursor.fetchall()
for col in current_schema:
    print(f'{col[1]} ({col[2]})')

print('\n=== CURRENT COORDINATOR_TASKS ROW COUNT ===')
cursor.execute('SELECT COUNT(*) FROM coordinator_tasks')
current_count = cursor.fetchone()[0]
print(f'Current coordinator_tasks: {current_count} rows')

# Check for 2025 tables
for table in tables:
    table_name = table[0]
    if '2025' in table_name and 'coordinator' in table_name:
        print(f'\n=== {table_name.upper()} SCHEMA ===')
        cursor.execute(f'PRAGMA table_info({table_name})')
        schema = cursor.fetchall()
        for col in schema:
            print(f'{col[1]} ({col[2]})')
        
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        count = cursor.fetchone()[0]
        print(f'{table_name}: {count} rows')
        
        # Show sample data
        print(f'\n=== {table_name.upper()} SAMPLE DATA ===')
        cursor.execute(f'SELECT * FROM {table_name} LIMIT 3')
        rows = cursor.fetchall()
        for row in rows:
            print(row)

conn.close()