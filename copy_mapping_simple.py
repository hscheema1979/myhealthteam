#!/usr/bin/env python3
import sqlite3

# Copy staff_code_mapping data from backup to production
backup = sqlite3.connect('production_backup_prototype_test.db')
prod = sqlite3.connect('production.db')

# Get all mappings from backup
cursor = backup.execute('SELECT * FROM staff_code_mapping')
mappings = cursor.fetchall()

# Clear existing data in production
prod.execute('DELETE FROM staff_code_mapping')

# Insert each mapping
for mapping in mappings:
    prod.execute('INSERT INTO staff_code_mapping VALUES (?, ?, ?, ?, ?, ?)', mapping)

prod.commit()
print(f"Copied {len(mappings)} staff code mappings")

# Show what we copied
cursor = prod.execute('SELECT staff_code, user_id, mapping_type FROM staff_code_mapping ORDER BY staff_code')
for row in cursor:
    print(f"{row[0]} -> User ID {row[1]} ({row[2]})")

backup.close()
prod.close()