@echo off
rem ============================================================
rem Keychron Launcher Local Edition - Launcher
rem Double-click to start local server and open browser.
rem To stop server: close the minimized "Keychron Launcher Server" window.
rem ============================================================
setlocal
cd /d "%~dp0"

rem ---- Find Python ----
set "PY="
for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PY set "PY=%%i"
)
if not defined PY (
    echo [ERROR] Python not found. Please install Python 3.x first.
    pause
    exit /b 1
)

rem ---- If port already listening, skip server start ----
set "PORT=1984"
netstat -ano | findstr ":1984 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo Starting Keychron Launcher local server on port %PORT% ...
    start "Keychron Launcher Server" /min "%PY%" "%~dp0server.py" --port=%PORT%
    ping -n 3 127.0.0.1 >nul
) else (
    echo Server already running on port %PORT%.
)

start "" "http://127.0.0.1:%PORT%/"
echo.
echo Keychron Launcher: http://127.0.0.1:%PORT%/
echo You can close this window. Server keeps running in background.
ping -n 4 127.0.0.1 >nul
endlocal
