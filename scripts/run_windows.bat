@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo  🦆 Starting QuakMeeting for Windows
echo ===================================================

:: Check for Python installation
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=py -3
    set PYW_CMD=pyw -3
    goto :FOUND_PY
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY_CMD=python
    set PYW_CMD=pythonw
    goto :FOUND_PY
)

echo [ERROR] Python 3 was not found in PATH!
echo Please install Python 3.10+ from https://www.python.org/
echo Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:FOUND_PY
:: Move to repository root directory
cd /d "%~dp0\.."

:: Check if PyQt6 is installed
%PY_CMD% -c "import PyQt6" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing required dependencies (PyQt6)...
    %PY_CMD% -m pip install -r requirements-windows.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies. Please run: pip install -r requirements-windows.txt
        pause
        exit /b 1
    )
)

echo [INFO] Launching QuakMeeting Flight Deck...
start "" %PYW_CMD% main.py %*
if %ERRORLEVEL% neq 0 (
    start "" %PY_CMD% main.py %*
)
