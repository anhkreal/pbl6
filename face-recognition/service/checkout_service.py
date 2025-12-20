from datetime import datetime
import pytz
from db.nguoi_repository import NguoiRepository
from utils.shift_config import SHIFT_DAY_END, SHIFT_NIGHT_END, get_shift_by_time, SHIFT_DAY_START, SHIFT_NIGHT_START
from service.kpi_calculator import calculate_kpi_for_user_date
from service.kpi_service import get_kpi_by_user_and_date_service, update_kpi_service


nguoi_repo = NguoiRepository()


def checkout(user_id: int, edited_by: int = None, note: str = None):
    """Perform checkout for a user.

    Behavior:
    - Uses Asia/Ho_Chi_Minh local time consistently.
    - Kiểm tra nhân viên có đang trong ca làm việc không
    - Allows multiple checkouts in a day by overwriting the checkout time and total_hours.
    - Computes total time = checkout - checkin - (absence_count * 10 seconds).
    - Early status if checkout before shift end (day: SHIFT_DAY_END, night: SHIFT_NIGHT_END).
    - After checkout, recalculate and update KPI based on:
      * Emotion logs for the day
      * Checklog data (late, early, total_hours)
      * Shift requirements
    
    Requirements:
    - Must have check_in time (cannot checkout without check-in)
    - Can checkout multiple times (updates checkout time each time)
    - KPI is recalculated after each checkout
    """
    TZ = pytz.timezone('Asia/Ho_Chi_Minh')
    try:
        # Get user info
        user = nguoi_repo.get_by_id(int(user_id))
        if not user:
            return {"success": False, "message": "Không tìm thấy user", "status_code": 404}
        
        shift = getattr(user, 'shift', 'day')
        
        # compute now in local time (UTC+7)
        now_local = datetime.now(TZ)
        current_time = now_local.time()
        
        # Kiểm tra nhân viên có trong ca làm việc không
        current_shift = get_shift_by_time(current_time)
        
        # Nếu không trong ca nào cả (none) hoặc ca hiện tại khác ca của nhân viên
        if current_shift == 'none':
            return {
                "success": False, 
                "message": f"Không thể check-out ngoài giờ làm việc. Giờ làm việc: Ca sáng {SHIFT_DAY_START.strftime('%H:%M')}-{SHIFT_DAY_END.strftime('%H:%M')}, Ca chiều {SHIFT_NIGHT_START.strftime('%H:%M')}-{SHIFT_NIGHT_END.strftime('%H:%M')}", 
                "status_code": 403
            }
        
        if current_shift != shift:
            return {
                "success": False, 
                "message": f"Không thể check-out vào ca {current_shift}. Bạn được phân ca {shift}", 
                "status_code": 403
            }

        # locate today's checklog row
        date_local = now_local.date()
        row = nguoi_repo.find_checklog_by_user_and_date(int(user_id), date_local)
        
        if not row:
            return {"success": False, "message": "Không tìm thấy checklog cho ngày hôm nay", "status_code": 404}

        # Check if check_in exists
        check_in_local = row.get('check_in')
        if check_in_local is None:
            return {"success": False, "message": "Chưa check-in, không thể check-out", "status_code": 400}

        # determine thresholds based on shift
        cutoff = SHIFT_DAY_END if shift == 'day' else SHIFT_NIGHT_END

        # decide early or not by comparing local checkout time
        is_early = now_local.time() < cutoff

        # ensure check_in_local is timezone-aware UTC+7; if naive, localize
        if check_in_local.tzinfo is None:
            check_in_local = TZ.localize(check_in_local)

        # compute total seconds then subtract absences (absence_count * 10s)
        total_seconds = (now_local - check_in_local).total_seconds()
        try:
            absence_count = nguoi_repo.get_absence_count_for_shift(user_id=int(user_id), date_only=date_local, shift=shift)
        except Exception:
            absence_count = 0
        absent_seconds = (absence_count or 0) * 10
        if absent_seconds > 0:
            total_seconds = max(0.0, total_seconds - absent_seconds)
        total_hours = round(total_seconds / 3600.0, 2)

        # Determine new status
        current_status = row.get('status')
        new_status = current_status
        
        # Update status based on checkout time
        if is_early:
            new_status = 'early'
        # Keep 'late' status if already late at check-in
        # Otherwise, mark as 'on_time' if not early
        elif current_status != 'late':
            new_status = 'on_time'

        # update the checklog row
        updated = nguoi_repo.update_checkin_checkout(
            row_id=row.get('id'), 
            check_out=now_local.replace(tzinfo=None), 
            total_hours=total_hours, 
            status=new_status, 
            edited_by=edited_by, 
            note=note
        )
        
        if not updated:
            return {"success": False, "message": "Không thể cập nhật checkout", "status_code": 500}
        
        # Recalculate KPI after checkout
        try:
            kpi_data = calculate_kpi_for_user_date(int(user_id), date_local)
            date_str = date_local.strftime('%Y-%m-%d')
            
            # Get existing KPI
            kpi_res = get_kpi_by_user_and_date_service(int(user_id), date_str)
            
            if kpi_res.get('success') and kpi_res.get('kpi'):
                # Update existing KPI
                kpi = kpi_res['kpi']
                update_kpi_service(
                    kpi_id=kpi['id'],
                    user_id=int(user_id),
                    date=date_str,
                    emotion_score=kpi_data['emotion_score'],
                    attendance_score=kpi_data['attendance_score'],
                    total_score=kpi_data['total_score'],
                    remark=kpi_data['remark']
                )
            # If KPI doesn't exist, it will be created at next check-in or by scheduler
            
        except Exception as e:
            # KPI calculation error shouldn't prevent checkout
            print(f"Warning: Could not update KPI after checkout: {e}")
        
        return {
            "success": True, 
            "id": row.get('id'), 
            "status": new_status, 
            "total_hours": total_hours,
            "message": "Checkout successful"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi checkout: {e}", "status_code": 500}
