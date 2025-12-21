from datetime import datetime
import pytz
from db.nguoi_repository import NguoiRepository
import os

TZ = pytz.timezone('Asia/Ho_Chi_Minh')
nguoi_repo = NguoiRepository()


def mark_absent_service(user_id: int, note: str = None, edited_by: int = None):
    """
    Mark the given user as 'absent' for the current local date.
    - If a checklog already exists for today and is 'absent', do nothing (idempotent).
    - If a checklog exists and is not 'absent', return conflict.
    - Otherwise, insert a new checklog with status 'absent' and no check_in/check_out.
    """
    try:
        user = nguoi_repo.get_by_id(int(user_id))
        if not user:
            return {"success": False, "message": "Không tìm thấy user", "status_code": 404}

        shift = getattr(user, 'shift', 'day')
        now_local = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
        row = nguoi_repo.find_checklog_by_user_and_date(user_id=int(user_id), date_only=now_local.date())

        if row:
            existing_status = row.get('status') or ''
            if existing_status == 'absent':
                return {"success": True, "id": row.get('id'), "status": "absent", "message": "Đã được đánh dấu vắng từ trước"}
            else:
                return {"success": False, "message": "Đã có checklog cho ngày này (không thể đánh dấu vắng)", "status_code": 409}

        rowid = nguoi_repo.add_absence(user_id=int(user_id), shift=shift, edited_by=edited_by, note=note)
        if rowid:
            return {"success": True, "id": rowid, "status": "absent"}
        return {"success": False, "message": "Không thể đánh dấu vắng", "status_code": 500}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi đánh dấu vắng: {e}", "status_code": 500}


def _parse_to_local_date(s: str):
    if not s:
        return None
    try:
        # Try ISO format (YYYY-MM-DD) or full datetime
        from datetime import datetime as _dt
        try:
            dt = _dt.fromisoformat(s)
        except Exception:
            dt = _dt.strptime(s, '%Y-%m-%d')
    except Exception:
        return None
    if dt.tzinfo is None:
        dt_local = TZ.localize(dt)
    else:
        dt_local = dt.astimezone(TZ)
    return dt_local.date()


def generate_absent_report(date: str = None, shift: str = None, write_log: bool = True):
    """Generate a report of absent users for a given date and shift.

    - date: YYYY-MM-DD (optional; defaults to today local)
    - shift: 'day'|'night' (optional; defaults to user's recorded shift or 'day')
    - write_log: if True, append to logs/absent_report_YYYY-MM-DD_<shift>.log
    Returns JSON-friendly dict with list of absentees.
    """
    try:
        now_local = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
        date_only = _parse_to_local_date(date) or now_local.date()
        shift_name = (shift or 'day').lower()

        rows = nguoi_repo.get_absent_users_by_shift_date(shift=shift_name, date_only=date_only)
        absentees = [
            {
                "user_id": r.get("user_id"),
                "full_name": r.get("full_name"),
                "checklog_id": r.get("checklog_id"),
            }
            for r in rows
        ]

        if write_log:
            # Write to logs directory
            date_str = date_only.strftime('%Y-%m-%d')
            log_dir = os.path.join(os.getcwd(), 'logs')
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                pass
            log_path = os.path.join(log_dir, f"absent_report_{date_str}_{shift_name}.log")
            timestamp = now_local.strftime('%Y-%m-%d %H:%M:%S')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] shift={shift_name} date={date_str} total={len(absentees)}\n")
                for item in absentees:
                    f.write(f"- user_id={item['user_id']} | name={item['full_name']} | checklog_id={item['checklog_id']}\n")
                f.write("\n")

        return {"success": True, "date": date_only.isoformat(), "shift": shift_name, "total": len(absentees), "absentees": absentees}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi tạo báo cáo vắng: {e}", "status_code": 500}
