@echo off
setlocal
cd /d "%~dp0"

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
where py >nul 2>nul
if not errorlevel 1 (
    set "BASE_PYTHON=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 goto no_python
    set "BASE_PYTHON=python"
)

if not exist "%VENV_PYTHON%" (
    echo Preparing the app environment. This only happens on first launch.
    %BASE_PYTHON% -m venv .venv
    if errorlevel 1 goto setup_failed
)

"%VENV_PYTHON%" -c "import tkinter" >nul 2>nul
if errorlevel 1 goto no_tkinter

"%VENV_PYTHON%" -c "import pynput" >nul 2>nul
if errorlevel 1 (
    echo Installing app dependencies. An internet connection is needed the first time.
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto install_failed
)

"%VENV_PYTHON%" mouse_controller\main.py
if errorlevel 1 pause
exit /b %errorlevel%

:no_python
echo Python 3.10 or newer was not found. Install Python from https://www.python.org/downloads/ and try again.
pause
exit /b 1

:no_tkinter
echo Tkinter is missing. Re-run the Python installer and include Tcl/Tk support.
pause
exit /b 1

:setup_failed
echo Could not create the app environment. Make sure Python includes its venv and pip components.
pause
exit /b 1

:install_failed
echo Dependency installation failed. Check your internet connection and try again.
pause
exit /b 1