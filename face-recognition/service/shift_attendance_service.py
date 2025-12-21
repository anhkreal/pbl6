from datetime import datetime, time, timedelta
import threading
import time as systime
import pytz
from db.nguoi_repository import NguoiRepository
from utils.shift_config import (
    SHIFT_DAY_START,
    SHIFT_DAY_END,
    SHIFT_NIGHT_START,
    SHIFT_NIGHT_END,
)
from service.kpi_service import (
    get_kpi_by_user_and_date_service,
    add_kpi_service,
    update_kpi_service,
)
from service.attendance_absence_service import generate_absent_report

TZ = pytz.timezone('Asia/Ho_Chi_Minh')
ABSENCE_THRESHOLD_SECONDS = 30
INCREMENT_INTERVAL_SECONDS = 10

# Emotion penalty weights
EMOTION_PENALTIES = {
    'Anger': 8.0,
    'Fear': 6.0,
    'Sad': 5.0,
    'Disgust': 7.0,
    'Surprise': 3.0
}

nguoi_repo = NguoiRepository()


def current_shift(now_local: datetime | None = None) -> str:
    now_local = now_local or datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
    t = now_local.time()
    if SHIFT_DAY_START <= t < SHIFT_DAY_END:
        return 'day'
    if SHIFT_NIGHT_START <= t < SHIFT_NIGHT_END:
        return 'night'
    # Outside shift windows: return the last ended shift for consistency
    return 'none'


def init_shift_rows(shift_name: str, date_local):
    """Initialize shift_attendance rows, checklog, and KPI for all working users of the given shift and date.
    
    For each employee in the shift:
    - Create shift_attendance row for tracking
    - Create checklog with status 'pending' (waiting for check-in)
    - Create KPI initialized with emotion_score=100, attendance_score=100, total_score=100
    """
    try:
        users = nguoi_repo.list_users_by_shift_status(shift=shift_name, status='working')
        date_str = date_local.strftime('%Y-%m-%d')
        print(f"[shift-init] Bắt đầu khởi tạo ca '{shift_name}' cho ngày {date_str}. Tổng nhân viên: {len(users)}")
        
        for u in users:
            uid = u.get('id')
            if uid is None:
                continue
            
            user_id = int(uid)
            
            # 1. Create shift_attendance row
            nguoi_repo.upsert_shift_attendance(user_id=user_id, date_only=date_local, shift=shift_name, last_seen=None)
            print(f"[shift-init] Đã khởi tạo shift_attendance cho user_id={user_id}, ca={shift_name}, ngày={date_str}")
            
            # 2. Create checklog with status 'pending' if not exists
            existing_checklog = nguoi_repo.find_checklog_by_user_and_date(user_id, date_local)
            if not existing_checklog:
                try:
                    # Insert checklog without check_in (waiting for actual check-in)
                    with nguoi_repo as cursor:
                        sql = "INSERT INTO checklog (user_id, date, shift, status, note) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(sql, (user_id, date_local, shift_name, 'pending', 'Auto-created at shift start'))
                except Exception:
                    pass  # If already exists, skip
                else:
                    print(f"[shift-init] Đã tạo checklog 'pending' cho user_id={user_id}, ca={shift_name}, ngày={date_str}")
            
            # 3. Create KPI initialized with full scores if not exists
            try:
                kpi_res = get_kpi_by_user_and_date_service(user_id, date_str)
                if not kpi_res.get('success'):
                    # Create new KPI with initial perfect scores
                    add_kpi_service(
                        user_id=user_id,
                        date=date_str,
                        emotion_score=100.0,
                        attendance_score=100.0,
                        total_score=100.0,
                        remark='Auto-initialized at shift start'
                    )
            except Exception:
                pass  # If already exists, skip
            else:
                print(f"[shift-init] Đã khởi tạo KPI 100/100/100 cho user_id={user_id}, ngày={date_str}")
        
        print(f"[shift-init] Hoàn tất khởi tạo ca '{shift_name}' cho ngày {date_str}")
        return True
    except Exception:
        return False


def needs_initialization_for_shift(shift_name: str, date_local) -> bool:
    """Return True if any working user is missing a shift_attendance row for the given shift and date."""
    try:
        users = nguoi_repo.list_users_by_shift_status(shift=shift_name, status='working')
        missing_found = False
        for u in users:
            uid = u.get('id')
            if uid is None:
                continue
            row = nguoi_repo.get_shift_attendance(user_id=int(uid), date_only=date_local, shift=shift_name)
            if not row:
                missing_found = True
                break
        return missing_found
    except Exception:
        return False

