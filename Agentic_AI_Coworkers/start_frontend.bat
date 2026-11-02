@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
echo Opening Streamlit at http://localhost:8502
.venv\Scripts\python.exe -m streamlit run frontend/app.py --server.port 8502
pause
