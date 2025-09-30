import sqlite3
import re
from pathlib import Path

DB = 'production.db'
OUT_DIR = Path('scripts')

def get_tables(conn):
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return sorted([r[0] for r in cur.fetchall()])

def find_tables_by_pattern(conn, pattern):
    # case-insensitive match substring
    tables = get_tables(conn)
    pat = pattern.lower()
    return [t for t in tables if pat in t.lower()]

def pretty_write(name, rows):
    path = OUT_DIR / f'unique_names_{name}.txt'
    with path.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(r + '\n')
    print(f'Wrote {len(rows)} names to {path}')

def likely_real_name(s: str) -> bool:
    if not s:
        return False
    s = s.strip()
    if len(s) < 3:
        return False
    low = s.lower()
    # Exclude emails, numeric codes, placeholders
    if '@' in s or 'http' in low:
        return False
    if low in ('n/a', 'na', 'unknown', 'none', 'none found', 'test'):
        return False
    # Exclude strings that are mostly digits or contain suspicious punctuation
    digits = sum(c.isdigit() for c in s)
    if digits > len(s) * 0.4:
        return False
    # Accept if contains a space (first last) or comma (last, first) or DOB pattern
    if ' ' in s or ',' in s or re.search(r'\d{4}-\d{2}-\d{2}', s) or re.search(r'\d{2}/\d{2}/\d{4}', s):
        return True
    # Otherwise reject short single-token strings
    return False

def extract_from_table(conn, table):
    cur = conn.execute(f"PRAGMA table_info({table})")
    info = cur.fetchall()
    cols = [r[1] for r in info]
    col_types = {r[1]: (r[2] or '').upper() for r in info}
    print(' Columns:', cols)
    names = set()

    # Common patterns
    if 'first_name' in cols and 'last_name' in cols:
        rows = conn.execute(f"SELECT DISTINCT first_name, last_name FROM {table}").fetchall()
        for fn, ln in rows:
            name = ((ln or '').strip() + ', ' + (fn or '').strip()).strip(', ').strip()
            if name:
                names.add(name)
    elif 'patient_name' in cols:
        rows = conn.execute(f"SELECT DISTINCT patient_name FROM {table}").fetchall()
        for (pn,) in rows:
            if pn:
                names.add(pn.strip())
    elif 'pt_name' in cols:
        rows = conn.execute(f"SELECT DISTINCT pt_name FROM {table}").fetchall()
        for (pn,) in rows:
            if pn:
                names.add(pn.strip())
    elif 'patient_last' in cols and 'patient_first' in cols:
        rows = conn.execute(f"SELECT DISTINCT patient_last, patient_first FROM {table}").fetchall()
        for last, first in rows:
            name = ((last or '').strip() + ', ' + (first or '').strip()).strip(', ').strip()
            if name:
                names.add(name)
    else:
        # fallback: try concatenating up to three likely text columns
        text_like = [c for c in cols if ('CHAR' in col_types.get(c, '') or 'TEXT' in col_types.get(c, '') or col_types.get(c,'')=='')]
        if not text_like:
            # if no types declared as text, fallback to any columns with 'name'/'first'/'last'
            text_like = [c for c in cols if 'name' in c.lower() or 'first' in c.lower() or 'last' in c.lower() or c.lower().startswith('pt_')]
        if text_like:
            # try combinations of up to 3 columns
            tried = False
            for i in range(min(3, len(text_like))):
                sel_cols = text_like[:i+1]
                sel = " || ' ' || ".join(sel_cols)
                try:
                    rows = conn.execute(f"SELECT DISTINCT {sel} FROM {table} LIMIT 10000").fetchall()
                    tried = True
                    for (val,) in rows:
                        if val:
                            names.add(str(val).strip())
                    if names:
                        break
                except Exception as e:
                    # continue trying with different combos
                    continue
            if not tried:
                print(f'Could not build fallback selection for table {table}')

    filtered = sorted(n for n in names if likely_real_name(n))
    pretty_write(table, filtered)
    print(f'{table}: total distinct names=', len(names), 'likely real names=', len(filtered))
    if filtered:
        print('Sample:', filtered[:20])

def extract_from_source_coordinators(conn):
    # table may be named source_coordinators_task_history or similar
    cand = 'source_coordinators_task_history'
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (cand,))
    if not cur.fetchone():
        print(f'{cand} not found')
        return
    cur = conn.execute(f"PRAGMA table_info({cand})")
    cols = [r[1] for r in cur.fetchall()]
    names = set()
    if 'pt_name' in cols:
        rows = conn.execute(f"SELECT DISTINCT pt_name FROM {cand}").fetchall()
        for (v,) in rows:
            if v:
                names.add(v.strip())
    else:
        # look for patient_name-like cols
        possible = [c for c in cols if 'name' in c or 'pt_' in c]
        if possible:
            sel = possible[0]
            rows = conn.execute(f"SELECT DISTINCT {sel} FROM {cand}").fetchall()
            for (v,) in rows:
                if v:
                    names.add(v.strip())
    filtered = sorted(n for n in names if likely_real_name(n))
    pretty_write(cand, filtered)
    print(f'{cand}: total distinct names=', len(names), 'likely real=', len(filtered))

def extract_from_source_providers(conn):
    cand = 'source_providers_task_history'
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (cand,))
    if not cur.fetchone():
        print(f'{cand} not found')
        return
    cur = conn.execute(f"PRAGMA table_info({cand})")
    cols = [r[1] for r in cur.fetchall()]
    names = set()
    # possible columns: patient_last, patient_first, patient_dob or patient_last_first_dob
    if 'patient_last' in cols and 'patient_first' in cols:
        rows = conn.execute(f"SELECT DISTINCT patient_last, patient_first FROM {cand}").fetchall()
        for last, first in rows:
            name = ((last or '').strip() + ', ' + (first or '').strip()).strip(', ').strip()
            if name:
                names.add(name)
    elif 'patient_last_first_dob' in cols:
        rows = conn.execute(f"SELECT DISTINCT patient_last_first_dob FROM {cand}").fetchall()
        for (v,) in rows:
            if v:
                names.add(v.strip())
    else:
        possible = [c for c in cols if 'patient' in c and 'name' in c]
        if possible:
            sel = possible[0]
            rows = conn.execute(f"SELECT DISTINCT {sel} FROM {cand}").fetchall()
            for (v,) in rows:
                if v:
                    names.add(v.strip())
    filtered = sorted(n for n in names if likely_real_name(n))
    pretty_write(cand, filtered)
    print(f'{cand}: total distinct names=', len(names), 'likely real=', len(filtered))

def main():
    conn = sqlite3.connect(DB)
    try:
            tables = get_tables(conn)
            print('Tables found:', tables)

            # Patterns to find
            patterns = ['source_pat', 'source_coordinator', 'source_provider']
            for pat in patterns:
                matches = [t for t in tables if pat in t.lower()]
                if not matches:
                    print(f'No tables matching pattern: {pat}')
                    continue
                for t in matches:
                    print('Extracting names from', t)
                    extract_from_table(conn, t)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
