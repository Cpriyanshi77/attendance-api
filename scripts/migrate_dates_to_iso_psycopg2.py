#!/usr/bin/env python3
"""
Migrate RFC date strings in attendance.date to ISO YYYY-MM-DD using psycopg2.
Usage:
  source venv/bin/activate
  export DB_DSN="host=127.0.0.1 dbname=yourdb user=youruser password=yourpass"
  python3 scripts/migrate_dates_to_iso_psycopg2.py
"""

import os
from email.utils import parsedate_to_datetime
from datetime import datetime
import psycopg2
import psycopg2.extras

DB_DSN = os.getenv("DB_DSN") or os.getenv("DATABASE_DSN") or os.getenv("DATABASE_URL") or "host=127.0.0.1 dbname=yourdb user=youruser password=yourpass"
TABLE = os.getenv("ATT_TABLE", "attendance")
ID_COL = os.getenv("ATT_ID_COL", "id")
DATE_COL = os.getenv("ATT_DATE_COL", "date")

def parse_to_iso(s):
    if s is None:
        return None
    s = str(s).strip()
    if len(s) == 10 and s.count("-") == 2:
        return s
    try:
        dt = parsedate_to_datetime(s)
        return dt.date().isoformat()
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(s)
        return dt.date().isoformat()
    except Exception:
        pass
    return None

def main():
    print("Connecting to DB using DSN:", DB_DSN if "yourdb" not in DB_DSN else "(masked)")
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT {ID_COL}, {DATE_COL} FROM {TABLE}")
    rows = cur.fetchall()
    print(f"Found {len(rows)} rows in {TABLE}")
    updated = 0
    skipped = 0
    for r in rows:
        rid = r[ID_COL]
        date_val = r[DATE_COL]
        iso = parse_to_iso(date_val)
        if not iso:
            skipped += 1
            print(f"SKIP id={rid} unparseable date: {date_val!r}")
            continue
        if iso == date_val:
            continue
        cur.execute(f"UPDATE {TABLE} SET {DATE_COL} = %s WHERE {ID_COL} = %s", (iso, rid))
        updated += 1
    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. Updated: {updated}, Skipped: {skipped}")

if __name__ == "__main__":
    main()
