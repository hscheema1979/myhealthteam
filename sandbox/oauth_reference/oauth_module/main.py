"""
Main entry point for App Engine deployment
This file is required by App Engine to run the Streamlit application
"""

import os
import subprocess
import sys

def main():
    """Main function to start the Streamlit application"""
    # Set environment variables for Streamlit
    os.environ.setdefault('STREAMLIT_SERVER_PORT', '8080')
    os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
    os.environ.setdefault('STREAMLIT_SERVER_ENABLE_CORS', 'false')
    os.environ.setdefault('STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION', 'false')
    
    # Get the port from environment (App Engine sets this)
    port = os.environ.get('PORT', '8080')
    
    # Start Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    subprocess.run(cmd)

if __name__ == '__main__':
    main()