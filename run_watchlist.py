#!/usr/bin/env python3
"""
Reads watchlist.yaml and runs `camply campsites` searches.

Each entry uses camply's `--search-once` (run once and exit — the correct
mode for cron-style scheduling, as opposed to `--continuous`, which loops
and sleeps forever inside the process) + `--offline-search` flags: camply
remembers what it saw last run (state saved under .camply-state/) and only
fires a notification for campsites that are newly available. That's what
makes it safe to run this on a schedule without getting the same
notification every time, and what lets the job actually finish instead of
running until the timeout kills it.

Usage:
  python run_watchlist.py                          # run every entry
  python run_watchlist.py --entry NAME              # run just one entry (used by the
                                                     # GitHub Actions matrix so entries
                                                     # run in parallel instead of queued
                                                     # up behind each other)
  python run_watchlist.py --provider ReserveCalifornia   # run only entries for one provider
  python run_watchlist.py --list-json               # print [{"name": ..., "slug": ...}, ...]
                                                     # for building the matrix
  python run_watchlist.py --list-json --provider RecreationDotGov   # same, filtered

Requires: pip install camply pyyaml
Requires env var NTFY_TOPIC to be set (see README.md).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
WATCHLIST_PATH = ROOT / "watchlist.yaml"
STATE_DIR = ROOT / ".camply-state"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "watch"


def load_watches() -> list[dict]:
    if not WATCHLIST_PATH.exists():
        print(f"No watchlist found at {WATCHLIST_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(WATCHLIST_PATH) as f:
        config = yaml.safe_load(f) or {}
    return config.get("watches") or []


def build_command(entry: dict) -> list[str]:
    name = entry["name"]
    provider = entry.get("provider", "ReserveCalifornia")

    cmd = [
        "camply", "campsites",
        "--provider", provider,
        "--start-date", str(entry["start_date"]),
        "--end-date", str(entry["end_date"]),
        "--notifications", "ntfy",
        "--search-once",
        "--offline-search",
        "--offline-search-path", str(STATE_DIR / f"{slugify(name)}.json"),
    ]

    for campground_id in entry.get("campground_ids") or []:
        cmd += ["--campground", str(campground_id)]

    for rec_area_id in entry.get("rec_area_ids") or []:
        cmd += ["--rec-area", str(rec_area_id)]

    if entry.get("nights"):
        cmd += ["--nights", str(entry["nights"])]

    if entry.get("weekends_only"):
        cmd += ["--weekends"]

    return cmd


def run_entry(entry: dict) -> int:
    name = entry.get("name", "unnamed watch")
    if not entry.get("campground_ids") and not entry.get("rec_area_ids"):
        print(f"Skipping '{name}': no campground_ids or rec_area_ids set.")
        return 0

    cmd = build_command(entry)
    print(f"\n=== Checking: {name} ===")
    print(" ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"'{name}' exited with code {result.returncode}", file=sys.stderr)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry", help="Run only the watch with this exact name")
    parser.add_argument(
        "--provider",
        help="Only run watches for this provider (e.g. ReserveCalifornia, RecreationDotGov)",
    )
    parser.add_argument(
        "--list-json",
        action="store_true",
        help="Print watches as a JSON array of {name, slug} and exit",
    )
    args = parser.parse_args()

    watches = load_watches()
    if not watches:
        print("watchlist.yaml has no entries under 'watches:' — nothing to do.")
        return 0

    if args.provider:
        watches = [
            w for w in watches
            if w.get("provider", "ReserveCalifornia").lower() == args.provider.lower()
        ]
        if not watches:
            print(f"No watches found for provider '{args.provider}'.")
            return 0

    if args.list_json:
        print(json.dumps([
            {"name": w.get("name", "unnamed watch"), "slug": slugify(w.get("name", "unnamed watch"))}
            for w in watches
        ]))
        return 0

    STATE_DIR.mkdir(exist_ok=True)

    if args.entry:
        matches = [w for w in watches if w.get("name") == args.entry]
        if not matches:
            print(f"No watch named '{args.entry}' found in watchlist.yaml", file=sys.stderr)
            return 1
        return run_entry(matches[0])

    exit_code = 0
    for entry in watches:
        code = run_entry(entry)
        if code != 0:
            exit_code = code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
