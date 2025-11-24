#!/usr/bin/env python3
"""
Create and populate staff_codes mapping table in production.db
This provides a centralized source for all staff identification codes.
"""

import sqlite3
import os

def create_staff_codes_table():
    """Create the staff_codes table and populate with current staff data"""

    # Path to production database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'production.db')

    if not os.path.exists(db_path):
        print(f"❌ Production database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop table if exists (for clean re-creation)
    cursor.execute("DROP TABLE IF EXISTS staff_codes")

    # Create staff_codes table
    cursor.execute("""
        CREATE TABLE staff_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            coordinator_code TEXT NOT NULL,
            provider_code TEXT NOT NULL,
            alt_provider_code TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Staff data from STAFF_CODE_REFERENCE.md (as of Nov 2025)
    staff_data = [
        ('Ethel Antonio', 'ethel@myhealthteam.org', 'ANTET000', 'Antonio, Ethel', 'Antonio, Ethel'),
        ('Harpreet Cheema', 'harpreet@myhealthteam.org', 'CHEHA000', 'Cheema, Harpreet', 'Cheema, Harpreet'),
        ('Eden Dabalus', 'eden@myhealthteam.org', 'DABED000', 'Dabalus, Eden', 'Dabalus, Eden'),
        ('Genevieve Davis', 'genevieve@myhealthteam.org', 'DAVGE000', 'Davis, Genevieve', 'Davis, Genevieve'),
        ('Albert Diaz', 'albert@myhealthteam.org', 'DIAAL000', 'Diaz, Albert', 'Diaz, Albert'),
        ('Jan Estomo', 'jan@myhealthteam.org', 'ESTJA000', 'Estomo, Jan', 'Estomo, Jan'),
        ('Hector Hernandez', 'hector@myhealthteam.org', 'HERHE000', 'Hernandez, Hector', 'Hernandez, Hector'),
        ('Anisha Jackson', 'anisha@myhealthteam.org', 'JACAN000', 'Jackson, Anisha', 'Jackson, Anisha'),
        ('Jaspreet Kaur', 'jaspreet@myhealthteam.org', 'KAUJA000', 'Kaur, Jaspreet', 'Kaur, Jaspreet'),
        ('Justin Malhotra MD', 'admin@myhealthteam.org', 'MALJU000', 'Malhotra, Justin', 'Malhotra, Justin'),
        ('Sherwin Maningas', 'sherwin@myhealthteam.org', 'MANSH000', 'Maningas, Sherwin', 'Maningas, Sherwin'),
        ('Cindy Mariano', 'cindy@myhealthteam.org', 'MARCI000', 'Mariano, Cindy', 'Mariano, Cindy'),
        ('Dianela Medez', 'dianela@myhealthteam.org', 'MEDDI000', 'Medez, Dianela', 'Medez, Dianela'),
        ('Claudia Melara', 'claudia@myhealthteam.org', 'MELCL000', 'Melara, Claudia', 'Melara, Claudia'),
        ('Angela Otegbulu', 'angela@myhealthteam.org', 'OTEAN000', 'Otegbulu, Angela', 'Otegbulu, Angela'),
        ('Jorge Perez', 'jorge@myhealthteam.org', 'PERJO000', 'Perez, Jorge', 'Perez, Jorge'),
        ('Manuel Rios', 'manuel@myhealthteam.org', 'RIOMA000', 'Rios, Manuel', 'Rios, Manuel'),
        ('Bianchi Sanchez', 'bianchi@myhealthteam.org', 'SANBI000', 'Sanchez, Bianchi', 'Sanchez, Bianchi'),
        ('Laura Sumpay CC', 'laura@myhealthteam.org', 'SUMLA000', 'Sumpay, Laura', 'Sumpay, Laura'),
        ('Shirley Alter CC', 'shirley@myhealthteam.org', 'ALTSH000', 'Alter, Shirley', 'Alter, Shirley'),
        ('Jose Soberanis', 'jose@myhealthteam.org', 'SOBJO000', 'Soberanis, Jose', 'Soberanis, Jose'),
        ('Andrew Szalas NP', 'andrews@myhealthteam.org', 'SZAAN000', 'Szalas, Andrew', 'Szalas, Andrew'),
        ('Lourdes Villasenor NP', 'lourdesv@myhealthteam.org', 'VILLO000', 'Villasenor, Lourdes', 'Villasenor, Lourdes')
    ]

    # Insert all staff data
    for staff in staff_data:
        cursor.execute("""
            INSERT INTO staff_codes (full_name, email, coordinator_code, provider_code, alt_provider_code)
            VALUES (?, ?, ?, ?, ?)
        """, staff)

    conn.commit()

    # Verify data was inserted
    cursor.execute("SELECT COUNT(*) FROM staff_codes")
    count = cursor.fetchone()[0]

    print(f"✅ Successfully created staff_codes table")
    print(f"📊 Populated with {count} staff members")
    print(f"🗄️ Table location: {db_path}")

    # Show sample of the data
    print("\n📋 Sample staff data:")
    cursor.execute("SELECT full_name, coordinator_code, provider_code FROM staff_codes LIMIT 5")
    for row in cursor.fetchall():
        print(f"   {row[0]} | {row[1]} | {row[2]}")

    conn.close()
    print(f"\n🎯 Next steps:")
    print(f"   • Update import scripts to query this table")
    print(f"   • Add/remove staff by updating this table instead of multiple files")
    print(f"   • Use this as single source of truth for staff codes")

if __name__ == "__main__":
    create_staff_codes_table()