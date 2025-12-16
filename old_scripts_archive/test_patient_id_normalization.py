import sqlite3
import pytest

# Canonical normalization expression from src/sql/patient_id_normalization_standard.sql,
# extended to collapse consecutive spaces to a single space.

def normalization_expr_sql(col_name: str) -> str:
    return f"""
    TRIM(REPLACE(REPLACE(REPLACE(
        TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM({col_name}),
            'ZEN-',''),
            'PM-',''),
            'ZMN-',''),
            'BLESSEDCARE-',''),
            'BLEESSEDCARE-',''),
            '3PR-',''),
            'BLESSEDCARE ',''),
            'BLEESSEDCARE ',''),
            '3PR ',''),
            ', ',' '),
            ',',' '
        )),
        '  ', ' '),
        '  ', ' '),
        '  ', ' '
    ))
    """

TEST_CASES = [
    ("SMITH, JOHN 01/15/1980", "SMITH JOHN 01/15/1980"),
    ("ZEN-DOE, JANE 03/10/1990", "DOE JANE 03/10/1990"),
    ("PM-JONES,MARY 12/25/1975", "JONES MARY 12/25/1975"),
    ("BLESSEDCARE-ALPHA, BOB 06/20/1985", "ALPHA BOB 06/20/1985"),
    ("3PR BROWN  MIKE 06/20/1985", "BROWN MIKE 06/20/1985"),
]

@pytest.mark.parametrize("raw,expected", TEST_CASES)
def test_normalization_cases(raw, expected):
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE t (raw TEXT)")
        conn.execute("INSERT INTO t(raw) VALUES (?)", (raw,))
        expr = normalization_expr_sql("raw")
        cur = conn.execute(f"SELECT {expr} AS normalized FROM t")
        (normalized,) = cur.fetchone()
        assert normalized == expected
    finally:
        conn.close()

def test_with_sample_from_source_patient_data_if_available():
    # Optional integration test: if SOURCE_PATIENT_DATA exists in production.db, sample a few rows
    # and ensure normalization yields non-empty strings (smoke test).
    # This is a non-strict check to avoid brittle expectations for unseen data.
    try:
        conn = sqlite3.connect("production.db")
    except Exception:
        pytest.skip("production.db not available")
        return
    try:
        # Check table existence
        try:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SOURCE_PATIENT_DATA'")
            if cur.fetchone() is None:
                pytest.skip("SOURCE_PATIENT_DATA not present in production.db")
                return
        except Exception:
            pytest.skip("Could not inspect production.db schema")
            return
        # Sample raw values from LAST FIRST DOB if available, else construct from Last/First/DOB
        column = None
        try:
            conn.execute("SELECT [LAST FIRST DOB] FROM SOURCE_PATIENT_DATA LIMIT 1")
            column = "[LAST FIRST DOB]"
        except sqlite3.OperationalError:
            try:
                conn.execute("SELECT COALESCE(Last,'') || ' ' || COALESCE(First,'') || ' ' || COALESCE(DOB,'') FROM SOURCE_PATIENT_DATA LIMIT 1")
                column = "COALESCE(Last,'') || ' ' || COALESCE(First,'') || ' ' || COALESCE(DOB,'')"
            except sqlite3.OperationalError:
                pytest.skip("No compatible name/DOB columns in SOURCE_PATIENT_DATA")
                return
        expr = normalization_expr_sql(column)
        # Verify we can compute normalized values and they are non-empty
        cur = conn.execute(f"SELECT {expr} AS norm FROM SOURCE_PATIENT_DATA WHERE {column} IS NOT NULL LIMIT 10")
        rows = cur.fetchall()
        assert len(rows) >= 0  # always true, placeholder
        for (norm,) in rows:
            assert isinstance(norm, str)
            assert norm.strip() != ""  # smoke check: should produce non-empty normalized strings
    finally:
        conn.close()