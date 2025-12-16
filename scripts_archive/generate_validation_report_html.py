#!/usr/bin/env python3
import os
import csv
import datetime
import sqlite3
from html import escape

BASE_DIR = os.path.dirname(__file__)
REPORT_DIR = os.path.join(BASE_DIR, 'outputs', 'reports')
OUTPUT_HTML = os.path.join(REPORT_DIR, 'validation_report.html')
PROD_DB = os.path.abspath(os.path.join(BASE_DIR, '..', 'production.db'))
BASELINE_DATE = '2025-09-26'

FILES = [
    ('Provider rows in production missing in staging (recent)', 'provider_rows_missing_in_staging_production_recent.csv'),
    ('Provider rows in staging missing in production (recent)', 'provider_rows_missing_in_production_staging_recent.csv'),
    ('Coordinator rows in production missing in staging (recent)', 'coordinator_rows_missing_in_staging_production_recent.csv'),
    ('Coordinator rows in staging missing in production (recent)', 'coordinator_rows_missing_in_production_staging_recent.csv'),
    ('Provider unmatched samples (staging vs prod)', 'provider_tasks_unmatched_samples.csv'),
    ('Coordinator unmatched samples (staging vs prod)', 'coordinator_tasks_unmatched_samples.csv'),
    ('Tasks without panel', 'tasks_without_panel.csv'),
    ('Panel without tasks', 'panel_without_tasks.csv'),
    ('Two-day audit: Provider prod→staging missing', 'provider_prod_missing_in_staging_two_days.csv'),
    ('Two-day audit: Provider staging→prod missing', 'provider_staging_missing_in_prod_two_days.csv'),
    ('Two-day audit: Provider prod→sheets missing', 'provider_prod_missing_in_sheets_two_days.csv'),
    ('Two-day audit: Provider sheets→prod missing', 'provider_sheets_missing_in_prod_two_days.csv'),
    ('Two-day audit: Coordinator prod→staging missing', 'coordinator_prod_missing_in_staging_two_days.csv'),
    ('Two-day audit: Coordinator staging→prod missing', 'coordinator_staging_missing_in_prod_two_days.csv'),
    ('Two-day audit: Coordinator prod→sheets missing', 'coordinator_prod_missing_in_sheets_two_days.csv'),
    ('Two-day audit: Coordinator sheets→prod missing', 'coordinator_sheets_missing_in_prod_two_days.csv'),
    ('Mapping candidates: Provider codes', 'provider_code_candidates.csv'),
    ('Mapping candidates: Coordinator codes', 'coordinator_code_candidates.csv'),
    ('Curated check: patient_panel non-numeric IDs', 'patient_panel_non_numeric_ids.csv'),
    ('Curated check: assignments non-numeric IDs', 'user_patient_assignments_non_numeric_ids.csv'),
    ('Curated check: panel IDs missing names', 'patient_panel_missing_names_for_ids.csv'),
]

SUMMARY_TXT = os.path.join(REPORT_DIR, 'normalization_linkage_summary.txt')

def read_csv(path, limit=50):
    rows = []
    headers = []
    count = 0
    if not os.path.exists(path):
        return headers, rows, count
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            headers = []
        for i, r in enumerate(reader):
            count += 1
            if i < limit:
                rows.append(r)
    return headers, rows, count

def read_text(path, limit_lines=1000):
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def render_table(title, headers, rows, total_count, csv_name):
    h = []
    h.append('<section class="section">')
    h.append('<h2>' + escape(title) + '</h2>')
    h.append('<div class="meta">Total rows: ' + str(total_count) + ' — Source: ' + escape(csv_name) + '</div>')
    if headers and rows:
        h.append('<div class="table-wrap">')
        h.append('<table>')
        h.append('<thead><tr>' + ''.join('<th>' + escape(x) + '</th>' for x in headers) + '</tr></thead>')
        h.append('<tbody>')
        for r in rows:
            h.append('<tr>' + ''.join('<td>' + escape(x) + '</td>' for x in r) + '</tr>')
        h.append('</tbody>')
        h.append('</table>')
        h.append('</div>')
    else:
        h.append('<div class="empty">No data or file missing</div>')
    h.append('</section>')
    return '\n'.join(h)

def query_count(sql):
    try:
        conn = sqlite3.connect(PROD_DB)
        cur = conn.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception:
        return None

def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sections = []
    for title, fname in FILES:
        path = os.path.join(REPORT_DIR, fname)
        headers, rows, total = read_csv(path)
        sections.append(render_table(title, headers, rows, total, fname))
    summary_block = ''
    summary = read_text(SUMMARY_TXT)
    if summary:
        summary_block = '<pre class="summary">' + escape(summary) + '</pre>'
    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html lang="en">')
    html.append('<head>')
    html.append('<meta charset="utf-8"/>')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1"/>')
    html.append('<title>Validation Report</title>')
    html.append('<style>')
    css = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;padding:20px;background:#f7f8fa;color:#222}
