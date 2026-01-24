#!/usr/bin/env python3
"""
FileLogManager - Level 5: File System redundancy for raw input logs.

Writes JSONL log files outside the database for disaster recovery.
If the database is corrupted or lost, data can be recovered from these files.

JSONL format: One JSON object per line
{"log_id": 1, "timestamp": "2026-01-22T10:30:00", "user_id": 26, "target_table": "coordinator_tasks_2026_01", "data_json": "{...}"}

Directory structure:
    data_logs/
        raw_input/
            2026/
                2026-01/
                    2026-01-22.jsonl
                    2026-01-23.jsonl
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class FileLogManager:
    """Manages JSONL log files for raw input data outside the database."""

    def __init__(self, base_dir: str = "data_logs/raw_input"):
        """
        Initialize the FileLogManager.

        Args:
            base_dir: Base directory for log files (default: data_logs/raw_input)
        """
        self.base_dir = Path(base_dir)

    def _get_log_file_path(self, date: Optional[datetime] = None) -> Path:
        """
        Get the log file path for a given date.

        Structure: data_logs/raw_input/YYYY/YYYY-MM/YYYY-MM-DD.jsonl

        Args:
            date: Date for the log file. Defaults to today.

        Returns:
            Path to the log file.
        """
        if date is None:
            date = datetime.now()

        year = date.strftime("%Y")
        month = date.strftime("%m")
        day = date.strftime("%Y-%m-%d")

        log_dir = self.base_dir / year / f"{year}-{month}"
        log_dir.mkdir(parents=True, exist_ok=True)

        return log_dir / f"{day}.jsonl"

    def write_log(self, log_entry: Dict[str, Any]) -> str:
        """
        Write a log entry to today's JSONL file.

        Args:
            log_entry: Dictionary containing log data.
                       Must include: log_id, timestamp, user_id, target_table, data_json

        Returns:
            Path to the log file that was written to.
        """
        log_file = self._get_log_file_path()

        # Ensure the entry has required fields
        required_fields = ["log_id", "timestamp", "user_id", "target_table", "data_json"]
        for field in required_fields:
            if field not in log_entry:
                raise ValueError(f"Missing required field: {field}")

        # Add file write timestamp
        log_entry["file_write_timestamp"] = datetime.now().isoformat()

        # Write as JSONL (one JSON per line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return str(log_file)

    def write_logs_batch(self, log_entries: list[Dict[str, Any]]) -> str:
        """
        Write multiple log entries in a single operation.

        Args:
            log_entries: List of log entry dictionaries.

        Returns:
            Path to the log file that was written to.
        """
        log_file = self._get_log_file_path()

        with open(log_file, "a", encoding="utf-8") as f:
            for entry in log_entries:
                entry["file_write_timestamp"] = datetime.now().isoformat()
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return str(log_file)

    def read_log_file(self, date: Optional[datetime] = None) -> list[Dict[str, Any]]:
        """
        Read all log entries from a specific date's file.

        Args:
            date: Date to read. Defaults to today.

        Returns:
            List of log entry dictionaries.
        """
        log_file = self._get_log_file_path(date)

        if not log_file.exists():
            return []

        entries = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines

        return entries

    def get_recent_logs(self, days: int = 7) -> list[Dict[str, Any]]:
        """
        Read log entries from the last N days.

        Args:
            days: Number of days to look back.

        Returns:
            List of log entry dictionaries.
        """
        entries = []
        for i in range(days):
            date = datetime.now()
            entries.extend(self.read_log_file(date))

        # Sort by timestamp
        entries.sort(key=lambda x: x.get("timestamp", ""))

        return entries

    def get_logs_for_user(self, user_id: int, days: int = 30) -> list[Dict[str, Any]]:
        """
        Get all log entries for a specific user.

        Args:
            user_id: User ID to filter by.
            days: Number of days to look back.

        Returns:
            List of log entry dictionaries for the user.
        """
        all_entries = self.get_recent_logs(days)
        return [e for e in all_entries if e.get("user_id") == user_id]

    def get_logs_for_table(self, target_table: str, days: int = 30) -> list[Dict[str, Any]]:
        """
        Get all log entries for a specific target table.

        Args:
            target_table: Table name to filter by.
            days: Number of days to look back.

        Returns:
            List of log entry dictionaries for the table.
        """
        all_entries = self.get_recent_logs(days)
        return [e for e in all_entries if e.get("target_table") == target_table]

    def recover_from_logs(self, target_table: Optional[str] = None, days: int = 30) -> list[Dict[str, Any]]:
        """
        Get recoverable log entries (pending or failed status).

        Args:
            target_table: Optional table filter.
            days: Number of days to look back.

        Returns:
            List of recoverable log entries.
        """
        all_entries = self.get_recent_logs(days)

        recoverable = []
        for entry in all_entries:
            # Filter by table if specified
            if target_table and entry.get("target_table") != target_table:
                continue

            # Only return pending or failed entries
            status = entry.get("status", "pending")
            if status in ("pending", "failed"):
                recoverable.append(entry)

        return recoverable

    def get_file_stats(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get statistics about a log file.

        Args:
            date: Date to check. Defaults to today.

        Returns:
            Dictionary with file stats.
        """
        log_file = self._get_log_file_path(date)

        if not log_file.exists():
            return {
                "file_path": str(log_file),
                "exists": False,
                "entries": 0,
                "size_bytes": 0,
            }

        entries = self.read_log_file(date)
        file_size = log_file.stat().st_size if log_file.exists() else 0

        return {
            "file_path": str(log_file),
            "exists": True,
            "entries": len(entries),
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
        }


# Singleton instance for easy import
_file_log_manager = None


def get_file_log_manager() -> FileLogManager:
    """Get the singleton FileLogManager instance."""
    global _file_log_manager
    if _file_log_manager is None:
        _file_log_manager = FileLogManager()
    return _file_log_manager
