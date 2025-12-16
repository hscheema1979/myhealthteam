#!/usr/bin/env python3
"""
Group normalized mappings to remove repeats and produce a summarized CSV.

Output: `scripts/normalized_summary.csv` with columns:
 - normalized
 - total_count
 - sources (source:count semi-colon separated)
 - sample_raws (up to 5 examples separated by ' | ')

Run: `python scripts/group_normalized.py`
"""

import csv
from collections import defaultdict, Counter
from pathlib import Path

IN_CSV = Path(__file__).resolve().parent / 'normalized_mappings.csv'
OUT_CSV = Path(__file__).resolve().parent / 'normalized_summary.csv'

def main():
    if not IN_CSV.exists():
        print('Input file not found:', IN_CSV)
        return

    groups = {}
    # normalized -> {'count': int, 'sources': Counter, 'raws': Counter}
    with IN_CSV.open(newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            raw, norm, src = row[0].strip(), row[1].strip(), row[2].strip()
            if norm == '':
                continue
            entry = groups.get(norm)
            if entry is None:
                entry = {'count': 0, 'sources': Counter(), 'raws': Counter()}
                groups[norm] = entry
            entry['count'] += 1
            entry['sources'][src] += 1
            entry['raws'][raw] += 1

    # Write summary CSV
    with OUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['normalized', 'total_count', 'sources', 'sample_raws'])
        for norm, entry in sorted(groups.items(), key=lambda kv: (-kv[1]['count'], kv[0])):
            sources_str = ';'.join(f"{s}:{c}" for s, c in entry['sources'].most_common())
            sample_raws = ' | '.join(r for r, _ in entry['raws'].most_common(5))
            writer.writerow([norm, entry['count'], sources_str, sample_raws])

    print('Wrote', OUT_CSV, 'with', len(groups), 'unique normalized values')

    # Print top 20 for quick inspection
    printed = 0
    for norm, entry in sorted(groups.items(), key=lambda kv: (-kv[1]['count'], kv[0]))[:20]:
        print(f"{entry['count']:6d} | {entry['sources']} | {norm[:120]}")
        printed += 1

if __name__ == '__main__':
    main()
