#!/usr/bin/env python3
"""
Fix inconsistent usernames and ensure proper login ID format
"""
import sqlite3
import re

def clean_username(full_name, email):
    """Generate a consistent username from full name and email"""
    # If we have a proper full name, use it to create username
    if full_name and len(full_name.split()) >= 2:
        # Take first name and last name
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0].lower()
            last_name = name_parts[-1].lower()
            # Remove any special characters and spaces
            first_clean = re.sub(r'[^a-zA-Z0-9]', '', first_name)
            last_clean = re.sub(r'[^a-zA-Z0-9]', '', last_name)
            return f"{first_clean}.{last_clean}"
    
    # If we have an email, try to extract username from it
    if email and '@' in email:
        username_from_email = email.split('@')[0]
        # Clean it up
        username_clean = re.sub(r'[^a-zA-Z0-9_]', '_', username_from_email)
        return username_clean
    
    # Fallback to generic pattern
    return "user"

def fix_usernames():
    """Fix inconsistent usernames in the database"""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute('SELECT user_id, username, full_name, email FROM users')
    users = cursor.fetchall()
    
    print("Current username issues:")
    needs_update = []
    
    for user_id, username, full_name, email in users:
        issues = []
        
        # Check if username is an email address
        if '@' in username:
            issues.append("username_is_email")
        
        # Check if username has special characters or underscores that should be periods
        if '_' in username or len(username) > 15:
            issues.append("inconsistent_format")
        
        # Check if username is too short or unclear
        if len(username) < 4:
            issues.append("too_short")
        
        if issues:
            proposed_username = clean_username(full_name, email)
            needs_update.append((user_id, username, proposed_username, issues, full_name, email))
            print(f"  ID: {user_id}, Current: '{username}', Proposed: '{proposed_username}', Issues: {', '.join(issues)}")
    
    if needs_update:
        print(f"\nFound {len(needs_update)} users with username issues. Updating...")
        
        for user_id, current_username, new_username, issues, full_name, email in needs_update:
            cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (new_username, user_id))
            print(f"  Updated ID {user_id}: '{current_username}' -> '{new_username}'")
        
        conn.commit()
        print(f"✅ Updated {len(needs_update)} usernames")
    else:
        print("✅ All usernames look consistent!")
    
    # Show final results
    cursor.execute('SELECT user_id, username, full_name, email FROM users ORDER BY user_id LIMIT 10')
    final_users = cursor.fetchall()
    
    print("\nUpdated user list (first 10):")
    for user_id, username, full_name, email in final_users:
        print(f"  ID: {user_id}, Username: '{username}', Name: {full_name}, Email: {email}")
    
    conn.close()

if __name__ == "__main__":
    fix_usernames()