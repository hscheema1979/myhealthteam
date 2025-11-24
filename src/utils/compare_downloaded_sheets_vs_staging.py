import os
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

STAGING_DB = Path("D:/Git/myhealthteam2/Streamlit/scripts/sheets_data.db")
PROVIDER_DIR = Path("D:/Git/myhealthteam2/Streamlit/downloads/monthly_PSL")
COORDINATOR_DIR = Path("D:/Git/myhealthteam2/Streamlit/downloads/monthly_CM")
REPORTS_DIR = Path("D:/Git/myhealthteam2/Streamlit/outputs/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Use less strict keys to allow for service/type naming differences
KEYS_PROVIDER = ["Prov", "Patient Last, First DOB", "DOS"]
KEYS_COORD = ["Staff", "Pt Name", "Date Only"]


def _read_all_csvs(csv_dir: Path) -> pd.DataFrame:
    files = sorted([p for p in csv_dir.glob("*.csv")])
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, dtype=str)
            # Drop unnamed/index columns if present
            drop_cols = [c for c in df.columns if c.startswith("Unnamed") or c == "1" or c == "index"]
            if drop_cols:
                df = df.drop(columns=drop_cols)
            frames.append(df)
        except Exception as e:
            print(f"Failed reading {f}: {e}")
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


def _normalize_date(val: str) -> str:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    # Already in MM/DD/YY
    if "/" in s:
        # Some have trailing spaces or missing leading zeros; try parse
        for fmt in ("%m/%d/%y", "%m/%d/%Y", "%m/%d/%y "):
            try:
                dt = datetime.strptime(s.strip(), fmt)
                return dt.strftime("%m/%d/%y")
            except Exception:
                continue
        # If parsing fails, return upper stripped
        return s.upper()
    # Likely ISO YYYY-MM-DD
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%m/%d/%y")
    except Exception:
        return s.upper()


