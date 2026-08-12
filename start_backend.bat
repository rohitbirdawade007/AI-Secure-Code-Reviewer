@echo off
title AI Secure Code Reviewer — Backend Server
color 0A

echo.
echo  ===================================================
echo   AI Secure Code Reviewer — Backend Server
echo   FastAPI + Semgrep + LangChain + OpenAI
echo  ===================================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo  [ERROR] Virtual environment not found.
    echo  Run this first:
    echo     python -m venv venv
    echo     venv\Scripts\pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

:: Check if .env exists
if not exist ".env" (
    echo  [WARNING] .env file not found. Copying from .env.example...
    copy ".env.example" ".env"
    echo  [!] Please edit .env and add your OPENAI_API_KEY before scanning.
    echo.
)

echo  [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo  [*] Starting FastAPI backend on http://localhost:8000
echo  [*] API Docs available at http://localhost:8000/docs
echo  [*] Press Ctrl+C to stop the server
echo.

:: Only watch backend/ and frontend/ — NOT uploads/ or reports/
:: This prevents uvicorn from restarting when files are uploaded
venv\Scripts\python -m uvicorn backend.main:app ^
    --reload ^
    --reload-dir backend ^
    --reload-dir frontend ^
    --host 0.0.0.0 ^
    --port 8000

echo.
echo  [*] Server stopped.
pause
