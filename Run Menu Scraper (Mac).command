#!/bin/bash
# Double-click this file to scrape Swiggy / Zomato menus. Excel files are saved in the "output" folder.
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python is not installed. Install it from https://www.python.org/downloads/ then double-click this file again."
  read -r -p "Press Enter to close"
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "First run: setting things up, this takes a minute..."
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt
mkdir -p output && cd output
../.venv/bin/python ../menu_scraper.py
echo
echo "Your Excel files are in: $(pwd)"
open .
read -r -p "Press Enter to close"
