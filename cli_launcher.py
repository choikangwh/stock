import sys
import os
import streamlit.web.cli as stcli

def run_dashboard():
    """
    Programmatic entry point to run the Streamlit stock dashboard.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    app_path = os.path.join(dir_path, "app.py")
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())

if __name__ == "__main__":
    run_dashboard()
