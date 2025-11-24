import sqlite3, json

def main():
    conn = sqlite3.connect('production.db')
    conn.row_factory = sqlite3.Row
    # Find monthly coordinator task tables
    tables = [row['name'] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_tasks_%'")]
    coordinator_ids = set()
    for t in tables:
        try:
            rows = conn.execute(f"SELECT DISTINCT coordinator_id FROM {t} WHERE coordinator_id IS NOT NULL").fetchall()
            for r in rows:
                try:
                    val = r['coordinator_id']
                except Exception:
                    val = r[0]
                if val is not None:
                    coordinator_ids.add(str(val))
        except Exception as e:
            print(f"WARNING: Could not scan table {t}: {e}")

    # Sort IDs: numeric first by value, then non-numeric by string
    ids_sorted = sorted([str(x) for x in coordinator_ids], key=lambda s: (0, int(s)) if s.isdigit() else (1, s))

    results = []
    for cid in ids_sorted:
        u = conn.execute("SELECT user_id, full_name, username FROM users WHERE user_id = ?", (cid,)).fetchone()
        roles = conn.execute(
            "SELECT ur.role_id, r.role_name FROM user_roles ur JOIN roles r ON ur.role_id = r.role_id WHERE ur.user_id = ?",
            (cid,)
        ).fetchall()
        if u:
            role_ids = []
            role_names = []
            for row in roles:
                try:
                    role_ids.append(row['role_id'])
                    role_names.append(row['role_name'])
                except Exception:
                    role_ids.append(row[0])
                    role_names.append(row[1])
            is_coord = any(rid in (36, 37, 39, 40) for rid in role_ids)
            results.append({
                'coordinator_id': cid,
                'user_found': True,
                'full_name': u['full_name'],
                'username': u['username'],
                'role_ids': role_ids,
                'role_names': role_names,
                'is_coordinator_role': is_coord
            })
        else:
            results.append({'coordinator_id': cid, 'user_found': False})

    # Also check for specific expected coordinator names
    check_names = ['Medez, Dianela', 'Soberanis, Jose']
    name_checks = []
    for name in check_names:
        row = conn.execute("SELECT user_id, full_name FROM users WHERE full_name = ?", (name,)).fetchone()
        name_checks.append({
            'name': name,
            'found': bool(row),
            'user_id': (row['user_id'] if row else None)
        })
    conn.close()
    print(json.dumps({
        'tables_scanned': tables,
        'coordinator_ids_found': ids_sorted,
        'validation': results,
        'name_checks': name_checks
    }, indent=2))

if __name__ == '__main__':
    main()