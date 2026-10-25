import os
import sys

# Clear any environment variables that could cause port mismatches or overrides in Streamlit
for key in list(os.environ.keys()):
    if key in ["PORT", "STREAMLIT_SERVER_PORT", "STREAMLIT_BROWSER_SERVER_PORT"]:
        del os.environ[key]

import streamlit as st
import streamlit.web.bootstrap

if __name__ == "__main__":
    # Get the directory path
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_path, "app.py")
    
    # Configure Streamlit settings programmatically
    flag_options = {
        "server.port": 8501,
        "browser.serverPort": 8501,
        "server.headless": False,
        "global.developmentMode": False,
        "_is_running_with_streamlit": True,
    }
    
    # Load and run
    streamlit.web.bootstrap.load_config_options(flag_options=flag_options)
    
    # Setup sys.argv
    sys.argv = ["streamlit", "run", app_path]
    
    # Run Streamlit bootstrap
    streamlit.web.bootstrap.run(app_path, False, [], flag_options)
