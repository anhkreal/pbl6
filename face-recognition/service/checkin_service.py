from db.nguoi_repository import NguoiRepository
from datetime import datetime
import pytz
from utils.shift_config import SHIFT_DAY_START, SHIFT_NIGHT_START, SHIFT_DAY_END, SHIFT_NIGHT_END, get_shift_by_time

# timezone for Vietnam (UTC+7)
TZ = pytz.timezone('Asia/Ho_Chi_Minh')

nguoi_repo = NguoiRepository()


def checkin_service(user_id: int, edited_by: int = None, note: str = None):
    """Create or update check-in for user_id. Determine lateness based on shift:
    - 'day' shift cutoff: SHIFT_DAY_START local
    - 'night' shift cutoff: SHIFT_NIGHT_START local

    Logic:
    1. Kiểm tra nhân viên có đang trong ca làm việc không
    2. Find existing checklog for today
    3. If found and check_in is NULL (status='pending' or 'absent'):
       - Update with actual check_in time
       - Update status to 'on_time' or 'late'
    4. If not found:
       - Create new checklog with check_in
       - Create new KPI if not exists
    5. Ensure KPI exists for this user and date

    Store check_in datetime (UTC) and return the created record id and status.
    """
    try:
        from service.kpi_service import get_kpi_by_user_and_date_service, add_kpi_service
        
        user = nguoi_repo.get_by_id(int(user_id))
        if not user:
            return {"success": False, "message": "Không tìm thấy user", "status_code": 404}

        shift = getattr(user, 'shift', 'day')

        # use local time (UTC+7) for cutoff comparison
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        now_local = now_utc.astimezone(TZ)
        current_time = now_local.time()
        
        # Kiểm tra nhân viên có trong ca làm việc không
        current_shift = get_shift_by_time(current_time)
        
        # Nếu không trong ca nào cả (none) hoặc ca hiện tại khác ca của nhân viên
        if current_shift == 'none':
            return {
                "success": False, 
                "message": f"Không thể check-in ngoài giờ làm việc. Giờ làm việc: Ca sáng {SHIFT_DAY_START.strftime('%H:%M')}-{SHIFT_DAY_END.strftime('%H:%M')}, Ca chiều {SHIFT_NIGHT_START.strftime('%H:%M')}-{SHIFT_NIGHT_END.strftime('%H:%M')}", 
                "status_code": 403
            }
        
        if current_shift != shift:
            return {
                "success": False, 
                "message": f"Không thể check-in vào ca {current_shift}. Bạn được phân ca {shift}", 
                "status_code": 403
            }

        # Determine cutoff time based on shift
        cutoff = SHIFT_NIGHT_START if shift == 'night' else SHIFT_DAY_START

        # Check if there's already a checklog for this user on the local date
        existing = nguoi_repo.find_checklog_by_user_and_date(user_id=int(user_id), date_only=now_local.date())
        
        # Determine status based on time
        status = 'on_time' if now_local.time() <= cutoff else 'late'
        
        if existing:
            # Checklog exists
            check_in_time = existing.get('check_in')
            
            if check_in_time is None:
                # No check_in yet (status might be 'pending' or 'absent')
                # Update with actual check_in time
                try:
                    with nguoi_repo as cursor:
                        sql = """
                        UPDATE checklog
                        SET check_in = %s, status = %s, edited_by = COALESCE(%s, edited_by), note = COALESCE(%s, note)
                        WHERE id = %s
                        """
                        cursor.execute(sql, (now_local, status, edited_by, note, existing.get('id')))
                    
                    # Ensure KPI exists
                    date_str = now_local.date().strftime('%Y-%m-%d')
                    kpi_res = get_kpi_by_user_and_date_service(int(user_id), date_str)
                    if not kpi_res.get('success'):
                        # Create KPI with initial scores
                        add_kpi_service(
                            user_id=int(user_id),
                            date=date_str,
                            emotion_score=100.0,
                            attendance_score=100.0,
                            total_score=100.0,
                            remark='Created at check-in'
                        )
                    
                    return {"success": True, "id": existing.get('id'), "status": status, "message": "Check-in updated successfully"}
                except Exception as e:
                    return {"success": False, "message": f"Không thể cập nhật check-in: {e}", "status_code": 500}
            else:
                # Already checked in
                return {"success": False, "message": "Đã tồn tại check-in cho user này vào ngày hôm nay", "status_code": 409}
        else:
            # No checklog exists - create new one
            try:
                # Create checklog
                rowid = nguoi_repo.add_checkin(user_id=int(user_id), shift=shift, status=status, edited_by=edited_by, note=note)
                
                if rowid:
                    # Ensure KPI exists
                    date_str = now_local.date().strftime('%Y-%m-%d')
                    kpi_res = get_kpi_by_user_and_date_service(int(user_id), date_str)
                    if not kpi_res.get('success'):
                        # Create KPI with initial scores
                        add_kpi_service(
                            user_id=int(user_id),
                            date=date_str,
                            emotion_score=100.0,
                            attendance_score=100.0,
                            total_score=100.0,
                            remark='Created at check-in'
                        )
                    
                    return {"success": True, "id": rowid, "status": status, "message": "Check-in created successfully"}
                else:
                    return {"success": False, "message": "Không thể tạo check-in", "status_code": 500}
            except Exception as e:
                return {"success": False, "message": f"Lỗi khi tạo check-in: {e}", "status_code": 500}
                
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi tạo check-in: {e}", "status_code": 500}
