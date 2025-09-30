#!/usr/bin/env python3
"""
Normalize patient name+DOB strings from source tables and export a CSV mapping raw->normalized.

Rules (conservative):
- Strip explicit vendor/facility prefixes (blacklist: BlessedCare, BleessedCare, zen, 3pr, etc.)
- Strip tokens that contain words like 'care', 'clinic', 'center' at the start
- Strip numeric prefixes or prefixes containing digits before '-' or ':'
- Do NOT strip ordinary hyphenated surnames (e.g. GUY-DAVIS, PORTILLO-RAYAN) unless the prefix matches blacklist or contains digits or vendor keywords

Outputs:
- `scripts/normalized_mappings.csv` with columns: raw, normalized, src
- Summary printed to stdout with counts and sample multi-source matches

Run from repository root: `python scripts/normalize_names.py`
"""

import sqlite3
import re
import csv
from collections import defaultdict, Counter
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'production.db'
OUT_CSV = Path(__file__).resolve().parent / 'normalized_mappings.csv'

BLACKLIST = [
    'blessedcare', 'bleessedcare', 'zen', '3pr', 'blessed care'
]

VENDOR_KEYWORDS = ['care', 'clinic', 'center', 'services']

def collapse_whitespace(s: str) -> str:
    s = re.sub(r'[\t\r\n]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def strip_prefix_blacklist(s: str) -> str:
    # Strip explicit blacklisted prefixes at start followed by common separators
    pattern = r'^(?:' + '|'.join(re.escape(b) for b in BLACKLIST) + r')[:\-,:\s]+'
    m = re.match(pattern, s, flags=re.I)
    if m:
        return s[m.end():].strip()
    return s

def strip_vendor_like_prefix(s: str) -> str:
    # If the initial token contains vendor keywords (care/clinic/etc.), strip it
    m = re.match(r'^([^\-,:\s]{1,60})[\-,:\s]+(.*)$', s)
    if m:
        token = m.group(1)
        rest = m.group(2)
        if any(kw in token.lower() for kw in VENDOR_KEYWORDS):
            return rest.strip()
    return s

def strip_numeric_prefix_before_delim(s: str) -> str:
    # If prefix before '-' or ':' contains digits, strip the prefix
    for delim in ('-', ':'):
        if delim in s:
            prefix, rest = s.split(delim, 1)
            if re.search(r'\d', prefix):
                return rest.strip()
    return s

def normalize(raw: str) -> str:
    if raw is None:
        return raw
    s = collapse_whitespace(raw)
    if not s:
        return s

    # First, apply explicit blacklist removal
    s2 = strip_prefix_blacklist(s)
    if s2 != s:
        s = s2

    # Vendor-like tokens containing 'care' etc.
    s2 = strip_vendor_like_prefix(s)
    if s2 != s:
        s = s2

    # Numeric prefix before delimiters
    s2 = strip_numeric_prefix_before_delim(s)
    if s2 != s:
        s = s2

    # Colon-prefixed tokens: only strip if blacklisted or numeric or vendor-like
    if ':' in s:
        prefix, rest = s.split(':', 1)
        prefix = prefix.strip()
        lowerp = prefix.lower()
        if lowerp in BLACKLIST or re.search(r'\d', prefix) or any(kw in lowerp for kw in VENDOR_KEYWORDS):
            s = rest.strip()

    # Hyphen handling: be conservative: only strip hyphen prefix if prefix contains digits or vendor keywords
    if '-' in s:
        prefix, rest = s.split('-', 1)
        lowerp = prefix.strip().lower()
        if re.search(r'\d', prefix) or any(kw in lowerp for kw in VENDOR_KEYWORDS) or lowerp in BLACKLIST:
            s = rest.strip()
        else:
            # keep hyphenated name as-is (likely family name)
            s = s

    # Final cleanups
    s = re.sub(r'\s*,\s*', ', ', s)
    s = collapse_whitespace(s)
    return s

def fetch_raw_rows(conn):
    queries = [
        ("SOURCE_PATIENT_DATA",
         "SELECT TRIM(COALESCE(Last,'') || ' ' || COALESCE(First,'') || ' ' || COALESCE(DOB,'')) AS raw FROM SOURCE_PATIENT_DATA WHERE (Last IS NOT NULL OR First IS NOT NULL OR DOB IS NOT NULL) AND TRIM(COALESCE(Last,'') || ' ' || COALESCE(First,'') || ' ' || COALESCE(DOB,'')) != ''"),
        ("SOURCE_PATIENT_DATA",
         "SELECT TRIM([LAST FIRST DOB]) AS raw FROM SOURCE_PATIENT_DATA WHERE [LAST FIRST DOB] IS NOT NULL AND TRIM([LAST FIRST DOB]) <> ''"),
        ("SOURCE_COORDINATOR_TASKS_HISTORY",
         "SELECT TRIM([Pt Name]) AS raw FROM SOURCE_COORDINATOR_TASKS_HISTORY WHERE [Pt Name] IS NOT NULL AND TRIM([Pt Name]) <> ''"),
        ("SOURCE_PROVIDER_TASKS_HISTORY",
         "SELECT TRIM([Patient Last, First DOB]) AS raw FROM SOURCE_PROVIDER_TASKS_HISTORY WHERE [Patient Last, First DOB] IS NOT NULL AND TRIM([Patient Last, First DOB]) <> ''"),
        ("SOURCE_PROVIDER_TASKS_HISTORY",
         "SELECT TRIM([Patient Last, First DOB.1]) AS raw FROM SOURCE_PROVIDER_TASKS_HISTORY WHERE [Patient Last, First DOB.1] IS NOT NULL AND TRIM([Patient Last, First DOB.1]) <> ''"),
    ]
    for src, q in queries:
        try:
            for (raw,) in conn.execute(q):
                if raw is None:
                    continue
                raw2 = raw.strip()
                if raw2 == '':
                    continue
                yield raw2, src
        except sqlite3.OperationalError:
            # table or column missing, skip gracefully
            continue

def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = None

    mappings = []
    src_counts = Counter()
    norm_counts = Counter()
    raw_seen = set()

    for raw, src in fetch_raw_rows(conn):
        norm = normalize(raw)
        mappings.append((raw, norm, src))
        src_counts[src] += 1
        norm_counts[norm] += 1
        raw_seen.add(raw)

    # Write CSV
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['raw', 'normalized', 'src'])
        for row in mappings:
            writer.writerow(row)

    # Summary
    print('Wrote', OUT_CSV)
    print('Total raw rows processed:', sum(src_counts.values()))
    print('Counts per source:')
    for src, cnt in src_counts.most_common():
        print('  ', src, '|', cnt)

    unique_norm = len([n for n in norm_counts.keys() if n and n.strip()])
    print('Unique normalized values (non-empty):', unique_norm)
    print('Top 20 normalized values:')
    for norm, cnt in norm_counts.most_common(20):
        print('  ', repr(norm)[:80].ljust(40), '|', cnt)

    # Find normalized values that appear in multiple sources
    value_sources = defaultdict(set)
    for raw, norm, src in mappings:
        value_sources[norm].add(src)

    multi = [(norm, len(srcs), srcs) for norm, srcs in value_sources.items() if len(srcs) > 1]
    multi.sort(key=lambda x: (-x[1], x[0]))
    print('Normalized values appearing in multiple sources (top 20):')
    for norm, count, srcs in multi[:20]:
        print('  ', repr(norm)[:80].ljust(40), '|', count, '|', ','.join(sorted(srcs)))

    conn.close()

if __name__ == '__main__':
    main()