.container{max-width:1200px;margin:0 auto}
h1{font-size:22px;margin:0 0 8px}
.timestamp{color:#666;margin-bottom:20px}
.section{margin:24px 0;padding:16px;background:#fff;border:1px solid #e5e7eb;border-radius:8px}
.table-wrap{overflow:auto}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #e5e7eb;padding:8px;text-align:left;font-size:12px}
thead{background:#f3f4f6}
.meta{color:#444;margin-bottom:8px}
.empty{color:#888;font-style:italic}
.summary{white-space:pre-wrap;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:16px 0}
.card{padding:12px;background:#fff;border:1px solid #e5e7eb;border-radius:8px}
.card h3{margin:0 0 6px;font-size:14px}
.card .num{font-weight:600}
a{color:#0b79d0;text-decoration:none}
a:hover{text-decoration:underline}
"""
    html.append(css)
    html.append('</style>')
    html.append('</head>')
    html.append('<body>')
    html.append('<div class="container">')
    html.append('<h1>Validation Report</h1>')
    html.append('<div class="timestamp">Generated ' + escape(now) + ' — Window: ≥ ' + escape(BASELINE_DATE) + '</div>')

    # Aggregated counts (optional if DB/views available)
    provider_prod_cnt = query_count("SELECT COUNT(*) FROM P_PROVIDER_TASKS_EQUIV WHERE activity_date >= '" + BASELINE_DATE + "'")
    provider_staging_cnt = query_count("SELECT COUNT(*) FROM NORM_STAGING_PROVIDER_TASKS WHERE activity_date >= '" + BASELINE_DATE + "'")
    coord_prod_cnt = query_count("SELECT COUNT(*) FROM P_COORDINATOR_TASKS_EQUIV WHERE activity_date >= '" + BASELINE_DATE + "'")
    coord_staging_cnt = query_count("SELECT COUNT(*) FROM NORM_STAGING_COORDINATOR_TASKS WHERE activity_date >= '" + BASELINE_DATE + "'")

    provider_map_total = query_count("SELECT COUNT(*) FROM provider_code_map")
    provider_map_mapped = query_count("SELECT COUNT(*) FROM provider_code_map WHERE user_id IS NOT NULL")
    coord_map_total = query_count("SELECT COUNT(*) FROM coordinator_code_map")
    coord_map_mapped = query_count("SELECT COUNT(*) FROM coordinator_code_map WHERE user_id IS NOT NULL")

    provider_unmapped_staging = query_count("SELECT COUNT(*) FROM staging_provider_tasks_mapped WHERE activity_date >= '" + BASELINE_DATE + "' AND provider_user_id IS NULL")
    coord_unmapped_staging = query_count("SELECT COUNT(*) FROM staging_coordinator_tasks_mapped WHERE activity_date >= '" + BASELINE_DATE + "' AND coordinator_user_id IS NULL")

    # CSV-based unmatched counts
    counts_map = {}
    for title, fname in FILES:
        path = os.path.join(REPORT_DIR, fname)
        _, _, total = read_csv(path, limit=0)
        counts_map[fname] = total

    cards = []
    def card(label, num):
        return '<div class="card"><h3>' + escape(label) + '</h3><div class="num">' + escape(str(num) if num is not None else 'n/a') + '</div></div>'
    cards.append(card('Provider (production, recent)', provider_prod_cnt))
    cards.append(card('Provider (staging, recent)', provider_staging_cnt))
    cards.append(card('Provider unmatched prod→staging (recent)', counts_map.get('provider_rows_missing_in_staging_production_recent.csv', 0)))
    cards.append(card('Provider unmatched staging→prod (recent)', counts_map.get('provider_rows_missing_in_production_staging_recent.csv', 0)))
    cards.append(card('Provider code map: mapped / total', f"{provider_map_mapped or 0} / {provider_map_total or 0}"))
    cards.append(card('Provider unmapped in staging (recent)', provider_unmapped_staging))
    cards.append(card('Coordinator (production, recent)', coord_prod_cnt))
    cards.append(card('Coordinator (staging, recent)', coord_staging_cnt))
    cards.append(card('Coordinator unmatched prod→staging (recent)', counts_map.get('coordinator_rows_missing_in_staging_production_recent.csv', 0)))
    cards.append(card('Coordinator unmatched staging→prod (recent)', counts_map.get('coordinator_rows_missing_in_production_staging_recent.csv', 0)))
    cards.append(card('Coordinator code map: mapped / total', f"{coord_map_mapped or 0} / {coord_map_total or 0}"))
    cards.append(card('Coordinator unmapped in staging (recent)', coord_unmapped_staging))
    curated_non_numeric_panel = query_count("SELECT COUNT(*) FROM patient_panel WHERE (CAST(provider_id AS TEXT) NOT GLOB '[0-9]*' AND provider_id IS NOT NULL) OR (CAST(coordinator_id AS TEXT) NOT GLOB '[0-9]*' AND coordinator_id IS NOT NULL)")
    curated_non_numeric_assign = query_count("SELECT COUNT(*) FROM user_patient_assignments WHERE (CAST(provider_id AS TEXT) NOT GLOB '[0-9]*' AND provider_id IS NOT NULL) OR (CAST(coordinator_id AS TEXT) NOT GLOB '[0-9]*' AND coordinator_id IS NOT NULL)")
    cards.append(card('Curated: panel non-numeric IDs', curated_non_numeric_panel))
    cards.append(card('Curated: assignments non-numeric IDs', curated_non_numeric_assign))
    html.append('<section class="section"><h2>Summary Counts</h2><div class="grid">' + ''.join(cards) + '</div></section>')

    if summary_block:
        html.append('<section class="section"><h2>Linkage Summary</h2>' + summary_block + '</section>')
    links = []
    for _, fname in FILES:
        p = os.path.join('scripts', 'outputs', 'reports', fname)
        if os.path.exists(os.path.join(REPORT_DIR, fname)):
            links.append('<div class="card"><h3>' + escape(fname) + '</h3><div><a href="' + escape(p) + '">' + escape(p) + '</a></div></div>')
    if links:
        html.append('<section class="section"><h2>CSV Files</h2><div class="grid">' + ''.join(links) + '</div></section>')
    for s in sections:
        html.append(s)
    html.append('</div>')
    html.append('</body>')
    html.append('</html>')
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))

if __name__ == '__main__':
    main()