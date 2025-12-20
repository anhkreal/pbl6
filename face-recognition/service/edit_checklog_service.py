from datetime import datetime
from db.nguoi_repository import NguoiRepository
from utils.timezone import TZ
from dateutil import parser

nguoi_repo = NguoiRepository()

VALID_STATUSES = {'late', 'early', 'on_time', 'absent'}


def _parse_to_local_date(s: str):
    if not s:
        return None
    try:
        dt = parser.parse(s)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt_local = TZ.localize(dt)
    else:
        dt_local = dt.astimezone(TZ)
    return dt_local.date()


def edit_checklog_by_id(row_id: int, status: str, edited_by: int = None, note: str = None):
    if status not in VALID_STATUSES:
        return {"success": False, "message": "Invalid status", "status_code": 400}
    existing = nguoi_repo.find_checklog_by_id(row_id)
    if not existing:
        return {"success": False, "message": "Checklog not found", "status_code": 404}
    ok = nguoi_repo.update_checklog_status(row_id=row_id, status=status, edited_by=edited_by, note=note)
    if ok:
        return {"success": True, "id": row_id, "status": status}
    return {"success": False, "message": "Could not update checklog", "status_code": 500}


def edit_checklog_by_user_and_date(user_id: int, date: str, status: str, edited_by: int = None, note: str = None):
    if status not in VALID_STATUSES:
        return {"success": False, "message": "Invalid status", "status_code": 400}
    date_parsed = _parse_to_local_date(date)
    if not date_parsed:
        return {"success": False, "message": "Invalid date", "status_code": 400}
    row = nguoi_repo.find_checklog_by_user_and_date(user_id=int(user_id), date_only=date_parsed)
    if not row:
        return {"success": False, "message": "No checklog for user/date", "status_code": 404}
    row_id = row.get('id')
    ok = nguoi_repo.update_checklog_status(row_id=row_id, status=status, edited_by=edited_by, note=note)
    if ok:
        return {"success": True, "id": row_id, "status": status}
    return {"success": False, "message": "Could not update checklog", "status_code": 500}
