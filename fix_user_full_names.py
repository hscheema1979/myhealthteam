#!/usr/bin/env python3
"""
Fix users missing full_name field by populating it from first_name and last_name
"""
import sqlite3

def fix_user_full_names():
    """Populate missing full_name fields in users table"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Check users without full_name
    cursor.execute("SELECT user_id, username, first_name, last_name, email, full_name FROM users WHERE full_name IS NULL OR full_name = ''")
    users_without_full_name = cursor.fetchall()
    
    print('Users without full_name:')
    for user in users_without_full_name:
        print(f'  ID: {user[0]}, Username: {user[1]}, First: {user[2]}, Last: {user[3]}, Email: {user[4]}, Full: {user[5]}')
    
    # Update users to populate full_name
    cursor.execute("UPDATE users SET full_name = first_name || ' ' || last_name WHERE full_name IS NULL OR full_name = ''")
    conn.commit()
    
    print(f'\nUpdated {cursor.rowcount} users to populate full_name field')
    
    # Verify the fix
    cursor.execute("SELECT user_id, username, first_name, last_name, email, full_name FROM users WHERE full_name IS NULL OR full_name = ''")
    remaining_users = cursor.fetchall()
    
    if remaining_users:
        print(f'\nStill {len(remaining_users)} users without full_name:')
        for user in remaining_users:
            print(f'  ID: {user[0]}, Username: {user[1]}, First: {user[2]}, Last: {user[3]}, Email: {user[4]}, Full: {user[5]}')
    else:
        print('\n✓ All users now have full_name populated!')
    
    # Show some sample users for verification
    cursor.execute("SELECT user_id, username, first_name, last_name, email, full_name FROM users LIMIT 5")
    sample_users = cursor.fetchall()
    
    print('\nSample users (first 5):')
    for user in sample_users:
        print(f'  ID: {user[0]}, Username: {user[1]}, Name: {user[5]} ({user[2]} {user[3]}), Email: {user[4]}')
    
    conn.close()

if __name__ == "__main__":
    fix_user_full_names()