def mark_seen(user_id: int, is_serving: bool = False):
    """Mark user as seen and update serving status.
    
    Args:
        user_id: ID of the user
        is_serving: True if user is currently serving a customer
    
    Logic:
        - Update last_seen to current time
        - If is_serving=True: set serving_time=True (employee is serving)
        - If is_serving=False: increment no_serving_count
          * If no_serving_count >= 2: set serving_time=False and reset counter
    """
    now_local = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
    shift_name = current_shift(now_local)
    if shift_name == 'none':
        return False
    
    # Get current shift_attendance record
    row = nguoi_repo.get_shift_attendance(user_id=int(user_id), date_only=now_local.date(), shift=shift_name)
    
    if is_serving:
        # User is serving customer → set serving_time=True, reset counter
        nguoi_repo.upsert_shift_attendance(
            user_id=int(user_id), 
            date_only=now_local.date(), 
            shift=shift_name, 
            last_seen=now_local,
            serving_time=True,
            no_serving_count=0
        )
        print(f"[seen] user_id={user_id} đang phục vụ khách (serving_time=True). Ca={shift_name}")
    else:
        # User is not serving customer → increment counter
        if row:
            no_serving_count = row.get('no_serving_count', 0) or 0
            serving_time = row.get('serving_time', False)
            
            # Increment counter
            no_serving_count += 1
            
            # After 2 consecutive non-serving detections → set serving_time=False
            if no_serving_count >= 2:
                serving_time = False
                no_serving_count = 0  # Reset counter
                print(f"[seen] user_id={user_id} ngừng phục vụ sau 2 lần liên tiếp không phục vụ → serving_time=False")
            
            nguoi_repo.upsert_shift_attendance(
                user_id=int(user_id),
                date_only=now_local.date(),
                shift=shift_name,
                last_seen=now_local,
                serving_time=serving_time,
                no_serving_count=no_serving_count
            )
        else:
            # First time seeing this user today
            nguoi_repo.upsert_shift_attendance(
                user_id=int(user_id),
                date_only=now_local.date(),
                shift=shift_name,
                last_seen=now_local,
                serving_time=False,
                no_serving_count=1
            )
            print(f"[seen] Lần đầu ghi nhận user_id={user_id} hôm nay. no_serving_count=1, serving_time=False")
    
    return True


def increment_absences_for_inactive(shift_name: str | None = None):
    nguoi_repo.increment_absence_if_inactive(threshold_seconds=ABSENCE_THRESHOLD_SECONDS, shift=shift_name)


