"""
Generate a migration audit report by checking each ALTER/CREATE statement
in `src/sql/5_schema_enhancement.sql` and reporting whether it was applied
or skipped based on presence in the current `production.db` schema.
"""
import re
import sqlite3
from pathlib import Path

SQL_FILE = Path('src/sql/5_schema_enhancement.sql')
DB_FILE = 'production.db'
OUT_FILE = Path('scripts/migration_audit.txt')

def load_statements():
    raw = SQL_FILE.read_text()
    if raw.strip().startswith('```'):
        lines = raw.splitlines()
        if lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith('```'):
            lines = lines[:-1]
        raw = '\n'.join(lines)
    stmts = [s.strip() for s in raw.split(';') if s.strip()]
    return stmts

def table_columns(conn, table):
    try:
        cur = conn.execute(f"PRAGMA table_info({table});")
        return [r[1] for r in cur.fetchall()]
    except Exception:
        return []

def audit():
    conn = sqlite3.connect(DB_FILE)
    results = []
    stmts = load_statements()
    for s in stmts:
        s_norm = re.sub(r"\s+", " ", s).strip()
        if s_norm.upper().startswith('ALTER TABLE') and 'ADD COLUMN' in s_norm.upper():
            m = re.match(r"ALTER TABLE ([A-Za-z0-9_]+) ADD COLUMN ([A-Za-z0-9_]+)", s_norm, re.IGNORECASE)
            if m:
                table, column = m.group(1), m.group(2)
                cols = table_columns(conn, table)
                status = 'APPLIED' if column in cols else 'MISSING'
                results.append((s_norm, status, table, column))
                continue

        if s_norm.upper().startswith('CREATE INDEX') or s_norm.upper().startswith('CREATE UNIQUE INDEX'):
            # check for index existence
            name_m = re.match(r"CREATE (UNIQUE )?INDEX IF NOT EXISTS ([A-Za-z0-9_]+)", s_norm, re.IGNORECASE)
            if name_m:
                idx_name = name_m.group(2)
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name = ?", (idx_name,))
                found = cur.fetchone() is not None
                results.append((s_norm, 'APPLIED' if found else 'MISSING', 'index', idx_name))
                continue

        # fallback: mark as UNKNOWN
        results.append((s_norm, 'UNKNOWN', '', ''))

    conn.close()

    with OUT_FILE.open('w', encoding='utf-8') as f:
        f.write('Migration Audit Report\n')
        f.write('======================\n\n')
        for stmt, status, table, column in results:
            f.write(f'STATUS: {status}\n')
            f.write(stmt.replace('\n', ' ') + '\n')
            if table:
                f.write(f'Object: {table}.{column}\n')
            f.write('\n')

    print('Audit written to', OUT_FILE)

if __name__ == '__main__':
    audit()
