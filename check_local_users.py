import sqlite3

def check_local_users():
    """Check local users table structure and content"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print('📋 Local users table structure:')
        for col in columns:
            print(f'   {col[1]} ({col[2]})')
        
        # Get current users count
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        print(f'\n📊 Current users: {user_count}')
        
        # Sample a few users
        cursor.execute('SELECT user_id, username, full_name FROM users LIMIT 10')
        users = cursor.fetchall()
        print('\n📝 Sample users:')
        for user in users:
            print(f'   ID: {user[0]}, Username: {user[1]}, Name: {user[2]}')
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    check_local_users()
