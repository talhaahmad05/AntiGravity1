@echo off
title Weather Application
echo Starting Weather Application...
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Make sure Python is installed and run:
    echo   pip install -r requirements.txt
    pause
)
