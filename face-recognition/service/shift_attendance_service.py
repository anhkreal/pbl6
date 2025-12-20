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
    """At shift end, create absent attendance + KPI=0 for working users without any checklog for the day.

    - Insert checklog with status 'absent' if none exists
    - If KPI exists: set attendance_score=0 and total_score=0
      else create KPI with both emotion_score and attendance_score = 0 (total=0)
    """
    try:
        users = nguoi_repo.list_users_by_shift_status(shift=shift_name, status='working')
        for u in users:
            uid = u.get('id')
            if uid is None:
                continue
            existing = nguoi_repo.find_checklog_by_user_and_date(int(uid), date_local)
            if existing:
                continue
            # Add absent attendance row
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
        return True
    except Exception:
        return False


def scheduler_loop():
    last_init_day = None
    last_init_night = None
    last_finalize_day = None
    last_finalize_night = None
    while True:
        try:
            now_local = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
            # At exact shift starts, initialize rows
            if now_local.time() >= SHIFT_DAY_START and now_local.time() < (datetime.combine(now_local.date(), SHIFT_DAY_START) + timedelta(minutes=1)).time():
                if last_init_day != now_local.date():
                    print(f"[scheduler] Khởi tạo ca ngày lúc {now_local.strftime('%H:%M:%S')} cho ngày {now_local.date()}")
                    init_shift_rows('day', now_local.date())
                    last_init_day = now_local.date()
            if now_local.time() >= SHIFT_NIGHT_START and now_local.time() < (datetime.combine(now_local.date(), SHIFT_NIGHT_START) + timedelta(minutes=1)).time():
                if last_init_night != now_local.date():
                    print(f"[scheduler] Khởi tạo ca tối lúc {now_local.strftime('%H:%M:%S')} cho ngày {now_local.date()}")
                    init_shift_rows('night', now_local.date())
                    last_init_night = now_local.date()
            # Catch-up initialization if backend started late but within shift hours and no rows exist yet
            if SHIFT_DAY_START <= now_local.time() < SHIFT_DAY_END:
                if last_init_day != now_local.date() and needs_initialization_for_shift('day', now_local.date()):
                    print(f"[scheduler] Catch-up: phát hiện thiếu dữ liệu ca ngày → khởi tạo bổ sung")
                    init_shift_rows('day', now_local.date())
                    last_init_day = now_local.date()
            if SHIFT_NIGHT_START <= now_local.time() < SHIFT_NIGHT_END:
                if last_init_night != now_local.date() and needs_initialization_for_shift('night', now_local.date()):
                    print(f"[scheduler] Catch-up: phát hiện thiếu dữ liệu ca tối → khởi tạo bổ sung")
                    init_shift_rows('night', now_local.date())
                    last_init_night = now_local.date()
            # At shift end, auto finalize absentees and zero KPI if needed
            if now_local.time() >= SHIFT_DAY_END and now_local.time() < (datetime.combine(now_local.date(), SHIFT_DAY_END) + timedelta(minutes=1)).time():
                if last_finalize_day != now_local.date():
                    print(f"[scheduler] Kết thúc ca ngày: tự động đánh vắng và cập nhật KPI")
                    finalize_shift_absents('day', now_local.date())
                    last_finalize_day = now_local.date()
            if now_local.time() >= SHIFT_NIGHT_END and now_local.time() < (datetime.combine(now_local.date(), SHIFT_NIGHT_END) + timedelta(minutes=1)).time():
                if last_finalize_night != now_local.date():
                    print(f"[scheduler] Kết thúc ca tối: tự động đánh vắng và cập nhật KPI")
                    finalize_shift_absents('night', now_local.date())
                    last_finalize_night = now_local.date()
            # Every 10s, increment absences for current shift if last_seen > 30s
            sh = current_shift(now_local)
            if sh in ('day', 'night'):
                # Increment absence counts in active shift
                increment_absences_for_inactive(shift_name=sh)
        except Exception:
            pass
        systime.sleep(INCREMENT_INTERVAL_SECONDS)


def start_scheduler_background():
    th = threading.Thread(target=scheduler_loop, daemon=True)
    th.start()
    return th
