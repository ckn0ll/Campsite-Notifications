@echo off
REM Runs the ReserveCalifornia portion of the watchlist locally.
REM Recreation.gov watches stay on GitHub Actions — see README.md for why.
REM
REM This is meant to be triggered by Windows Task Scheduler on a repeating
REM schedule. It pulls the latest watchlist.yaml from GitHub first, so
REM changes made in campsite-watchlist.html + pushed to the repo show up
REM here automatically.

cd /d "%~dp0"

REM Only run between 7:30am and 10:30pm Pacific — see check_time_window.py.
REM This is a safety net on top of the Task Scheduler trigger window itself,
REM in case Task Scheduler ever fires a catch-up run outside that window
REM (e.g. right after the PC wakes from an extended sleep).
python check_time_window.py
if errorlevel 1 (
    exit /b 0
)

REM Best-effort pull — if it fails (no internet, merge conflict, etc.)
REM keep using whatever watchlist.yaml is already on disk.
git pull

python run_watchlist.py --provider ReserveCalifornia
