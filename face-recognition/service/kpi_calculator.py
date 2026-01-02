"""
KPI Calculator Service
----------------------
Tính toán KPI dựa trên emotion logs và attendance (checklog).

KPI Calculation Logic (UPDATED 2025-12-21):
1. Emotion Score (0-100):
   - Base: 100
   - CHỈ trừ điểm khi serving_time=True (đang phục vụ khách)
   - Sử dụng session tracking: chỉ trừ 1 lần/session (nhóm theo time window 5 phút)
   - Với mỗi session: trừ emotion XẤU NHẤT
   - Penalties: Anger(-8), Disgust(-7), Fear(-6), Sad(-5), Surprise(-3)
   
2. Attendance Score (0-100):
   - Late: -10 points
   - Early checkout: -10 points (thay vì -5)
   - Missing hours + Absences: 
     min(80 * (total_hours - missing_hours - absence_hours + 1) / total_hours, 80)
     → Tối đa 80 điểm, cho phép tối đa 1 giờ vắng
   - Absent: 0 points
   
3. Total Score: checklog_score * 0.7 + emotion_score * 0.3 (thay vì 50-50)
"""

from datetime import datetime, time, timedelta
import pytz
from db.nguoi_repository import NguoiRepository
from utils.shift_config import (
    SHIFT_DAY_START,
    SHIFT_DAY_END,
    SHIFT_NIGHT_START,
    SHIFT_NIGHT_END,
)

TZ = pytz.timezone('Asia/Ho_Chi_Minh')
nguoi_repo = NguoiRepository()

# Bad emotions from emonet output
BAD_EMOTIONS = ['Anger', 'Fear', 'Sad', 'Disgust', 'Surprise']
BAD_EMOTIONS_LOWER = {e.lower() for e in BAD_EMOTIONS}

def get_shift_hours(shift: str) -> float:
    """Get expected work hours for a shift."""
    if shift == 'day':
        start = datetime.combine(datetime.today(), SHIFT_DAY_START)
        end = datetime.combine(datetime.today(), SHIFT_DAY_END)
    elif shift == 'night':
        start = datetime.combine(datetime.today(), SHIFT_NIGHT_START)
        end = datetime.combine(datetime.today(), SHIFT_NIGHT_END)
    else:
        return 8.0  # default
    
    return (end - start).total_seconds() / 3600.0


def group_emotions_by_session(emotion_logs, window_minutes=5) -> list:
    """Group emotion logs into sessions based on time proximity.
    
    Logic: If two logs are more than 'window_minutes' apart → new session
    
    Returns: list of sessions, each session is a list of emotion logs
    """
    if not emotion_logs:
        return []
    
    # Sort by timestamp
    sorted_logs = sorted(emotion_logs, key=lambda x: x.captured_at if hasattr(x, 'captured_at') else x.get('captured_at'))
    
    sessions = []
    current_session = [sorted_logs[0]]
    
    for i in range(1, len(sorted_logs)):
        prev_log = sorted_logs[i - 1]
        curr_log = sorted_logs[i]
        
        prev_time = prev_log.captured_at if hasattr(prev_log, 'captured_at') else prev_log.get('captured_at')
        curr_time = curr_log.captured_at if hasattr(curr_log, 'captured_at') else curr_log.get('captured_at')
        
        # Ensure timezone-aware comparison
        if prev_time.tzinfo is None:
            prev_time = TZ.localize(prev_time)
        if curr_time.tzinfo is None:
            curr_time = TZ.localize(curr_time)
        
        time_gap = (curr_time - prev_time).total_seconds()
        
        if time_gap > window_minutes * 60:
            # Start new session
            sessions.append(current_session)
            current_session = [curr_log]
        else:
            current_session.append(curr_log)
    
    if current_session:
        sessions.append(current_session)
    
    return sessions


