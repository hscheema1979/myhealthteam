import sqlite3, pathlib, sys, re

SQL_FILE = pathlib.Path('src/sql/5_schema_enhancement.sql')
DB_FILE = 'production.db'

if not SQL_FILE.exists():
    print('Migration SQL file not found:', SQL_FILE)
    sys.exit(1)

raw_sql = SQL_FILE.read_text()
# Strip Markdown code fences if present
if raw_sql.strip().startswith('```'):
    lines = raw_sql.splitlines()
    if lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith('```'):
        lines = lines[:-1]
    raw_sql = '\n'.join(lines)

# Split into statements by semicolon
statements = [s.strip() for s in raw_sql.split(';') if s.strip()]

print('Running idempotent migration SQL against', DB_FILE)
conn = sqlite3.connect(DB_FILE)
try:
    cur = conn.cursor()
    for stmt in statements:
        # Normalize whitespace
        s = re.sub(r"\s+", " ", stmt).strip()

        # Handle ALTER TABLE ... ADD COLUMN specially to avoid duplicate column errors
        m = re.match(r"ALTER TABLE ([A-Za-z0-9_]+) ADD COLUMN ([A-Za-z0-9_]+) (.+)", s, re.IGNORECASE)
        if m:
            table = m.group(1)
            column = m.group(2)
            # Check if column exists
            cur.execute(f"PRAGMA table_info({table});")
            cols = [r[1] for r in cur.fetchall()]
            if column in cols:
                print(f"Skipping existing column: {table}.{column}")
                continue
            try:
                print(f"Applying: ALTER TABLE {table} ADD COLUMN {column}")
                cur.execute(stmt)
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"Failed to apply ALTER for {table}.{column}: {e}")
                conn.rollback()
                raise
            continue

        # For other statements (CREATE INDEX, PRAGMA, etc.) run and ignore 'already exists' errors
        try:
            cur.execute(stmt)
            conn.commit()
        except sqlite3.OperationalError as e:
            msg = str(e).lower()
            if 'already exists' in msg or 'duplicate column name' in msg:
                print(f"Skipping statement due to existing object: {e}")
                conn.rollback()
                continue
            else:
                conn.rollback()
                print('Migration failed on statement:', stmt[:80])
                raise

    print('Migration applied (idempotent runner completed).')
finally:
    conn.close()