def _normalize_cols(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    # Ensure columns exist; create empty if missing
    for c in cols:
        if c not in df.columns:
            df[c] = None
    # Keep only target cols
    df = df[cols].copy()
    # Strip whitespace, unify None, uppercase for robust matching; normalize dates
    for c in cols:
        if c in ("DOS", "Date Only"):
            df[c] = df[c].apply(_normalize_date)
        else:
            df[c] = df[c].astype(str).str.strip().str.upper().replace({"NAN": None, "NONE": None})
    # Drop rows with any null keys
    return df.dropna(how="any")


def _load_db_table(conn: sqlite3.Connection, table: str, cols: list) -> pd.DataFrame:
    q_cols = ",".join([f'"{c}"' for c in cols])
    q = f"SELECT {q_cols} FROM {table}"
    df = pd.read_sql_query(q, conn)
    # Normalize whitespace and dates
    for c in cols:
        if c in ("DOS", "Date Only"):
            df[c] = df[c].apply(_normalize_date)
        else:
            df[c] = df[c].astype(str).str.strip().str.upper().replace({"NAN": None, "NONE": None})
    return df.dropna(how="any")


def _compare_sets(left: pd.DataFrame, right: pd.DataFrame, keys: list):
    left_dedup = left.drop_duplicates(subset=keys)
    right_dedup = right.drop_duplicates(subset=keys)
    merged = left_dedup.merge(right_dedup, on=keys, how="outer", indicator=True)
    only_left = merged[merged["_merge"] == "left_only"][keys]
    only_right = merged[merged["_merge"] == "right_only"][keys]
    both = merged[merged["_merge"] == "both"][keys]
    return only_left, only_right, both


def main():
    print("=== Comparing downloaded sheets CSVs vs staging sheets_data.db ===")
    print(f"Staging DB: {STAGING_DB}")
    if not STAGING_DB.exists() or STAGING_DB.stat().st_size == 0:
        print("ERROR: Staging DB not found or empty. Expected at scripts/sheets_data.db")
        return 2

    conn = sqlite3.connect(str(STAGING_DB))

    # Provider tasks
    print("\n-- Provider tasks --")
    provider_csv = _read_all_csvs(PROVIDER_DIR)
    if provider_csv.empty:
        print(f"No provider CSVs found in {PROVIDER_DIR}")
    provider_csv_norm = _normalize_cols(provider_csv, KEYS_PROVIDER)

    provider_db = _load_db_table(conn, "SOURCE_PROVIDER_TASKS_HISTORY", KEYS_PROVIDER)

    p_left, p_right, p_both = _compare_sets(provider_csv_norm, provider_db, KEYS_PROVIDER)

    p_left_path = REPORTS_DIR / "provider_csv_only_rows_keys.csv"
    p_right_path = REPORTS_DIR / "provider_db_only_rows_keys.csv"
    p_both_path = REPORTS_DIR / "provider_matching_rows_keys_sample.csv"

    p_left.to_csv(p_left_path, index=False)
    p_right.to_csv(p_right_path, index=False)
    p_both.head(200).to_csv(p_both_path, index=False)

    print(f"Provider comparison (by keys {KEYS_PROVIDER}): CSV-only={len(p_left)}, DB-only={len(p_right)}, Matches(sample)={len(p_both)}")
    print(f"  -> {p_left_path}")
    print(f"  -> {p_right_path}")
    print(f"  -> {p_both_path}")

    # Coordinator tasks
    print("\n-- Coordinator tasks --")
    coord_csv = _read_all_csvs(COORDINATOR_DIR)
    if coord_csv.empty:
        print(f"No coordinator CSVs found in {COORDINATOR_DIR}")
    coord_csv_norm = _normalize_cols(coord_csv, KEYS_COORD)

    coord_db = _load_db_table(conn, "source_coordinator_tasks_history", KEYS_COORD)

    c_left, c_right, c_both = _compare_sets(coord_csv_norm, coord_db, KEYS_COORD)

    c_left_path = REPORTS_DIR / "coordinator_csv_only_rows_keys.csv"
    c_right_path = REPORTS_DIR / "coordinator_db_only_rows_keys.csv"
    c_both_path = REPORTS_DIR / "coordinator_matching_rows_keys_sample.csv"

    c_left.to_csv(c_left_path, index=False)
    c_right.to_csv(c_right_path, index=False)
    c_both.head(200).to_csv(c_both_path, index=False)

    print(f"Coordinator comparison (by keys {KEYS_COORD}): CSV-only={len(c_left)}, DB-only={len(c_right)}, Matches(sample)={len(c_both)}")
    print(f"  -> {c_left_path}")
    print(f"  -> {c_right_path}")
    print(f"  -> {c_both_path}")

    # Patient names coverage across both datasets
    print("\n-- Patient names coverage --")
    prov_csv_names = set(provider_csv_norm["Patient Last, First DOB"].dropna().tolist())
    prov_db_names = set(provider_db["Patient Last, First DOB"].dropna().tolist())
    coord_csv_names = set(coord_csv_norm["Pt Name"].dropna().tolist())
    coord_db_names = set(coord_db["Pt Name"].dropna().tolist())

    csv_union = prov_csv_names.union(coord_csv_names)
    db_union = prov_db_names.union(coord_db_names)

    only_csv_names = sorted(csv_union - db_union)
    only_db_names = sorted(db_union - csv_union)

    pd.DataFrame({"patient_name_csv_only": only_csv_names}).to_csv(REPORTS_DIR / "patient_names_csv_only.csv", index=False)
    pd.DataFrame({"patient_name_db_only": only_db_names}).to_csv(REPORTS_DIR / "patient_names_db_only.csv", index=False)

    print(f"Patient names differences: CSV-only={len(only_csv_names)}, DB-only={len(only_db_names)}")
    print(f"Reports saved under {REPORTS_DIR}")

    conn.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())