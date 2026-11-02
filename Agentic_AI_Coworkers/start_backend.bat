@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
echo Starting FastAPI at http://127.0.0.1:8001
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
pause