def finalize_shift_absents(shift_name: str, date_local):
    """At shift end, handle users without checklog or without checkout.
    
    UPDATED 2025-12-21 with GRACE PERIOD:
    - Được gọi SAU grace period 30 phút (14:30 cho ca sáng, 20:30 cho ca tối)
    - Grace period cho nhân viên thời gian checkout

    1. Users without any checklog:
       - Insert checklog with status 'absent'
       - Set KPI to 0/0/0
    
    2. Users with check-in but no check-out:
       - Auto checkout tại thời điểm KẾT THÚC CA (14:00 hoặc 20:00)
       - KHÔNG trừ điểm early (vì trong grace period)
       - Recalculate KPI
    """
    try:
        from service.kpi_calculator import calculate_kpi_for_user_date
        
        users = nguoi_repo.list_users_by_shift_status(shift=shift_name, status='working')
        
        # Determine shift end time (KHÔNG phải 5 phút trước nữa)
        if shift_name == 'day':
            shift_end = datetime.combine(date_local, SHIFT_DAY_END).replace(tzinfo=TZ)
        else:
            shift_end = datetime.combine(date_local, SHIFT_NIGHT_END).replace(tzinfo=TZ)
        
        # Auto checkout time = ĐÚNG GIỜ KẾT THÚC CA (không trừ 5 phút)
        auto_checkout_time = shift_end
        
        for u in users:
            uid = u.get('id')
            if uid is None:
                continue
            
            existing = nguoi_repo.find_checklog_by_user_and_date(int(uid), date_local)
            
            if not existing:
                # Case 1: No checklog at all → Mark absent
                try:
                    nguoi_repo.add_absence(user_id=int(uid), shift=shift_name, edited_by=None, note='auto-absent')
                except Exception:
                    pass
                
                # Ensure KPI exists and is zeroed
                try:
                    date_str = date_local.strftime('%Y-%m-%d')
                    kpi_res = get_kpi_by_user_and_date_service(int(uid), date_str)
                    if kpi_res.get('success') and kpi_res.get('kpi'):
                        k = kpi_res['kpi']
                        update_kpi_service(k['id'], int(uid), date_str, 0.0, 0.0, 0.0, (k.get('remark') or ''))
                    else:
                        add_kpi_service(int(uid), date_str, 0.0, 0.0, 0.0, 'auto-absent')
                except Exception:
                    pass
            
            elif existing.get('check_in') and not existing.get('check_out'):
                # Case 2: Check-in but no check-out → Auto checkout tại GIỜ KẾT THÚC CA
                print(f"[finalize] Auto checkout cho user_id={uid} lúc {shift_end.strftime('%H:%M')} (quên checkout trong grace period)")
                
                try:
                    check_in_time = existing.get('check_in')
                    if check_in_time.tzinfo is None:
                        check_in_time = TZ.localize(check_in_time)
                    
                    # Calculate total hours with absences
                    total_seconds = (auto_checkout_time - check_in_time).total_seconds()
                    
                    try:
                        absence_count = nguoi_repo.get_absence_count_for_shift(
                            user_id=int(uid),
                            date_only=date_local,
                            shift=shift_name
                        )
                    except Exception:
                        absence_count = 0
                    
                    absent_seconds = (absence_count or 0) * 10
                    if absent_seconds > 0:
                        total_seconds = max(0.0, total_seconds - absent_seconds)
                    
                    total_hours = round(total_seconds / 3600.0, 2)
                    if total_seconds > 0 and total_hours == 0.0:
                        total_hours = 0.01
                    
                    # NEW: Giữ status hiện tại (on_time/late)
                    # KHÔNG đặt early vì checkout đúng giờ kết thúc ca
                    current_status = existing.get('status')
                    new_status = current_status if current_status in ['late', 'on_time'] else 'on_time'
                    
                    nguoi_repo.update_checkin_checkout(
                        row_id=existing.get('id'),
                        check_out=auto_checkout_time.replace(tzinfo=None),
                        total_hours=total_hours,
                        status=new_status,
                        edited_by=None,
                        note='Auto checkout at shift end (within grace period)'
                    )
                    
                    # Recalculate KPI
                    try:
                        kpi_data = calculate_kpi_for_user_date(int(uid), date_local)
                        date_str = date_local.strftime('%Y-%m-%d')
                        
                        kpi_res = get_kpi_by_user_and_date_service(int(uid), date_str)
                        if kpi_res.get('success') and kpi_res.get('kpi'):
                            kpi = kpi_res['kpi']
                            update_kpi_service(
                                kpi_id=kpi['id'],
                                user_id=int(uid),
                                date=date_str,
                                emotion_score=kpi_data['emotion_score'],
                                attendance_score=kpi_data['attendance_score'],
                                total_score=kpi_data['total_score'],
                                remark=kpi_data['remark'] + ' (auto checkout)'
                            )
                    except Exception as e:
                        print(f"[finalize] Warning: Could not update KPI for user_id={uid}: {e}")
                
                except Exception as e:
                    print(f"[finalize] Error auto checkout user_id={uid}: {e}")
        
        return True
    except Exception as e:
        print(f"[finalize] Error in finalize_shift_absents: {e}")
        return False

    # Write absent report log for this shift and date
    try:
        generate_absent_report(date=date_local.strftime('%Y-%m-%d'), shift=shift_name, write_log=True)
    except Exception:
        pass


