import sqlite3
import pandas as pd

conn = sqlite3.connect('production.db')

print('=== SEPTEMBER 2025 DATA ANALYSIS ===')

# Check if we have September data in provider_tasks
query = '''
SELECT 
    strftime('%Y-%m', task_date) as month,
    COUNT(*) as task_count,
    COUNT(DISTINCT provider_name) as provider_count,
    GROUP_CONCAT(DISTINCT provider_name) as providers
FROM provider_tasks
WHERE strftime('%Y-%m', task_date) = '2025-09'
GROUP BY strftime('%Y-%m', task_date)
'''
df = pd.read_sql_query(query, conn)
print('September 2025 in provider_tasks:')
print(df.to_string(index=False))

# Check monthly provider_tasks tables for September
print('\n=== CHECKING MONTHLY TABLES FOR SEPTEMBER ===')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%2025_09%' ORDER BY name")
sept_tables = cursor.fetchall()

for table in sept_tables:
    table_name = table[0]
    print(f'\n--- {table_name} ---')
    try:
        query = f'''
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT provider_name) as unique_providers,
            GROUP_CONCAT(DISTINCT provider_name) as providers
        FROM {table_name}
        WHERE provider_name IS NOT NULL
        '''
        df = pd.read_sql_query(query, conn)
        print(df.to_string(index=False))
        
        # Show sample data
        query = f'''
        SELECT provider_name, COUNT(*) as count
        FROM {table_name}
        WHERE provider_name IS NOT NULL
        GROUP BY provider_name
        ORDER BY count DESC
        '''
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            print('Provider breakdown:')
            print(df.to_string(index=False))
        
    except Exception as e:
        print(f'Error: {e}')

# Check if September data exists in source tables
print('\n=== CHECKING SOURCE TABLES FOR SEPTEMBER ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'source%2025_09%' ORDER BY name")
source_sept_tables = cursor.fetchall()

for table in source_sept_tables:
    table_name = table[0]
    print(f'\n--- {table_name} ---')
    try:
        query = f'SELECT COUNT(*) as count FROM {table_name}'
        df = pd.read_sql_query(query, conn)
        print(f'Records: {df.iloc[0][0]}')
    except Exception as e:
        print(f'Error: {e}')

# Check the latest data in provider_tasks
print('\n=== LATEST DATA IN PROVIDER_TASKS ===')
query = '''
SELECT 
    MAX(task_date) as latest_date,
    strftime('%Y-%m', MAX(task_date)) as latest_month
FROM provider_tasks
'''
df = pd.read_sql_query(query, conn)
print('Latest data:')
print(df.to_string(index=False))

# Check recent months data
print('\n=== RECENT MONTHS DATA ===')
query = '''
SELECT 
    strftime('%Y-%m', task_date) as month,
    COUNT(*) as task_count,
    COUNT(DISTINCT provider_name) as provider_count
FROM provider_tasks
WHERE task_date >= date('now', '-3 months')
GROUP BY strftime('%Y-%m', task_date)
ORDER BY month DESC
'''
df = pd.read_sql_query(query, conn)
print('Last 3 months:')
print(df.to_string(index=False))

conn.close()