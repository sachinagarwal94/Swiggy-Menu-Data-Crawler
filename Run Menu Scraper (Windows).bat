@echo off
rem Double-click this file to scrape Swiggy / Zomato menus. Excel files are saved in the "output" folder.
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during setup, then double-click this file again.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  echo First run: setting things up, this takes a minute...
  python -m venv .venv
)
.venv\Scripts\python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if not exist output mkdir output
cd output
..\.venv\Scripts\python ..\menu_scraper.py
echo.
echo Your Excel files are in: %cd%
start "" "%cd%"
pause
