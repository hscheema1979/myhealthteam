import sqlite3, datetime, os

SRC_DB = 'production.db'
BACKUP_DIR = 'backups'

os.makedirs(BACKUP_DIR, exist_ok=True)

ts = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
backup_path = os.path.join(BACKUP_DIR, f'production_backup_{ts}.db')

print(f'Backing up {SRC_DB} to {backup_path} using sqlite3 backup API...')

src_conn = sqlite3.connect(SRC_DB)
dst_conn = sqlite3.connect(backup_path)
try:
    with dst_conn:
        src_conn.backup(dst_conn)
    print('Backup completed.')
except Exception as e:
    print('Backup failed:', e)
    raise
finally:
    src_conn.close()
    dst_conn.close()

print(backup_path)
