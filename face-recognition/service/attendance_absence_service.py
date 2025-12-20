from datetime import datetime
import pytz
from db.nguoi_repository import NguoiRepository

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
