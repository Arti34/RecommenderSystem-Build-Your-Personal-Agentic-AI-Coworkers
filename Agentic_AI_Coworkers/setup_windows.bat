@echo off
cd /d "%~dp0"
echo Setting up Agentic AI Coworkers...
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 (
    echo Python was not found. Please install Python 3.11 or newer and try again.
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and retry.
  pause
  exit /b 1
)
echo Setup complete. Double-click start_backend.bat, then start_frontend.bat.
pause
