#!/usr/bin/env python3
import sqlite3
import difflib
import re
import csv
from collections import namedtuple

DB = 'production.db'
OUT = 'outputs/assigned_cm_fuzzy_suggestions.csv'

def normalize(name):
    if not name:
        return ''
    s = name.strip()
    # remove common titles and degrees
    s = re.sub(r'\b(MD|DO|NP|RN|LCSW|MSW|PA|NP,|MD,|RN,)\b', '', s, flags=re.I)
    s = re.sub(r'[,\.]+', ',', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip().strip(',')

def swap_first_last(s):
    # If 'First Last' -> return 'Last, First'
    parts = s.split()
    if len(parts) >= 2:
        first = parts[0]
        last = ' '.join(parts[1:])
        return f"{last}, {first}"
    return s

def best_fuzzy(target, candidates):
    best = None
    best_score = 0.0
    for cand in candidates:
        score = difflib.SequenceMatcher(None, target.lower(), cand.lower()).ratio()
        if score > best_score:
            best_score = score
            best = cand
    return best, best_score

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # fetch distinct Assigned CM values with counts and unmapped counts
    cur.execute('''
    SELECT spd."Assigned CM" AS assigned_cm,
        COUNT(*) AS total_count,
        SUM(CASE WHEN p.assigned_coordinator_id IS NULL OR p.assigned_coordinator_id = '' THEN 1 ELSE 0 END) AS unmapped_count
    FROM SOURCE_PATIENT_DATA spd
    JOIN patients p ON spd."LAST FIRST DOB" = p.last_first_dob
    GROUP BY spd."Assigned CM"
    ORDER BY total_count DESC
    ''')
    assigned_rows = cur.fetchall()

    # fetch users
    cur.execute("SELECT user_id, COALESCE(full_name, TRIM(COALESCE(last_name,'') || ', ' || COALESCE(first_name,''))) AS full_name FROM users")
    users = cur.fetchall()
    user_map = { (row['full_name'] or '').strip(): row['user_id'] for row in users if (row['full_name'] or '').strip() }
    user_full_names = [ (row['full_name'] or '').strip() for row in users if (row['full_name'] or '').strip() ]

    Suggest = namedtuple('Suggest', ['assigned_cm', 'total_count', 'unmapped_count', 'best_full_name', 'user_id', 'score', 'heuristic', 'confidence'])
    suggestions = []

    for r in assigned_rows:
        assigned_cm = r['assigned_cm'] or ''
        total = r['total_count']
        unmapped = r['unmapped_count']
        norm = normalize(assigned_cm)

        heuristic = None
        match_name = None
        match_id = None
        score = 0.0

        # 1) exact match to users.full_name
        for u in user_full_names:
            if norm.lower() == u.lower():
                heuristic = 'exact_full_name'
                match_name = u
                match_id = user_map[u]
                score = 1.0
                break

        # 2) try swap First Last -> Last, First
        if not match_name:
            swapped = swap_first_last(norm)
            for u in user_full_names:
                if swapped.lower() == u.lower():
                    heuristic = 'swap_first_last'
                    match_name = u
                    match_id = user_map[u]
                    score = 0.95
                    break

        # 3) try unique last-name match
        if not match_name:
            parts = norm.split()
            if len(parts) >= 1:
                last = parts[-1]
                candidates = [u for u in user_full_names if u.split(',')[0].strip().lower() == last.lower()]
                if len(candidates) == 1:
                    heuristic = 'unique_last'
                    match_name = candidates[0]
                    match_id = user_map[match_name]
                    score = 0.9

        # 4) fuzzy match
        if not match_name:
            best, best_score = best_fuzzy(norm, user_full_names)
            if best:
                heuristic = 'fuzzy'
                match_name = best
                match_id = user_map[best]
                score = best_score

        # confidence bucket
        if score >= 0.90:
            confidence = 'high'
        elif score >= 0.75:
            confidence = 'medium'
        elif score >= 0.60:
            confidence = 'low'
        else:
            confidence = 'none'

        suggestions.append(Suggest(assigned_cm, total, unmapped, match_name, match_id, round(score, 3), heuristic, confidence))

    # ensure outputs dir
    import os
    outdir = os.path.dirname(OUT)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir)

    # write CSV
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['assigned_cm','total_count','unmapped_count','best_full_name','user_id','score','heuristic','confidence'])
        for s in suggestions:
            writer.writerow([s.assigned_cm, s.total_count, s.unmapped_count, s.best_full_name or '', s.user_id or '', s.score, s.heuristic or '', s.confidence])

    # print summary
    total_distinct = len(suggestions)
    high_conf = sum(1 for s in suggestions if s.confidence == 'high')
    med_conf = sum(1 for s in suggestions if s.confidence == 'medium')
    low_conf = sum(1 for s in suggestions if s.confidence == 'low')
    none = sum(1 for s in suggestions if s.confidence == 'none')

    print(f"total_distinct_assigned_cm={total_distinct}")
    print(f"high_conf_suggestions={high_conf}")
    print(f"medium_conf_suggestions={med_conf}")
    print(f"low_conf_suggestions={low_conf}")
    print(f"no_suggestion={none}")
    print(f"wrote={OUT}")

if __name__ == '__main__':
    main()
