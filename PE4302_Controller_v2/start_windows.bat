@echo off
cd /d "%~dp0"
py -3 -c "import PySide6" 2>nul || py -3 -m pip install PySide6
py -3 main.py
pause
