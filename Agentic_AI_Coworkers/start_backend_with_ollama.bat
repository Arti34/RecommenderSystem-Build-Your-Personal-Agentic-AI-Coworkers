@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
set USE_OLLAMA=1
set OLLAMA_MODEL=qwen3:1.7b
echo Ollama mode enabled. Ensure Ollama is running and qwen3:1.7b has been downloaded.
echo Starting FastAPI at http://127.0.0.1:8001
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
pause
