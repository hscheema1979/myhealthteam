import sqlite3
from datetime import datetime

conn = sqlite3.connect('production.db')
try:
    query = 'SELECT pay_week_start_date FROM provider_weekly_payroll_status WHERE pay_week_start_date IS NOT NULL LIMIT 5'
    rows = conn.execute(query).fetchall()
    print('Sample pay_week_start_date values:')
    for i, row in enumerate(rows):
        print(f'Row {i}: {row[0]} - Type: {type(row[0]).__name__}')
        if row[0]:
            try:
                if isinstance(row[0], str):
                    # Try to parse as string
                    date_obj = datetime.strptime(row[0], '%Y-%m-%d')
                    display = date_obj.strftime('%B %Y')
                else:
                    # Assume it's already a datetime or similar
                    display = row[0].strftime('%B %Y') if hasattr(row[0], 'strftime') else str(row[0])
                print(f'  Formatted display: {display}')
            except Exception as e:
                print(f'  Error formatting date: {e}')
    
    print('\nTesting the original query that returns None:')
    query = '''
    SELECT DISTINCT
        pay_year,
        strftime('%m', pay_week_start_date) as month,
        strftime('%Y-%m', pay_week_start_date) as year_month,
        strftime('%B %Y', pay_week_start_date) as display
    FROM provider_weekly_payroll_status
    WHERE pay_week_start_date IS NOT NULL
    ORDER BY year_month DESC
    LIMIT 3
    '''
    rows = conn.execute(query).fetchall()
    for i, row in enumerate(rows):
        print(f'Row {i}: {row} - Types: {[type(x).__name__ for x in row]}')

except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
