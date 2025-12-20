from db.nguoi_repository import NguoiRepository
from datetime import datetime
import pytz
from utils.shift_config import get_shift_by_time, SHIFT_DAY_START, SHIFT_DAY_END, SHIFT_NIGHT_START, SHIFT_NIGHT_END

nguoi_repo = NguoiRepository()


def add_emotion_service(user_id: int = None, camera_id: int = None, emotion_type: str = None, confidence: float = None, image_file=None, note: str = None):
    """
    Thêm emotion log cho nhân viên.
    
    Quy tắc: Chỉ lưu emotion log nếu nhân viên đang trong ca làm việc được phân công
    """
    try:
        # Nếu có user_id, kiểm tra ca làm việc
        if user_id is not None:
            user = nguoi_repo.get_by_id(int(user_id))
            if not user:
                return {"success": False, "message": "Không tìm thấy user", "status_code": 404}
            
            shift = getattr(user, 'shift', 'day')
            
            # Kiểm tra thời gian hiện tại
            TZ = pytz.timezone('Asia/Ho_Chi_Minh')
            now_local = datetime.now(TZ)
            current_time = now_local.time()
            
            # Kiểm tra nhân viên có trong ca làm việc không
            current_shift = get_shift_by_time(current_time)
            
            # Nếu không trong ca nào cả (none) hoặc ca hiện tại khác ca của nhân viên
            if current_shift == 'none':
                return {
                    "success": False, 
                    "message": f"Không thể ghi nhận cảm xúc ngoài giờ làm việc. Giờ làm việc: Ca sáng {SHIFT_DAY_START.strftime('%H:%M')}-{SHIFT_DAY_END.strftime('%H:%M')}, Ca chiều {SHIFT_NIGHT_START.strftime('%H:%M')}-{SHIFT_NIGHT_END.strftime('%H:%M')}", 
                    "status_code": 403
                }
            
            if current_shift != shift:
                return {
                    "success": False, 
                    "message": f"Không thể ghi nhận cảm xúc vào ca {current_shift}. Nhân viên được phân ca {shift}", 
                    "status_code": 403
                }
        
        # read image bytes defensively
        image_bytes = None
        if image_file is not None:
            try:
                image_file.file.seek(0)
            except Exception:
                pass
            image_bytes = image_file.file.read()

        rowid = nguoi_repo.add_emotion_log(user_id=user_id, camera_id=camera_id, emotion_type=emotion_type, confidence=confidence, image_bytes=image_bytes, note=note)
        if rowid:
            return {"success": True, "message": "Đã lưu log cảm xúc", "id": rowid}
        else:
            return {"success": False, "message": "Không thể lưu log cảm xúc", "status_code": 500}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi lưu log: {e}", "status_code": 500}
