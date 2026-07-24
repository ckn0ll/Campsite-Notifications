#!/usr/bin/env python3
"""
Exits with code 0 (allowed) if the current time in Pacific time is inside
the configured window, or code 1 (blocked) otherwise.

Used by run_local_windows.bat as a safety net so the ReserveCalifornia
check never runs overnight, even if Task Scheduler fires an unexpected
"make-up" run outside its normal window (e.g. after the PC was asleep
through a scheduled trigger).

Uses zoneinfo (America/Los_Angeles) rather than the PC's raw system clock,
so this is correct regardless of what timezone Windows itself is set to,
and automatically handles the PST/PDT switch across the year.
"""

import sys
from datetime import datetime, time
from zoneinfo import ZoneInfo

WINDOW_START = time(7, 30)   # 7:30 AM Pacific
WINDOW_END = time(22, 30)    # 10:30 PM Pacific

now_pacific = datetime.now(ZoneInfo("America/Los_Angeles")).time()

if WINDOW_START <= now_pacific <= WINDOW_END:
    sys.exit(0)
else:
    print(
        f"Current time {now_pacific.strftime('%I:%M %p')} Pacific is outside "
        f"the {WINDOW_START.strftime('%I:%M %p')}\u2013{WINDOW_END.strftime('%I:%M %p')} "
        f"window — skipping this run."
    )
    sys.exit(1)
