import sqlite3

conn = sqlite3.connect('production.db')

# Check for coordinator monthly summary tables
tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%coordinator_monthly_summary%'").fetchall()]

print('Coordinator Monthly Summary Tables:')
for table in tables:
    print(f'  {table}')

# Check schema of first one if exists
if tables:
    first_table = tables[0]
    print(f'\nSchema of {first_table}:')
    schema = conn.execute(f'PRAGMA table_info({first_table})').fetchall()
    for row in schema:
        print(f'  {row[1]} ({row[2]})')

conn.close()