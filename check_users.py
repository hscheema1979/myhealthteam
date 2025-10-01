import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection

def check_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, email, first_name, last_name FROM users LIMIT 10')
        users = cursor.fetchall()
        
        print('Available users:')
        for user in users:
            print(f'  ID: {user[0]} | Email: {user[1]} | Name: {user[2]} {user[3]}')
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()