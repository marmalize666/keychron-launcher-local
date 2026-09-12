@echo off
rem ============================================================
rem Keychron Launcher 本地版 启动脚本
rem 双击运行：启动本地服务器并打开浏览器
rem 关闭：直接关闭本窗口（黑窗口），或按 Ctrl+C
rem ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

rem ---- 找 Python ----
set "PY="
for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PY set "PY=%%i"
)
if not defined PY (
    echo [ERROR] Python not found. Please install Python 3.x first.
    pause
    exit /b 1
)

rem ---- 端口已被占用则直接开浏览器（服务器已在跑） ----
set "PORT=1984"
netstat -ano | findstr ":1984 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo Starting Keychron Launcher local server on port %PORT% ...
    start "Keychron Launcher Server" /min "%PY%" "%~dp0server.py" --port=%PORT%
    timeout /t 2 /nobreak >nul
) else (
    echo Server already running on port %PORT%.
)

start "" "http://127.0.0.1:%PORT%/"
echo.
echo Keychron Launcher: http://127.0.0.1:%PORT%/
echo (Keep this window open. Close it to keep server running in background.)
timeout /t 5 /nobreak >nul
endlocal
