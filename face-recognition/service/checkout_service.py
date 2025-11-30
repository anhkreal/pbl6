from datetime import datetime, time
import pytz
from db.nguoi_repository import NguoiRepository


nguoi_repo = NguoiRepository()


def checkout(user_id: int, edited_by: int = None, note: str = None):
    """Perform checkout for a user. Uses Asia/Ho_Chi_Minh (UTC+7) local time to determine "early" status.

    Rules:
    - day shift: checkout before 14:00 local -> early
    - night shift: checkout before 10:00 local -> early
    """
    TZ = pytz.timezone('Asia/Ho_Chi_Minh')
    try:
        # compute now in local time (UTC+7)
        now_local = datetime.now(TZ)

        # find open checkin for today (use local date)
        date_local = now_local.date()
        open_row = nguoi_repo.find_open_checkin_by_date(user_id=int(user_id), date_only=date_local)
        if not open_row:
            return {"success": False, "message": "Không tìm thấy check-in mở cho ngày hôm nay", "status_code": 404}

        # determine thresholds based on shift
        shift = open_row.get('shift') or 'day'
        if shift == 'day':
            cutoff = time(14, 0, 0)
        else:
            cutoff = time(10, 0, 0)

        # decide early or not by comparing local checkout time
        is_early = now_local.time() < cutoff

        # compute total hours between stored check_in (assumed stored as UTC+7) and now (also UTC+7)
        check_in_local = open_row.get('check_in')
        if check_in_local is None:
            return {"success": False, "message": "Bản ghi check-in không có thời gian check_in", "status_code": 500}

        # ensure check_in_local is timezone-aware UTC+7; if naive, localize
        if check_in_local.tzinfo is None:
            check_in_local = TZ.localize(check_in_local)

        total_seconds = (now_local - check_in_local).total_seconds()
        total_hours = round(total_seconds / 3600.0, 2)

        # update the checklog row
        new_status = open_row.get('status')
        if is_early:
            new_status = 'early'

        updated = nguoi_repo.update_checkin_checkout(row_id=open_row.get('id'), check_out=now_local.replace(tzinfo=None), total_hours=total_hours, status=new_status, edited_by=edited_by, note=note)
        if updated:
            return {"success": True, "id": open_row.get('id'), "status": new_status, "total_hours": total_hours}
        else:
            return {"success": False, "message": "Không thể cập nhật checkout", "status_code": 500}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi checkout: {e}", "status_code": 500}
