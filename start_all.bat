@echo off
echo Starting EmpathAI Full Stack...
echo.

echo [1/3] Starting Backend Server...
start cmd /k "cd /d %~dp0 && python -m venv .venv && call .venv\Scripts\activate && pip install -r requirements.txt && python empathai_simple.py"

echo [2/3] Waiting for backend to start...
timeout /t 5 /nobreak

echo [3/3] Starting Frontend...
start cmd /k "cd /d %~dp0\frontend && npm start"

echo.
echo ============================================
echo ✅ EmpathAI is starting!
echo 📡 Backend: http://localhost:8007
echo 🌐 Frontend: http://localhost:3000
echo 📚 API Docs: http://localhost:8007/docs
echo ============================================
echo.
pause