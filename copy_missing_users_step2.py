#!/usr/bin/env python3
import sqlite3

print("STEP 2: Copying missing users (Dianela and Hector) from backup to production...")

# Connect to databases
backup = sqlite3.connect('production_backup_prototype_test.db')
prod = sqlite3.connect('production.db')

# Get missing users (Dianela and Hector)
cursor = backup.execute('SELECT * FROM users WHERE user_id IN (13, 14)')
missing_users = cursor.fetchall()

print(f"Found {len(missing_users)} missing users:")
for user in missing_users:
    print(f"  User ID {user[0]}: {user[2]} ({user[4]} {user[3]})")

# Insert missing users (skip if already exists)
for user in missing_users:
    try:
        prod.execute('''
            INSERT INTO users (user_id, username, password, first_name, last_name, full_name, email, phone, status, role_id, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', user)
        print(f"SUCCESS: Added user {user[2]}")
    except sqlite3.IntegrityError:
        print(f"WARNING: User {user[2]} already exists, skipping")

# Also copy their roles
cursor = backup.execute('''
    SELECT ur.* FROM user_roles ur
    JOIN users u ON ur.user_id = u.user_id
    WHERE u.user_id IN (13, 14)
''')
missing_roles = cursor.fetchall()

for role in missing_roles:
    try:
        prod.execute('''
            INSERT INTO user_roles (user_id, role_id, assigned_date)
            VALUES (?, ?, ?)
        ''', role)
        print(f"SUCCESS: Added role for User ID {role[0]}")
    except sqlite3.IntegrityError:
        print(f"WARNING: Role already exists for User ID {role[0]}, skipping")

prod.commit()

# Verify the restoration
print("\nVERIFICATION:")
cursor = prod.execute('SELECT user_id, full_name, username FROM users WHERE user_id IN (13, 14)')
restored_users = cursor.fetchall()
print(f"Restored users: {len(restored_users)}")
for user in restored_users:
    print(f"  User ID {user[0]}: {user[1]} ({user[2]})")

backup.close()
prod.close()

print("\nSTEP 2 COMPLETE: Missing users restored!")