def calculate_emotion_score(user_id: int, date_local) -> float:
    """Calculate emotion score for a user on a specific date.
    
    NEW Logic (2025-12-21 - UPDATED):
    - Start with 100 points
    - CHỈ trừ điểm khi serving_time=True (đang phục vụ khách)
    - Session được xác định: không phát hiện khách 2 lần liên tiếp → hết session
    - Với MỖI session: CHỈ trừ emotion TIÊU CỰC ĐẦU TIÊN (đơn giản hóa)
    
    Returns: score between 0 and 100
    """
    try:
        # Get all emotion logs for this user on this date
        start_ts = datetime.combine(date_local, time.min).replace(tzinfo=TZ)
        end_ts = datetime.combine(date_local, time.max).replace(tzinfo=TZ)
        
        emotion_logs = nguoi_repo.query_emotion_logs(
            user_id=user_id,
            start_ts=start_ts,
            end_ts=end_ts
        )
        
        if not emotion_logs:
            return 100.0  # No emotion data = perfect score
        
        # Fixed penalty per emotion type
        PENALTIES = {
            'anger': 8.0,
            'angry': 8.0,
            'disgust': 7.0,
            'sad': 5.0,
            'fear': 6.0,
            'surprise': 3.0,
        }
        
        # Filter logs: CHỈ giữ lại những log khi đang phục vụ khách
        # Logic: serving_time được set bởi mark_seen()
        # - is_serving=True → serving_time=True
        # - is_serving=False 2 lần liên tiếp → serving_time=False (hết session)
        filtered_logs = []
        for log in emotion_logs:
            # Get shift_attendance at the time of this emotion log
            log_time = log.captured_at if hasattr(log, 'captured_at') else log.get('captured_at')
            if log_time.tzinfo is None:
                log_time = TZ.localize(log_time)
            
            # Query shift_attendance for this moment
            shift = nguoi_repo.get_by_id(user_id).shift
            attendance = nguoi_repo.get_shift_attendance(
                user_id=user_id,
                date_only=log_time.date(),
                shift=shift
            )
            
            # CHỈ trừ điểm nếu serving_time=True
            if attendance and attendance.get('serving_time') == True:
                filtered_logs.append(log)
        
        if not filtered_logs:
            return 100.0  # No emotions while serving = perfect score
        
        # Group filtered logs into sessions
        # Session tự động phân tách nhờ logic no_serving_count trong mark_seen()
        sessions = group_emotions_by_session(filtered_logs, window_minutes=5)
        
        score = 100.0
        
        # NEW LOGIC: Trừ điểm EMOTION TIÊU CỰC ĐẦU TIÊN trong mỗi session
        for session in sessions:
            # Tìm emotion tiêu cực ĐẦU TIÊN
            first_bad_emotion_penalty = 0.0
            for log in session:
                emotion = (log.emotion_type or '' if hasattr(log, 'emotion_type') else log.get('emotion_type', '')).strip().lower()
                penalty = PENALTIES.get(emotion, 0.0)
                if penalty > 0:  # Tìm thấy emotion tiêu cực đầu tiên
                    first_bad_emotion_penalty = penalty
                    break  # Dừng lại, không tìm nữa
            
            # Trừ điểm emotion đầu tiên (nếu có)
            if first_bad_emotion_penalty > 0:
                score -= first_bad_emotion_penalty
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))
        
    except Exception as e:
        print(f"[ERROR] calculate_emotion_score: {e}")
        return 100.0  # Default to perfect score on error


