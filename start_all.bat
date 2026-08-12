@echo off
title AI Secure Code Reviewer — Full Stack Launcher
color 0E

echo.
echo  ====================================================
echo   AI Secure Code Reviewer — Full Stack Launcher
echo   Backend  :  FastAPI + Semgrep + LangChain + OpenAI
echo   Frontend :  http://localhost:8000
echo  ====================================================
echo.

:: ── Prerequisites check ────────────────────────────────────────────
if not exist "venv\Scripts\python.exe" (
    echo  [ERROR] Virtual environment not found!
    echo.
    echo  Run these commands first:
    echo    python -m venv venv
    echo    venv\Scripts\pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo  [INFO] .env not found — copying from .env.example...
    copy ".env.example" ".env" >nul
    echo  [!] IMPORTANT: Edit .env and add your OPENAI_API_KEY before scanning!
    echo.
    pause
)

:: ── Start backend in a new window ─────────────────────────────────
echo  [1/2] Starting backend server in a new window...
start "Backend — AI Secure Code Reviewer" cmd /k ^
    "color 0A && echo. && echo  Backend starting... && echo. && venv\Scripts\python -m uvicorn backend.main:app --reload --reload-dir backend --reload-dir frontend --host 0.0.0.0 --port 8000"

:: ── Wait for server to be ready ────────────────────────────────────
echo  [*] Waiting for backend to be ready...
set /a attempts=0
:wait_loop
    timeout /t 1 /nobreak >nul
    venv\Scripts\python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" 2>nul
    if %errorlevel% equ 0 goto server_ready
    set /a attempts+=1
    if %attempts% geq 15 (
        echo  [WARNING] Backend is taking longer than expected...
        goto open_browser
    )
    goto wait_loop

:server_ready
echo  [OK] Backend is up and running!

:open_browser
:: ── Open frontend ──────────────────────────────────────────────────
echo  [2/2] Opening frontend in browser...
timeout /t 1 /nobreak >nul
start "" "http://localhost:8000"
timeout /t 1 /nobreak >nul
start "" "http://localhost:8000/docs"

echo.
echo  ====================================================
echo   Everything is running!
echo.
echo   App      →  http://localhost:8000
echo   API Docs →  http://localhost:8000/docs
echo.
echo   To STOP: Close the Backend window or press Ctrl+C
echo  ====================================================
echo.
pause
