# scripts/migrate_dates_to_iso.py
from client.postgres import DatabaseSDKFacade
from email.utils import parsedate_to_datetime
from datetime import datetime

def parse_to_iso(s):
    if not s:
        return None
    s = str(s).strip()
    if len(s) == 10 and s.count("-") == 2:
        return s
    try:
        dt = parsedate_to_datetime(s)
        return dt.date().isoformat()
    except Exception:
        try:
            dt = datetime.fromisoformat(s)
            return dt.date().isoformat()
        except Exception:
            return None

db = DatabaseSDKFacade.database
records = db.read_all_employee_attendance()
updated = 0

for r in records:
    iso = parse_to_iso(r["date"])
    if iso and iso != r["date"]:
        db.create_employee_attendance(r["id"], r["name"], r["status"], iso)
        updated += 1

print("Updated rows:", updated)
