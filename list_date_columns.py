import sqlite3

conn = sqlite3.connect('production.db')

# Get all tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()

date_columns = {}

for table in tables:
    table_name = table[0]
    # Get column info
    columns = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    
    date_cols = []
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        # Look for date-related columns
        if 'date' in col_name.lower() or 'DATE' in col_type or 'TIMESTAMP' in col_type:
            date_cols.append((col_name, col_type))
    
    if date_cols:
        date_columns[table_name] = date_cols

print('='*80)
print('ALL DATE COLUMNS IN DATABASE')
print('='*80)

for table_name in sorted(date_columns.keys()):
    print(f'\n{table_name}:')
    for col_name, col_type in date_columns[table_name]:
        print(f'  - {col_name:30} ({col_type})')

print('\n' + '='*80)
print(f'SUMMARY: {len(date_columns)} tables with date columns')
print('='*80)

conn.close()
