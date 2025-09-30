"""
Compact, minimalistic timer component
"""

import streamlit as st
from datetime import datetime

def simple_timestamp_timer(timer_key):
    """
    Compact timer with Start/Stop, Reset, and time display
    
    Args:
        timer_key: Unique identifier for this timer
    
    Returns:
        int: Final duration in seconds (0 if not completed)
    """
    
    # Initialize session state
    start_key = f"{timer_key}_start"
    stop_key = f"{timer_key}_stop"
    running_key = f"{timer_key}_running"
    
    if start_key not in st.session_state:
        st.session_state[start_key] = None
        st.session_state[stop_key] = None
        st.session_state[running_key] = False
    
    # Get current state
    start_time = st.session_state[start_key]
    stop_time = st.session_state[stop_key]
    is_running = st.session_state[running_key]
    
    # Calculate duration
    if is_running and start_time:
        duration = int((datetime.now() - start_time).total_seconds())
    elif stop_time and start_time:
        duration = int((stop_time - start_time).total_seconds())
    else:
        duration = 0
    
    # Compact display
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Duration display
        minutes, seconds = divmod(duration, 60)
        st.metric("Duration", f"{minutes:02d}:{seconds:02d}")
    
    with col2:
        # Start/Stop button
        if is_running:
            if st.button("Stop", key=f"stop_{timer_key}", type="secondary"):
                st.session_state[stop_key] = datetime.now()
                st.session_state[running_key] = False
                st.rerun()
        else:
            if st.button("Start", key=f"start_{timer_key}", type="primary"):
                st.session_state[start_key] = datetime.now()
                st.session_state[stop_key] = None
                st.session_state[running_key] = True
                st.rerun()
    
    with col3:
        # Reset button
        if st.button("Reset", key=f"reset_{timer_key}"):
            st.session_state[start_key] = None
            st.session_state[stop_key] = None
            st.session_state[running_key] = False
            st.rerun()
    
    # Time fields (compact display)
    if start_time or stop_time:
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            st.text_input("Start Time", 
                         value=start_time.strftime("%H:%M:%S") if start_time else "", 
                         disabled=True, key=f"start_display_{timer_key}")
        with time_col2:
            st.text_input("Stop Time", 
                         value=stop_time.strftime("%H:%M:%S") if stop_time else "", 
                         disabled=True, key=f"stop_display_{timer_key}")
    
    # Return final duration for database storage
    if start_time and stop_time and not is_running:
        return int((stop_time - start_time).total_seconds())
    else:
        return 0