from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse
from auth.mysql_auth import get_current_user_mysql
from db.nguoi_repository import NguoiRepository
from db.taikhoan_repository import TaiKhoanRepository
from db.models import TaiKhoan, Nguoi
from datetime import datetime
import pytz
import traceback
from service.shift_attendance_service import current_shift
from service.kpi_service import get_kpi_by_user_and_date_service, add_kpi_service

add_user_and_account_router = APIRouter()

@add_user_and_account_router.post("/add-user-account", summary="Thêm mới nhân viên và tài khoản (yêu cầu đăng nhập)")
def add_user_and_account(
    full_name: str = Form(None),
    username: str = Form(...),
    age: int = Form(None),
    address: str = Form(None),
    phone: str = Form(None),
    shift: str = Form('day'),
    current_user: str = Depends(get_current_user_mysql)
):
    nguoi_repo = NguoiRepository()
    taikhoan_repo = TaiKhoanRepository()

    # Kiểm tra username đã tồn tại chưa
    if taikhoan_repo.get_by_username(username):
        return JSONResponse(content={"success": False, "message": "Username đã tồn tại"}, status_code=400)

    # Thêm tài khoản với mật khẩu mặc định 123456 (không mã hóa)
    default_password = "123456"
    try:
        tk = TaiKhoan(username=username, passwrd=default_password)
        taikhoan_repo.add(tk)
    except Exception as e:
        return JSONResponse(content={"success": False, "message": f"Lỗi khi thêm tài khoản: {e}"}, status_code=500)

    # Thêm nhân viên
    try:
        nguoi = Nguoi(
            id=None,
            username=username,
            pin=None,
            full_name=full_name,
            age=age,
            address=address,
            phone=phone,
            gender=None,
            role='user',
            shift=shift,
            status='working',
            avatar_url=None,
            created_at=None,
            updated_at=None
        )
        nguoi_id = nguoi_repo.add(nguoi)
        
        # Khởi tạo shift_attendance/checklog/KPI nếu đang trong ca làm việc
        try:
            tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now_local = datetime.now(tz)
            today = now_local.date()
            shift_name = current_shift(now_local)
            
            if shift_name in ('day', 'night') and (shift_name == shift):
                # 1) Tạo shift_attendance
                nguoi_repo.upsert_shift_attendance(user_id=int(nguoi_id), date_only=today, shift=shift_name, last_seen=None)
                
                # 2) Tạo checklog pending nếu chưa có
                existing_checklog = nguoi_repo.find_checklog_by_user_and_date(int(nguoi_id), today)
                if not existing_checklog:
                    with nguoi_repo as cursor:
                        sql = "INSERT INTO checklog (user_id, date, shift, status, note) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(sql, (int(nguoi_id), today, shift_name, 'pending', 'Auto-created on user add'))
                
                # 3) Tạo KPI khởi tạo nếu chưa có
                kpi_res = get_kpi_by_user_and_date_service(int(nguoi_id), today.strftime('%Y-%m-%d'))
                if not kpi_res.get('success'):
                    add_kpi_service(
                        user_id=int(nguoi_id),
                        date=today.strftime('%Y-%m-%d'),
                        emotion_score=100.0,
                        attendance_score=100.0,
                        total_score=100.0,
                        remark='Auto-init on user add'
                    )
                print(f"[user-add] Đã khởi tạo shift_attendance/checklog/KPI cho user_id={nguoi_id}, ca={shift_name}, ngày={today}")
            else:
                print(f"[user-add] Thêm nhân viên user_id={nguoi_id} ngoài ca ({shift_name}). Sẽ được khởi tạo vào đầu ca kế tiếp.")
        except Exception as e:
            print(f"[user-add] Lỗi khi khởi tạo shift_attendance/checklog/KPI: {e}")
            traceback.print_exc()
            # Không fail toàn bộ request, chỉ log lỗi
            
    except Exception as e:
        return JSONResponse(content={"success": False, "message": f"Lỗi khi thêm nhân viên: {e}"}, status_code=500)

    return JSONResponse(content={"success": True, "message": "Đã thêm mới nhân viên và tài khoản thành công", "user_id": nguoi_id, "username": username})