def scheduler_loop():
    """
    Scheduler loop with GRACE PERIOD support (2025-12-21 UPDATED):
    
    - Khởi tạo ca: đúng giờ bắt đầu (08:00, 14:00)
    - GRACE PERIOD: 30 phút sau kết thúc ca (14:00-14:30, 20:00-20:30)
      * KHÔNG track absence (cho nhân viên thời gian checkout)
      * KHÔNG tính vắng
    - Finalize ca: sau 30 phút (14:30, 20:30)
    """
    last_init_day = None
    last_init_night = None
    last_finalize_day = None
    last_finalize_night = None
    
    # Grace period: 30 minutes after shift ends
    GRACE_PERIOD_MINUTES = 30
    
    while True:
        try:
            now_local = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
            current_time = now_local.time()
            
            # Calculate grace period times
            day_end_grace = (datetime.combine(now_local.date(), SHIFT_DAY_END) + timedelta(minutes=GRACE_PERIOD_MINUTES)).time()
            night_end_grace = (datetime.combine(now_local.date(), SHIFT_NIGHT_END) + timedelta(minutes=GRACE_PERIOD_MINUTES)).time()
            
            # At exact shift starts, initialize rows
            if current_time >= SHIFT_DAY_START and current_time < (datetime.combine(now_local.date(), SHIFT_DAY_START) + timedelta(minutes=1)).time():
                if last_init_day != now_local.date():
                    print(f"[scheduler] Khởi tạo ca ngày lúc {now_local.strftime('%H:%M:%S')} cho ngày {now_local.date()}")
                    init_shift_rows('day', now_local.date())
                    last_init_day = now_local.date()
                    
            if current_time >= SHIFT_NIGHT_START and current_time < (datetime.combine(now_local.date(), SHIFT_NIGHT_START) + timedelta(minutes=1)).time():
                if last_init_night != now_local.date():
                    print(f"[scheduler] Khởi tạo ca tối lúc {now_local.strftime('%H:%M:%S')} cho ngày {now_local.date()}")
                    init_shift_rows('night', now_local.date())
                    last_init_night = now_local.date()
                    
            # Catch-up initialization if backend started late but within shift hours and no rows exist yet
            if SHIFT_DAY_START <= current_time < SHIFT_DAY_END:
                if last_init_day != now_local.date() and needs_initialization_for_shift('day', now_local.date()):
                    print(f"[scheduler] Catch-up: phát hiện thiếu dữ liệu ca ngày → khởi tạo bổ sung")
                    init_shift_rows('day', now_local.date())
                    last_init_day = now_local.date()
                    
            if SHIFT_NIGHT_START <= current_time < SHIFT_NIGHT_END:
                if last_init_night != now_local.date() and needs_initialization_for_shift('night', now_local.date()):
                    print(f"[scheduler] Catch-up: phát hiện thiếu dữ liệu ca tối → khởi tạo bổ sung")
                    init_shift_rows('night', now_local.date())
                    last_init_night = now_local.date()
            
            # NEW: Finalize shift AFTER grace period (30 minutes after shift end)
            # Day shift: finalize at 14:30
            if current_time >= day_end_grace and current_time < (datetime.combine(now_local.date(), day_end_grace) + timedelta(minutes=1)).time():
                if last_finalize_day != now_local.date():
                    print(f"[scheduler] Kết thúc ca ngày (sau grace period 30p): tự động đánh vắng và cập nhật KPI lúc {now_local.strftime('%H:%M:%S')}")
                    finalize_shift_absents('day', now_local.date())
                    last_finalize_day = now_local.date()
                    
            # Night shift: finalize at 20:30
            if current_time >= night_end_grace and current_time < (datetime.combine(now_local.date(), night_end_grace) + timedelta(minutes=1)).time():
                if last_finalize_night != now_local.date():
                    print(f"[scheduler] Kết thúc ca tối (sau grace period 30p): tự động đánh vắng và cập nhật KPI lúc {now_local.strftime('%H:%M:%S')}")
                    finalize_shift_absents('night', now_local.date())
                    last_finalize_night = now_local.date()
            
            # NEW: Every 10s, increment absences ONLY if NOT in grace period
            # Grace period: 14:00-14:30 (day), 20:00-20:30 (night)
            sh = current_shift(now_local)
            
            in_grace_period = False
            if sh == 'day' and SHIFT_DAY_END <= current_time < day_end_grace:
                in_grace_period = True
                # print(f"[scheduler] Ca ngày trong grace period (14:00-14:30) → KHÔNG track absence")
            elif sh == 'night' and SHIFT_NIGHT_END <= current_time < night_end_grace:
                in_grace_period = True
                # print(f"[scheduler] Ca tối trong grace period (20:00-20:30) → KHÔNG track absence")
            
            if sh in ('day', 'night') and not in_grace_period:
                # Increment absence counts in active shift (ONLY outside grace period)
                increment_absences_for_inactive(shift_name=sh)
                
        except Exception as e:
            print(f"[scheduler] Error: {e}")
            
        systime.sleep(INCREMENT_INTERVAL_SECONDS)


def start_scheduler_background():
    th = threading.Thread(target=scheduler_loop, daemon=True)
    th.start()
    return th
