#!/usr/bin/env python3
"""
Safe migration: convert stored RFC date strings to ISO 'YYYY-MM-DD'
Uses the project's DatabaseSDKFacade so you don't need psycopg2 installed here.
Run from repo root inside the venv:
  source venv/bin/activate
  python3 scripts/migrate_dates_to_iso_v2.py
"""

import sys
import os
from email.utils import parsedate_to_datetime
from datetime import datetime

# Ensure repo root is on sys.path so `client` package can be imported
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Now import project DB facade
from client.postgres import DatabaseSDKFacade

def parse_to_iso(s):
    if s is None:
        return None
    s = str(s).strip()
    # already ISO
    if len(s) == 10 and s.count("-") == 2:
        return s
    # try RFC/email-style
    try:
        dt = parsedate_to_datetime(s)
        return dt.date().isoformat()
    except Exception:
        pass
    # try ISO full datetime
    try:
        dt = datetime.fromisoformat(s)
        return dt.date().isoformat()
    except Exception:
        pass
    return None

def main():
    db = DatabaseSDKFacade.database
    print("Reading all records from DB via client.postgres...")
    records = db.read_all_employee_attendance()
    if not records:
        print("No records returned (empty list). Exiting.")
        return

    updated = 0
    total = 0
    for r in records:
        total += 1
        rid = r.get("id")
        old_date = r.get("date")
        iso = parse_to_iso(old_date)
        if not iso:
            # skip unparseable values (log them)
            print(f"SKIP (unparseable): id={rid} date={old_date!r}")
            continue
        # If already ISO or same, skip
        if iso == old_date:
            continue
        # Otherwise update by calling create_employee_attendance (upsert) or call an update method if you have one
        try:
            # create_employee_attendance should accept iso date (we intend ISO storage)
            db.create_employee_attendance(rid, r.get("name"), r.get("status"), iso)
            updated += 1
            print(f"Updated id={rid}: {old_date!r} -> {iso}")
        except Exception as e:
            print(f"ERROR updating id={rid}: {e}")

    print(f"Done. Processed {total} rows, updated {updated} rows.")

if __name__ == "__main__":
    main()
