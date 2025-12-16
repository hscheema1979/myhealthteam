import sqlite3

def main():
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        if tables:
            print('Total tables:', len(tables))
            for t in tables:
                print('  -', t[0])
        else:
            print('No tables found')
        
        # Check for provider_tasks tables specifically
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks%'")
        provider_tables = cursor.fetchall()
        print('\nProvider tasks tables:')
        for t in provider_tables:
            print('  -', t[0])
            
        conn.close()
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    main()