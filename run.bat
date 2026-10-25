@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo   Stock Analyst Dashboard Launcher
echo ==================================================

if exist ".venv\Scripts\python.exe" goto RUN_APP

where python >nul 2>&1
if errorlevel 1 goto NO_PYTHON

echo [INFO] Creating virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 goto VENV_FAIL

echo [INFO] Installing required packages...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto INSTALL_FAIL

:RUN_APP
echo [INFO] Starting dashboard in your default browser...
echo [INFO] Close this window or press Ctrl+C to stop.
echo ==================================================

.venv\Scripts\python.exe -m streamlit run app.py
if errorlevel 1 goto RUN_FAIL
goto END

:NO_PYTHON
echo [ERROR] Python is not installed or not in system PATH.
echo Please install Python 3.10+ from https://www.python.org/
pause
exit /b 1

:VENV_FAIL
echo [ERROR] Failed to create virtual environment.
pause
exit /b 1

:INSTALL_FAIL
echo [ERROR] Failed to install required packages.
pause
exit /b 1

:RUN_FAIL
echo.
echo [ERROR] Dashboard failed to start.
pause
exit /b 1

:END
endlocal
