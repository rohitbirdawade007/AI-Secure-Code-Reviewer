@echo off
title AI Secure Code Reviewer — Frontend
color 0B

echo.
echo  ===================================================
echo   AI Secure Code Reviewer — Opening Frontend UI
echo  ===================================================
echo.

:: Check if backend is running by hitting the health endpoint
echo  [*] Checking if backend is running on http://localhost:8000 ...

venv\Scripts\python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo  [WARNING] Backend server does not appear to be running!
    echo  Please start the backend first using: start_backend.bat
    echo.
    choice /C YN /M "Open browser anyway"
    if errorlevel 2 (
        echo  Exiting.
        pause
        exit /b 1
    )
)

echo  [*] Opening frontend in your default browser...
echo  [*] URL: http://localhost:8000
echo.
start "" "http://localhost:8000"

echo  [*] Also opening API Docs...
timeout /t 1 /nobreak >nul
start "" "http://localhost:8000/docs"

echo.
echo  Frontend opened! Switch to your browser.
echo.
pause
