#!/usr/bin/env python3
"""
WriteAheadLogger - Dual-write redundancy for all user input.

Logs ALL data to TWO places before attempting actual DB save:
1. raw_input_log table (Level 4: Database)
2. JSONL files on disk (Level 5: File System)

If the actual save fails or data is lost, recovery is possible from either source.

Usage:
    from src.utils.write_ahead_logger import log_write_ahead, mark_log_completed, mark_log_failed

    # Before saving to database
    log_id = log_write_ahead(
        user_id=26,
        target_table="coordinator_tasks_2026_01",
        operation="INSERT",
        data_json={"patient_id": "123", "task_date": "2026-01-22", "notes": "..."},
        source_system="COORDINATOR_DASHBOARD"
    )

    # Attempt actual save
    try:
        save_to_database(data)
        mark_log_completed(log_id, target_record_id=123)
    except Exception as e:
        mark_log_failed(log_id, error_message=str(e))
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from src.database import get_db_connection
from src.utils.file_log_manager import get_file_log_manager


def ensure_raw_input_log_table(conn: sqlite3.Connection) -> None:
    """
    Ensure the raw_input_log table exists.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='raw_input_log'"
    )
    if cursor.fetchone():
        return

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_input_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            target_table TEXT NOT NULL,
            target_record_id INTEGER,
            operation TEXT NOT NULL,
            data_json TEXT NOT NULL,
            source_system TEXT NOT NULL,
            session_id TEXT,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            recovered_from_log_id INTEGER,
            log_file_ref TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_raw_input_log_user ON raw_input_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_input_log_timestamp ON raw_input_log(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_raw_input_log_status ON raw_input_log(status)",
        "CREATE INDEX IF NOT EXISTS idx_raw_input_log_target ON raw_input_log(target_table, target_record_id)",
        "CREATE INDEX IF NOT EXISTS idx_raw_input_log_pending ON raw_input_log(status, timestamp) WHERE status IN ('pending', 'failed')",
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    conn.commit()


def log_write_ahead(
    user_id: int,
    target_table: str,
    operation: str,
    data_json: Dict[str, Any],
    source_system: str,
    session_id: Optional[str] = None,
) -> Optional[int]:
    """
    Log input data to BOTH raw_input_log table AND JSONL file before actual save.

    This is the write-ahead log - it captures all data before any attempt to write
    to the target table. If the target write fails, data is safe here.

    Args:
        user_id: User performing the operation.
        target_table: Target table name (e.g., coordinator_tasks_2026_01).
        operation: Operation type (INSERT, UPDATE, DELETE).
        data_json: Dictionary of all column names and values.
        source_system: Where this came from (COORDINATOR_DASHBOARD, WORKFLOW_MODULE, etc.).
        session_id: Optional Streamlit session ID.

    Returns:
        log_id if successful, None if logging failed.
    """
    conn = get_db_connection()
    try:
        ensure_raw_input_log_table(conn)
        cursor = conn.cursor()

        # Convert data dict to JSON string
        data_json_str = json.dumps(data_json, ensure_ascii=False, default=str)

        # Insert into raw_input_log table
        cursor.execute("""
            INSERT INTO raw_input_log (
                timestamp, user_id, target_table, operation,
                data_json, source_system, session_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            target_table,
            operation,
            data_json_str,
            source_system,
            session_id
        ))

        conn.commit()
        log_id = cursor.lastrowid

        # ALSO write to JSONL file (Level 5: File System redundancy)
        try:
            file_log = get_file_log_manager()
            log_file_path = file_log.write_log({
                "log_id": log_id,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "target_table": target_table,
                "operation": operation,
                "data_json": data_json_str,
                "source_system": source_system,
                "session_id": session_id,
                "status": "pending"
            })

            # Update log with file reference
            cursor.execute(
                "UPDATE raw_input_log SET log_file_ref = ? WHERE log_id = ?",
                (log_file_path, log_id)
            )
            conn.commit()

        except Exception as e:
            # File logging failed but DB succeeded - still OK
            print(f"Warning: File logging failed: {e}")

        return log_id

    except Exception as e:
        print(f"Error in log_write_ahead: {e}")
        return None
    finally:
        conn.close()


def mark_log_completed(log_id: int, target_record_id: Optional[int] = None) -> None:
    """
    Mark a log entry as successfully completed.

    Call this after the actual database save succeeds.

    Args:
        log_id: The log entry ID.
        target_record_id: The ID of the record that was created/updated.
    """
    if log_id is None:
        return

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        if target_record_id:
            cursor.execute("""
                UPDATE raw_input_log
                SET status = 'completed', target_record_id = ?
                WHERE log_id = ?
            """, (target_record_id, log_id))
        else:
            cursor.execute("""
                UPDATE raw_input_log
                SET status = 'completed'
                WHERE log_id = ?
            """, (log_id,))

        conn.commit()
    finally:
        conn.close()


def mark_log_failed(log_id: int, error_message: str) -> None:
    """
    Mark a log entry as failed.

    Call this when the actual database save fails.

    Args:
        log_id: The log entry ID.
        error_message: Error message describing the failure.
    """
    if log_id is None:
        return

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE raw_input_log
            SET status = 'failed', error_message = ?
            WHERE log_id = ?
        """, (error_message, log_id))
        conn.commit()
    finally:
        conn.close()


def get_failed_logs(user_id: Optional[int] = None, hours: int = 24) -> list[Dict[str, Any]]:
    """
    Get failed or pending log entries for recovery.

    Args:
        user_id: Optional user filter.
        hours: How many hours back to look.

    Returns:
        List of log entries that need recovery.
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""
                SELECT * FROM raw_input_log
                WHERE user_id = ?
                AND status IN ('pending', 'failed')
                AND timestamp > datetime('now', ? || ' hours')
                ORDER BY timestamp DESC
            """, (user_id, -hours))
        else:
            cursor.execute("""
                SELECT * FROM raw_input_log
                WHERE status IN ('pending', 'failed')
                AND timestamp > datetime('now', ? || ' hours')
                ORDER BY timestamp DESC
            """, (-hours,))

        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def recover_from_log(log_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the data for a specific log entry for recovery.

    Args:
        log_id: The log entry ID.

    Returns:
        Dictionary with log data including parsed data_json.
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM raw_input_log WHERE log_id = ?", (log_id,))
        row = cursor.fetchone()

        if not row:
            return None

        result = dict(row)
        # Parse the JSON data
        try:
            result["data"] = json.loads(result["data_json"])
        except json.JSONDecodeError:
            result["data"] = {}

        return result
    finally:
        conn.close()


# ============================================================================
# Convenience decorator for automatic write-ahead logging
# ============================================================================

def with_write_ahead_log(
    target_table: str,
    operation: str = "INSERT",
    source_system: str = "DASHBOARD"
):
    """
    Decorator that automatically adds write-ahead logging to a function.

    The decorated function should:
    - Accept user_id as first argument (or have it in kwargs)
    - Return the saved record ID on success

    Usage:
        @with_write_ahead_log(target_table="coordinator_tasks_2026_01", source_system="COORDINATOR_DASHBOARD")
        def save_coordinator_task(user_id, data):
            # ... save logic ...
            return record_id
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get user_id from args or kwargs
            user_id = kwargs.get('user_id') or (args[0] if args else None)

            if user_id is None:
                return func(*args, **kwargs)

            # Extract data for logging (all kwargs except user_id)
            data_to_log = {k: v for k, v in kwargs.items() if k != 'user_id'}

            # Write-ahead log
            log_id = log_write_ahead(
                user_id=user_id,
                target_table=target_table,
                operation=operation,
                data_json=data_to_log,
                source_system=source_system
            )

            # Call the actual function
            try:
                result = func(*args, **kwargs)
                mark_log_completed(log_id, target_record_id=result)
                return result
            except Exception as e:
                mark_log_failed(log_id, str(e))
                raise

        return wrapper
    return decorator
