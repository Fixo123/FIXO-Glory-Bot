@echo off
REM FIXO DEV — Guild Glory Bot Startup Script (Windows)

title FIXO DEV — Guild Glory Bot
echo 🔥 FIXO DEV — Guild Glory Bot
echo =================================

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
cd backend
pip install -r requirements.txt

REM Start backend
echo 🚀 Starting Backend Server...
start /B python main.py

REM Start frontend
echo 🌐 Starting Frontend Server...
cd ../frontend
start /B python -m http.server 3000

echo.
echo ✅ FIXO DEV Running!
echo 📡 Backend:  http://localhost:8000
echo 🌐 Frontend: http://localhost:3000
echo.
echo Press Ctrl+C to stop
pause