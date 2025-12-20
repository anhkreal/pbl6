from db.nguoi_repository import NguoiRepository
from datetime import datetime
import pytz
from utils.shift_config import SHIFT_DAY_START, SHIFT_NIGHT_END

nguoi_repo = NguoiRepository()


def change_shift_service(user_id: int, new_shift: str):
    """
    Thay đổi ca làm việc của nhân viên.
    
    Quy tắc: Chỉ được phép đổi ca sau giờ làm việc (sau 20:00 hoặc trước 8:00)
    """
    if not new_shift:
        return {"success": False, "message": "shift mới không được để trống", "status_code": 400}
    
    try:
        # Kiểm tra thời gian hiện tại
        TZ = pytz.timezone('Asia/Ho_Chi_Minh')
        now_local = datetime.now(TZ)
        current_time = now_local.time()
        
        # Chỉ cho phép đổi ca ngoài giờ làm việc (sau 20:00 hoặc trước 8:00)
        if SHIFT_DAY_START <= current_time < SHIFT_NIGHT_END:
            return {
                "success": False, 
                "message": f"Không thể đổi ca trong giờ làm việc. Vui lòng đổi ca sau {SHIFT_NIGHT_END.strftime('%H:%M')} hoặc trước {SHIFT_DAY_START.strftime('%H:%M')}", 
                "status_code": 403
            }
        
        existing = nguoi_repo.get_by_id(user_id)
        if not existing:
            return {"success": False, "message": "Không tìm thấy người", "status_code": 404}
        existing.shift = new_shift
        affected = nguoi_repo.update_by_id(user_id, existing)
        if affected > 0:
            return {"success": True, "message": f"Đã cập nhật ca làm cho user {user_id} -> {new_shift}"}
        else:
            return {"success": False, "message": "Không thể cập nhật ca làm", "status_code": 500}
    except Exception as e:
        return {"success": False, "message": f"Lỗi: {e}", "status_code": 500}