def calculate_attendance_score(checklog: dict, shift: str, user_id: int, date_local) -> float:
    """Calculate attendance score based on checklog data.
    
    NEW Logic (2025-12-21):
    - Absent (or check_in is NULL): 0 points
    - Late: -10 points
    - Early: -10 points  
    - Missing hours + Absences: 
      min(80 * (expected_hours - missing_hours - absence_hours + 1) / expected_hours, 80)
      → Tối đa 80 điểm, cho phép tối đa 1 giờ vắng
    
    Returns: score between 0 and 100
    """
    try:
        status = checklog.get('status', '')
        check_in = checklog.get('check_in')
        
        # Absent = 0 score
        if status == 'absent':
            return 0.0
        
        # NEW: If check_in is NULL, treat as absent (0 score)
        if check_in is None:
            print(f"[KPI] user_id={user_id} has NULL check_in → attendance_score = 0")
            return 0.0
        
        score = 100.0
        
        # Penalty for late check-in: -10 điểm
        if status == 'late':
            score -= 10.0
        
        # Penalty for early checkout: -10 điểm (thay đổi từ -5)
        if status == 'early':
            score -= 10.0
        
        # Check worked hours vs expected hours
        total_hours = checklog.get('total_hours')
        if total_hours is not None:
            expected_hours = get_shift_hours(shift)  # 6.0 hours
            
            # Get absence_count and convert to hours
            try:
                absence_count = nguoi_repo.get_absence_count_for_shift(
                    user_id=user_id,
                    date_only=date_local,
                    shift=shift
                )
                # Each absence = 10 seconds
                absence_hours = (absence_count * 10) / 3600.0
            except Exception:
                absence_hours = 0.0
            
            # Calculate missing hours (expected - actual)
            missing_hours = max(0.0, expected_hours - total_hours)
            
            # NEW FORMULA (FIXED 2025-12-21):
            # hours_score = min(80 * (expected - missing - absence + 1) / expected, 80) + 20
            # - 80 điểm: Quá trình làm việc (tối đa 80)
            # - 20 điểm: Base cho on_time (10 đi đúng giờ + 10 về đúng giờ)
            # - Trừ 10 nếu late, trừ 10 nếu early
            if expected_hours > 0:
                hours_component = 80.0 * (expected_hours - missing_hours - absence_hours + 1.0) / expected_hours
                hours_component = min(hours_component, 80.0)  # Cap at 80
                hours_component = max(hours_component, 0.0)   # Floor at 0
                
                # Add 20 base points (10 for on-time check-in + 10 for on-time check-out)
                hours_score = hours_component + 20.0
            else:
                hours_score = 100.0
            
            # Start from hours_score, then subtract penalties
            score = hours_score
            if status == 'late':
                score -= 10.0
            if status == 'early':
                score -= 10.0
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))
        
    except Exception as e:
        print(f"[ERROR] calculate_attendance_score: {e}")
        import traceback
        traceback.print_exc()
        return 0.0  # Return 0 on error (was 100.0 - BUG FIX)


def calculate_kpi_for_user_date(user_id: int, date_local) -> dict:
    """Calculate complete KPI for a user on a specific date.
    
    Returns:
        {
            'emotion_score': float (0-100),
            'attendance_score': float (0-100),
            'total_score': float (0-100),
            'remark': str
        }
    """
    try:
        # Get checklog for this date
        checklog = nguoi_repo.find_checklog_by_user_and_date(user_id, date_local)
        
        if not checklog:
            # No checklog = absent
            return {
                'emotion_score': 0.0,
                'attendance_score': 0.0,
                'total_score': 0.0,
                'remark': 'No checklog found (absent)'
            }
        
        # NEW: Check if check_in is NULL (pending or not checked in)
        check_in = checklog.get('check_in')
        if check_in is None:
            print(f"[KPI] user_id={user_id} has checklog but check_in is NULL → KPI = 0")
            return {
                'emotion_score': 0.0,
                'attendance_score': 0.0,
                'total_score': 0.0,
                'remark': 'No check-in (pending or absent)'
            }
        
        shift = checklog.get('shift', 'day')
        
        # Calculate individual scores
        emotion_score = calculate_emotion_score(user_id, date_local)
        attendance_score = calculate_attendance_score(checklog, shift, user_id, date_local)
        
        # NEW FORMULA: Total score = checklog * 0.7 + emotion * 0.3 (thay vì 50-50)
        total_score = (attendance_score * 0.7) + (emotion_score * 0.3)
        
        # Generate remark
        remarks = []
        if emotion_score < 80:
            remarks.append('Poor emotion performance')
        if attendance_score < 80:
            remarks.append('Attendance issues')
        if checklog.get('status') == 'late':
            remarks.append('Late check-in')
        if checklog.get('status') == 'early':
            remarks.append('Early checkout')
        
        remark = '; '.join(remarks) if remarks else 'Good performance'
        
        return {
            'emotion_score': round(emotion_score, 2),
            'attendance_score': round(attendance_score, 2),
            'total_score': round(total_score, 2),
            'remark': remark
        }
        
    except Exception as e:
        return {
            'emotion_score': 100.0,
            'attendance_score': 100.0,
            'total_score': 100.0,
            'remark': f'Error calculating KPI: {e}'
        }
