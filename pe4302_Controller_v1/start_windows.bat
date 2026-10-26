@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 pause & exit /b 1
py pe4302_gui.py
if errorlevel 1 pause
