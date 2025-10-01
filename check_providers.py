import sys
sys.path.append('src')
import database

try:
    providers = database.get_users_by_role('CP')
    print('Available Care Providers:')
    if providers:
        for provider in providers:
            print(f'  - {provider["full_name"]} ({provider["username"]})')
    else:
        print('  No providers found with role CP')
        
    # Also check what roles exist
    conn = database.get_db_connection()
    roles = conn.execute('SELECT DISTINCT role FROM users WHERE role IS NOT NULL').fetchall()
    print('\nAll roles in database:')
    for role in roles:
        print(f'  - {role[0]}')
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()