import re
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'production.db'
OUTFILE = 'scripts/names_dobs_from_tables_filtered.txt'

# date matcher (find last date-like token)
date_re = re.compile(r"(\d{1,2}[/-]\d{1,2}[/-](?:\d{2,4}))")

noise_keywords = [
    'televisit', 'tele', 'new tele', 'new televisit', 'appt', 'appointment', 'intake', 'no answer', 'no answe',
    'scheduled', 'confirmed', 'confirmed appt', 'cm', 'pcp/', 'admit date', 'dob:', 'hospitalized', 'facility',
    'address', 'phone', 'medicare', 'rp:', 'rp', 'rescheduled', 'homevisit', 'home visit', 'lab', 'labs', 'called',
    'call', 'message', 'text', 'notified', 'patient passed', 'superadmin', 'homevist', 'homevsit', 'homevst', 'onboarding',
    'mayra', 'tele', 'televisit', 'no answe', 'no answer', 'lvm', 'no-show', 'no show', 'cancel', 'cancelled'
]

name_pat = re.compile(r"^[A-Z][A-Z\- ',\.]{1,200}$")

tables = [
    ('SOURCE_PATIENT_DATA', ['Last', 'First', 'DOB', 'LAST FIRST DOB']),
    ('SOURCE_COORDINATOR_TASKS_HISTORY', ['Pt Name']),
    ('SOURCE_PROVIDER_TASKS_HISTORY', ['Patient Last, First DOB', 'Patient Last, First DOB.1']),
]


def fetch_values(conn, table, cols):
    out = []
    cur = conn.cursor()
    # If separate Last/First/DOB present, fetch combined
    if set(['Last', 'First', 'DOB']).issubset(cols):
        q = "SELECT DISTINCT TRIM(COALESCE(Last,'')) as Last, TRIM(COALESCE(First,'')) as First, TRIM(COALESCE(DOB,'')) as DOB FROM [%s]" % table
        for last, first, dob in cur.execute(q):
            if not dob or (not last and not first):
                continue
            combined = f"{last} {first} {dob}".strip()
            out.append(combined)
    # composite columns
    for col in cols:
        if col not in ('Last', 'First', 'DOB'):
            try:
                q = "SELECT DISTINCT TRIM([%s]) FROM [%s] WHERE [%s] IS NOT NULL AND TRIM([%s]) <> ''" % (col, table, col, col)
                for (val,) in cur.execute(q):
                    if val:
                        out.append(val.strip())
            except Exception:
                continue
    return out


def likely_noise(s: str) -> bool:
    low = s.lower()
    for k in noise_keywords:
        if k in low:
            return True
    # common short tokens that are not names
    if len(s) < 4:
        return True
    return False


def normalize_and_extract(line: str):
    # find last date token in the line
    dates = list(date_re.finditer(line))
    if not dates:
        return None
    m = dates[-1]
    date_token = m.group(1)
    name_part = line[:m.start()].strip()
    name_part = re.sub(r"[\t ]+", ' ', name_part).strip()
    if not name_part:
        return None
    if likely_noise(name_part):
        return None
    # require at least two words or a comma
    if (',' not in name_part) and (len(name_part.split()) < 2):
        return None
    up = name_part.upper().rstrip('.,;:')
    if not name_pat.match(up):
        letters = sum(1 for c in up if c.isalpha())
        if letters < 0.6 * max(1, len(up.replace(' ', ''))):
            return None
    # parse date
    parts = re.split(r'[/-]', date_token)
    try:
        mm = int(parts[0]); dd = int(parts[1]); yy = int(parts[2])
        if yy < 100:
            yy = 2000 + yy if yy <= (datetime.now().year % 100) else 1900 + yy
        if not (1900 <= yy <= datetime.now().year):
            return None
        datetime(yy, mm, dd)
    except Exception:
        return None
    # normalize name spacing
    name_norm = re.sub(r'\s+', ' ', up)
    return name_norm, f"{mm:02d}/{dd:02d}/{yy}"


def main():
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        return
    conn = sqlite3.connect(str(DB_PATH))
    try:
        # get table columns for presence check
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {r[0] for r in cur.fetchall()}
        results = []
        for table, wanted_cols in tables:
            if table not in existing_tables:
                print(f"Table {table} not found, skipping")
                continue
            # fetch PRAGMA columns
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{table}')")]
            vals = fetch_values(conn, table, cols)
            print(f"{table}: fetched {len(vals)} raw values from target columns")
            results.extend(vals)
        # process and dedupe
        seen = set()
        cleaned = []
        for raw in results:
            try:
                item = raw.strip()
            except Exception:
                continue
            res = normalize_and_extract(item)
            if not res:
                continue
            name, dob = res
            key = (name, dob)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append((name, dob))
        # write output
        outpath = ROOT / OUTFILE
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(f"{len(cleaned)} entries\n")
            for n,d in cleaned:
                f.write(f"{n}\t{d}\n")
        print(f"Wrote {len(cleaned)} filtered entries to {outpath}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()

