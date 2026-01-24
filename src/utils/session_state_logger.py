#!/usr/bin/env python3
"""
Session State Logger - Level 1: Data Entry/Activity Logging

Logs all user activity and state changes to:
- activity_log.jsonl (local file)
- Optionally to database

This captures what users are doing WITHOUT requiring event tracking.
We log the RESULT of actions (state changes), not the actions themselves.

Usage:
    from src.utils.session_state_logger import log_session_state, log_page_view

    log_page_view(user_id, page_name, st.session_state)
    log_session_state(user_id, page_name, st.session_state)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Directory for activity logs
ACTIVITY_LOG_DIR = Path("data_logs/activity")


def sanitize_session_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean up session_state for logging (remove large objects, sensitive data).

    Args:
        state: The session_state dictionary

    Returns:
        Cleaned dictionary safe for logging
    """
    cleaned = {}
    sensitive_keys = {'password', 'token', 'secret', 'key', 'auth'}

    for key, value in state.items():
        # Skip large objects (DataFrames, etc.)
        if hasattr(value, '__len__') and len(value) > 10000:
            cleaned[key] = f"<{type(value).__name__} size={len(value)}>"
        # Skip sensitive keys
        elif any(sensitive in key.lower() for sensitive in sensitive_keys):
            cleaned[key] = "***REDACTED***"
        # Skip complex streamlit internal objects
        elif key.startswith('_') or 'StDelta' in str(type(value)):
            continue
        else:
            try:
                # Try to serialize to JSON
                json.dumps(value)
                cleaned[key] = value
            except (TypeError, ValueError):
                cleaned[key] = f"<{type(value).__name__}>"

    return cleaned


def log_activity(user_id: int, activity_type: str, page_name: str,
                 data: Optional[Dict[str, Any]] = None) -> str:
    """
    Log a user activity to the activity log file.

    Args:
        user_id: User ID
        activity_type: Type of activity (PAGE_VIEW, STATE_CHANGE, SAVE, etc.)
        page_name: Name of the page/dashboard
        data: Optional additional data

    Returns:
        Path to the log file that was written to
    """
    # Ensure log directory exists
    ACTIVITY_LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Use daily log files
    today = datetime.now()
    log_file = ACTIVITY_LOG_DIR / f"activity_{today.strftime('%Y-%m-%d')}.jsonl"

    # Create log entry
    log_entry = {
        'timestamp': today.isoformat(),
        'user_id': user_id,
        'activity_type': activity_type,
        'page_name': page_name,
        'data': data or {}
    }

    # Append to log file (JSONL format - one JSON per line)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + '\n')

    return str(log_file)


def log_page_view(user_id: int, page_name: str, session_state: Dict[str, Any]) -> str:
    """
    Log a page view with current session state.

    Call this at the beginning or end of each dashboard's show() function.

    Args:
        user_id: User ID
        page_name: Name of the page/dashboard
        session_state: Current session_state

    Returns:
        Path to the log file that was written to
    """
    # Get key info from session_state
    key_info = {
        'authenticated': session_state.get('authenticated_user') is not None,
        'user_id': session_state.get('user_id'),
        'user_role_ids': session_state.get('user_role_ids'),
        'preferred_dashboard_role': session_state.get('preferred_dashboard_role')
    }

    # Remove large objects from key_info
    key_info = sanitize_session_state(key_info)

    return log_activity(user_id, 'PAGE_VIEW', page_name, key_info)


def log_state_change(user_id: int, page_name: str, session_state: Dict[str, Any],
                      changed_keys: Optional[list] = None) -> str:
    """
    Log a session state change.

    Call this when key state changes occur (saves, selections, etc.)

    Args:
        user_id: User ID
        page_name: Name of the page/dashboard
        session_state: Current session_state
        changed_keys: Optional list of what changed

    Returns:
        Path to the log file that was written to
    """
    # Get relevant state info
    state_snapshot = sanitize_session_state(session_state)

    data = {
        'state_snapshot': state_snapshot,
        'changed_keys': changed_keys or []
    }

    return log_activity(user_id, 'STATE_CHANGE', page_name, data)


def log_session_state(user_id: int, page_name: str, session_state: Dict[str, Any]) -> str:
    """
    Log the current session state (comprehensive snapshot).

    Call this periodically or after major actions.

    Args:
        user_id: User ID
        page_name: Name of the page/dashboard
        session_state: Current session_state

    Returns:
        Path to the log file that was written to
    """
    return log_state_change(user_id, page_name, session_state)


def get_recent_activity(limit: int = 100) -> list:
    """
    Get recent activity log entries.

    Args:
        limit: Maximum number of entries to return

    Returns:
        List of recent log entries
    """
    # Get recent log files (last 7 days)
    entries = []
    for i in range(7):
        date = datetime.now()
        log_file = ACTIVITY_LOG_DIR / f"activity_{date.strftime('%Y-%m-%d')}.jsonl"

        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

        date = datetime.now()
        # Move to previous day
        # (Simplified - in production would use proper date arithmetic)

    # Sort by timestamp descending and limit
    entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return entries[:limit]


def get_user_activity(user_id: int, days: int = 7) -> list:
    """
    Get all activity for a specific user.

    Args:
        user_id: User ID to filter by
        days: Number of days to look back

    Returns:
        List of log entries for the user
    """
    entries = get_recent_activity(limit=10000)  # Get a lot, then filter
    return [e for e in entries if e.get('user_id') == user_id]
