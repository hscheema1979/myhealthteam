
import sqlite3
import os
import datetime
import shutil

DB_PATHS = {
    "myhealthteam_app": "/opt/myhealthteam/production.db",
    "vps_monitor": "/var/lib/vps_monitor.db"
}

BASE_BACKUP_DIR = "/opt/myhealthteam/backups/"
DAILY_BACKUP_DIR = os.path.join(BASE_BACKUP_DIR, "daily")
WEEKLY_BACKUP_DIR = os.path.join(BASE_BACKUP_DIR, "weekly")
MONTHLY_BACKUP_DIR = os.path.join(BASE_BACKUP_DIR, "monthly")

RETENTION_DAYS = {
    "daily": 7,
    "weekly": 28,  # 4 weeks
    "monthly": 90  # 3 months
}

def ensure_dir(directory):
    os.makedirs(directory, exist_ok=True)

def perform_backup(db_path, backup_dir, db_name):
    ensure_dir(backup_dir)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{db_name}_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        # Use SQLite online backup API for safe backups
        source_conn = sqlite3.connect(db_path)
        dest_conn = sqlite3.connect(backup_path)
        with dest_conn:
            source_conn.backup(dest_conn)
        print(f"Backup of {db_path} to {backup_path} successful.")
        return True
    except sqlite3.Error as e:
        print(f"Backup of {db_path} failed: {e}")
        return False
    finally:
        if source_conn:
            source_conn.close()
        if dest_conn:
            dest_conn.close()

def apply_retention_policy(backup_dir, retention_days):
    now = datetime.datetime.now()
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath):
            creation_time = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
            if (now - creation_time).days > retention_days:
                os.remove(filepath)
                print(f"Removed old backup: {filepath}")

def run_backups():
    # Daily backups
    for db_name, db_path in DB_PATHS.items():
        perform_backup(db_path, DAILY_BACKUP_DIR, db_name)
    apply_retention_policy(DAILY_BACKUP_DIR, RETENTION_DAYS["daily"])

    # Weekly backups (e.g., every Sunday)
    if datetime.datetime.now().weekday() == 6:  # Sunday is 6
        for db_name, db_path in DB_PATHS.items():
            perform_backup(db_path, WEEKLY_BACKUP_DIR, db_name)
        apply_retention_policy(WEEKLY_BACKUP_DIR, RETENTION_DAYS["weekly"])

    # Monthly backups (e.g., on the 1st of the month)
    if datetime.datetime.now().day == 1:
        for db_name, db_path in DB_PATHS.items():
            perform_backup(db_path, MONTHLY_BACKUP_DIR, db_name)
        apply_retention_policy(MONTHLY_BACKUP_DIR, RETENTION_DAYS["monthly"])

if __name__ == "__main__":
    run_backups()
