@echo off
rem Double-click this file to scrape Swiggy / Zomato menus. Excel files are saved in the "output" folder.
title Menu Scraper
cd /d "%~dp0"

rem Find Python. "py" comes with the python.org installer; "python" can be a Microsoft Store shortcut that does nothing.
set "PY="
py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python is not installed.
  echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH" during setup,
  echo then double-click this file again.
  start "" https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist .venv\Scripts\python.exe (
  echo First run: setting things up, this takes a minute...
  %PY% -m venv .venv
)
.venv\Scripts\python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo Could not install the required packages. Check your internet connection and try again.
  pause
  exit /b 1
)
if not exist output mkdir output
cd output
echo.
echo Paste Swiggy / Zomato links, separated by commas, then press Enter.
..\.venv\Scripts\python ..\menu_scraper.py
echo.
echo Your Excel files are in: %cd%
start "" "%cd%"
pause
