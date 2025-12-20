from db.models import Nguoi
from db.nguoi_repository import NguoiRepository
from datetime import datetime
import pytz
import traceback
from service.shift_attendance_service import current_shift
from service.kpi_service import (
    get_kpi_by_user_and_date_service,
    add_kpi_service,
)

nguoi_repo = NguoiRepository()


def add_users_service(full_name: str, age: int = None, phone: str = None, shift: str = 'day', address: str = None, gender: str = None, role: str = 'user', pin: str = None, avatar_bytes: bytes = None):
    # Basic validation
    if not full_name:
        return {"success": False, "message": "full_name là bắt buộc", "status_code": 400}

    new_nguoi = Nguoi(
        id=None,
        username=None,
        pin=pin,
        full_name=full_name,
        age=age,
        address=address,
        phone=phone,
        gender=gender,
        role=role,
        shift=shift,
        status='working',
        avatar_url=avatar_bytes,
        created_at=None,
        updated_at=None
    )
    try:
        new_id = nguoi_repo.add(new_nguoi)
        # Sau khi thêm nhân viên: nếu đang trong ca trùng với shift của nhân viên → khởi tạo ngay lập tức
        try:
            tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now_local = datetime.now(tz)
            today = now_local.date()
            shift_name = current_shift(now_local)
            if shift_name in ('day', 'night') and (shift_name == (shift or 'day')):
                # 1) Tạo shift_attendance
                nguoi_repo.upsert_shift_attendance(user_id=int(new_id), date_only=today, shift=shift_name, last_seen=None)
                # 2) Tạo checklog pending nếu chưa có
                existing_checklog = nguoi_repo.find_checklog_by_user_and_date(int(new_id), today)
                if not existing_checklog:
                    with nguoi_repo as cursor:
                        sql = "INSERT INTO checklog (user_id, date, shift, status, note) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(sql, (int(new_id), today, shift_name, 'pending', 'Auto-created on user add'))
                # 3) Tạo KPI khởi tạo nếu chưa có
                kpi_res = get_kpi_by_user_and_date_service(int(new_id), today.strftime('%Y-%m-%d'))
                if not kpi_res.get('success'):
                    add_kpi_service(
                        user_id=int(new_id),
                        date=today.strftime('%Y-%m-%d'),
                        emotion_score=100.0,
                        attendance_score=100.0,
                        total_score=100.0,
                        remark='Auto-init on user add'
                    )
                print(f"[user-add] Đã khởi tạo ngay shift_attendance/checklog/KPI cho user_id={new_id}, ca={shift_name}, ngày={today}")
            else:
                print(f"[user-add] Thêm nhân viên user_id={new_id} ngoài khung ca hiện tại ({shift_name}). Sẽ được khởi tạo vào đầu ca kế tiếp.")
        except Exception as e:
            print(f"[user-add] Lỗi khi khởi tạo shift_attendance/checklog/KPI cho user_id={new_id}: {e}")
            traceback.print_exc()
        return {"success": True, "message": "Đã thêm nhân viên", "class_id": new_id}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi thêm nhân viên: {e}", "status_code": 500}
