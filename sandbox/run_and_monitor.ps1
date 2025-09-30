# Start Streamlit app in background
Start-Process -WindowStyle Minimized -FilePath "streamlit" -ArgumentList "run", "app.py"

# Start monitor script in background
Start-Process -WindowStyle Minimized -FilePath "python" -ArgumentList "sandbox/streamlit_monitor.py"

Write-Host "Streamlit app and monitor started in background processes."
Write-Host "Check sandbox/streamlit_monitor.log for status."
