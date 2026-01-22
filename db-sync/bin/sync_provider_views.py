"""Sync provider import views to VPS2"""
import sqlite3
import subprocess

def get_provider_views():
    """Get all provider import view definitions"""
    conn = sqlite3.connect("production.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, sql FROM sqlite_master
        WHERE type='view' AND name LIKE 'provider_monthly_%_import'
        ORDER BY name DESC
    """)
    views = cursor.fetchall()
    conn.close()

    return views

def sync_to_vps2(views):
    """Drop and recreate views on VPS2"""

    # First, drop all existing views
    drop_statements = [
        f"DROP VIEW IF EXISTS {name};"
        for name, _ in views
    ]

    # Create statements - sql already contains "CREATE VIEW name AS"
    create_statements = [
        f"{sql};"
        for _, sql in views
    ]

    all_sql = "\n".join(drop_statements + create_statements)

    # Run on VPS2
    result = subprocess.run(
        ["ssh", "server2", "sqlite3", "/opt/myhealthteam/production.db"],
        input=all_sql,
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False

    print(f"Synced {len(views)} provider import views to VPS2")
    return True

if __name__ == "__main__":
    views = get_provider_views()
    print(f"Found {len(views)} provider import views locally")

    for name, sql in views:
        print(f"  - {name}")

    if sync_to_vps2(views):
        print("Success!")
    else:
        print("Failed to sync")
