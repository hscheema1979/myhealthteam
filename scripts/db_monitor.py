
import sqlite3
import os
import json
import datetime

DB_PATHS = {
    "myhealthteam_app": "/opt/myhealthteam/production.db",
    "vps_monitor": "/var/lib/vps_monitor.db"
}

BACKUP_DIR = "/opt/myhealthteam/backups/"

def get_db_size(db_path):
    if os.path.exists(db_path):
        return os.path.getsize(db_path)
    return 0

def check_db_integrity(db_path):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        return result == "ok"
    except sqlite3.Error as e:
        print(f"Database integrity check failed for {db_path}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_connection_count(db_path):
    # For SQLite, direct connection count is not easily obtainable as it's embedded.
    # This would typically require OS-level process monitoring or application-level logging.
    # For simplicity, we'll return 0 or implement a placeholder if needed.
    return 0  # Placeholder for SQLite

def monitor_databases():
    monitoring_data = {}
    for db_name, db_path in DB_PATHS.items():
        data = {
            "size": get_db_size(db_path),
            "integrity_ok": check_db_integrity(db_path),
            "connection_count": get_connection_count(db_path) # Placeholder
        }
        monitoring_data[db_name] = data
    return monitoring_data

if __name__ == "__main__":
    data = monitor_databases()
    timestamp = datetime.datetime.now().isoformat()
    # In a real scenario, you'd store this in a monitoring database or send to a dashboard.
    # For now, print it to stdout or a log file.
    print(json.dumps({"timestamp": timestamp, "database_metrics": data}, indent=2))

    # Example of how you might store this data in the vps_monitor.db or a separate monitoring DB
    # This part would need integration with dashboard_web_app.py or a similar component.
    # For now, let's just log it to a file for demonstration.
    log_file_path = os.path.join(BACKUP_DIR, "db_monitor_log.json")
    with open(log_file_path, "a") as f:
        f.write(json.dumps({"timestamp": timestamp, "database_metrics": data}) + "\n")
