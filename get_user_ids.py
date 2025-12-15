#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()
cursor.execute("SELECT user_id, username, full_name FROM users WHERE username LIKE '%justin%' OR username LIKE '%harpreet%' OR full_name LIKE '%justin%' OR full_name LIKE '%harpreet%'")
users = cursor.fetchall()
for user in users:
    print(f'User ID: {user[0]}, Username: {user[1]}, Full Name: {user[2]}')
conn.close()