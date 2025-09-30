"""
Real-time timer component for Streamlit applications
Uses JavaScript for client-side updates to avoid server overhead
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

def javascript_timer(timer_key, is_running=False, start_time=None, elapsed_seconds=0):
    """
    Create a JavaScript-based timer that updates in real-time
    
    Args:
        timer_key: Unique identifier for this timer
        is_running: Whether the timer is currently running
        start_time: When the timer was started (pandas Timestamp)
        elapsed_seconds: Previously elapsed time (for paused timers)
    
    Returns:
        None (displays timer in Streamlit)
    """
    
    # Convert start_time to JavaScript timestamp if provided
    js_start_time = "null"
    if start_time and is_running:
        # JavaScript timestamp is in milliseconds
        js_start_time = str(int(start_time.timestamp() * 1000))
    
    # Calculate initial display time
    initial_seconds = elapsed_seconds
    if is_running and start_time:
        current_elapsed = int((pd.Timestamp.now() - start_time).total_seconds())
        initial_seconds = max(elapsed_seconds, current_elapsed)
    
    timer_html = f"""
    <div style="display: flex; align-items: center; gap: 10px;">
        <div id="timer-display-{timer_key}" style="
            font-family: 'Courier New', monospace; 
            font-size: 16px; 
            font-weight: bold; 
            color: {'#28a745' if is_running else '#6c757d'}; 
            background: {'#f8f9fa' if not is_running else '#e8f5e9'};
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid {'#28a745' if is_running else '#dee2e6'};
            min-width: 60px;
            text-align: center;
        ">
            00:00
        </div>
        <div style="font-size: 14px; color: #6c757d;">
            {'Running' if is_running else 'Paused'}
        </div>
    </div>
    
    <script>
    (function() {{
        const timerId = '{timer_key}';
        const isRunning = {str(is_running).lower()};
        const startTime = {js_start_time};
        const initialSeconds = {initial_seconds};
        
        let currentSeconds = initialSeconds;
        
        function updateDisplay() {{
            const display = document.getElementById('timer-display-' + timerId);
            if (!display) return;
            
            if (isRunning && startTime) {{
                const now = new Date().getTime();
                const elapsedMs = now - startTime;
                currentSeconds = Math.floor(elapsedMs / 1000);
            }} else {{
                currentSeconds = initialSeconds;
            }}
            
            const minutes = Math.floor(Math.max(0, currentSeconds) / 60);
            const seconds = Math.max(0, currentSeconds) % 60;
            display.textContent = 
                String(minutes).padStart(2, '0') + ':' + 
                String(seconds).padStart(2, '0');
        }}
        
        // Update immediately
        updateDisplay();
        
        // Update every second if running
        if (isRunning) {{
            const interval = setInterval(function() {{
                const display = document.getElementById('timer-display-' + timerId);
                if (!display) {{
                    clearInterval(interval);
                    return;
                }}
                updateDisplay();
            }}, 1000);
        }}
    }})();
    </script>
    """
    
    return components.html(timer_html, height=40)

def simple_timer_controls(timer_key):
    """
    Create start/stop controls for a timer using start/stop timestamps
    
    Args:
        timer_key: Unique identifier for this timer
    
    Returns:
        tuple: (is_running, elapsed_seconds, start_time, stop_time) - current timer state
    """
    
    # Initialize session state
    if f"{timer_key}_running" not in st.session_state:
        st.session_state[f"{timer_key}_running"] = False
        st.session_state[f"{timer_key}_start_time"] = None
        st.session_state[f"{timer_key}_stop_time"] = None
        st.session_state[f"{timer_key}_total_duration"] = 0
    
    # Get current state
    is_running = st.session_state[f"{timer_key}_running"]
    start_time = st.session_state[f"{timer_key}_start_time"]
    stop_time = st.session_state[f"{timer_key}_stop_time"]
    total_duration = st.session_state[f"{timer_key}_total_duration"]
    
    # Create control buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if is_running:
            if st.button("Stop", key=f"stop_{timer_key}", type="secondary"):
                # Record stop time and calculate duration
                stop_timestamp = pd.Timestamp.now()
                st.session_state[f"{timer_key}_stop_time"] = stop_timestamp
                st.session_state[f"{timer_key}_running"] = False
                
                # Calculate total duration from start to stop
                if start_time:
                    duration = int((stop_timestamp - start_time).total_seconds())
                    st.session_state[f"{timer_key}_total_duration"] = duration
                
                st.rerun()
        else:
            if st.button("Start", key=f"start_{timer_key}", type="primary"):
                # Record start time
                st.session_state[f"{timer_key}_start_time"] = pd.Timestamp.now()
                st.session_state[f"{timer_key}_running"] = True
                st.session_state[f"{timer_key}_stop_time"] = None  # Clear previous stop time
                st.rerun()
    
    with col2:
        if st.button("Reset", key=f"reset_{timer_key}"):
            st.session_state[f"{timer_key}_running"] = False
            st.session_state[f"{timer_key}_start_time"] = None
            st.session_state[f"{timer_key}_stop_time"] = None
            st.session_state[f"{timer_key}_total_duration"] = 0
            st.rerun()
    
    # Calculate current elapsed time for display
    if is_running and start_time:
        # While running, show live elapsed time
        current_elapsed = int((pd.Timestamp.now() - start_time).total_seconds())
    elif stop_time and start_time:
        # After stopping, show the final duration
        current_elapsed = total_duration
    else:
        # Not started or reset
        current_elapsed = 0
    
    # Show timer info for debugging
    with col3:
        if start_time and not is_running:
            duration_minutes = total_duration / 60.0
            st.caption(f"Duration: {duration_minutes:.1f} min")
    
    return is_running, current_elapsed, start_time, stop_time

def timer_with_controls(timer_key):
    """
    Complete timer component with display and controls
    Uses start/stop timestamps for accurate duration calculation
    
    Args:
        timer_key: Unique identifier for this timer
    
    Returns:
        int: Current elapsed seconds (final duration when stopped)
    """
    
    # Get timer state and controls
    is_running, elapsed_seconds, start_time, stop_time = simple_timer_controls(timer_key)
    
    # Display JavaScript timer (real-time while running)
    javascript_timer(timer_key, is_running, start_time, elapsed_seconds)
    
    # Return the duration for use in the form
    # If stopped, return the final calculated duration
    # If running, return current elapsed time
    if stop_time and start_time and not is_running:
        # Timer was stopped - return the final duration
        return st.session_state[f"{timer_key}_total_duration"]
    elif is_running and start_time:
        # Timer is running - return current elapsed time
        return elapsed_seconds
    else:
        # Timer not started or reset
        return 0