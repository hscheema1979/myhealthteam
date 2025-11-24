import os
import time
import subprocess
import requests
from datetime import datetime

# CONFIGURATION
STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"
# App resides in the same directory as this monitor script
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'app.py'))
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'streamlit_monitor.log'))
CHECK_INTERVAL = 60  # seconds

# Launch Streamlit in a visible PowerShell window so restarts are visible
START_CMD = [
    'powershell.exe', '-NoExit', '-Command', f'python -m streamlit run "{APP_PATH}"'
]

def log_status(message):
    with open(LOG_PATH, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def is_app_running():
    try:
        r = requests.get(STREAMLIT_URL, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def is_streamlit_process_running():
    try:
        result = subprocess.check_output(['tasklist'], shell=True).decode()
        return 'streamlit.exe' in result or ('python.exe' in result and 'streamlit' in result)
    except Exception:
        return False

def start_app():
    log_status("Attempting to start Streamlit app...")
    if is_streamlit_process_running():
        log_status("Streamlit process already running. Skipping start.")
        return
    try:
        # Start the app in a visible PowerShell window (no stdout/stderr redirection)
        subprocess.Popen(START_CMD)
        log_status("Streamlit app started in visible console.")
    except Exception as e:
        log_status(f"Failed to start Streamlit app: {e}")

def monitor_loop():
    log_status("Streamlit monitor started.")
    failure_count = 0
    MAX_FAILURES = 5
    while True:
        running = is_app_running()
        if running:
            log_status("Streamlit app is running.")
            failure_count = 0
        else:
            log_status("Streamlit app is NOT running. Restarting...")
            start_app()
            failure_count += 1
            if failure_count >= MAX_FAILURES:
                log_status(f"Streamlit app failed to start {MAX_FAILURES} times in a row. Manual intervention may be required.")
                failure_count = 0
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_loop()
