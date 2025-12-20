"""
KPI Calculator Service
----------------------
Tính toán KPI dựa trên emotion logs và attendance (checklog).

KPI Calculation Logic:
1. Emotion Score (0-100):
   - Base: 100
   - For each bad emotion (Anger, Fear, Sad, Disgust, Surprise):
     * Penalty based on confidence and frequency
   
2. Attendance Score (0-100):
   - Base: 100
   - Late: -10 points
   - Early checkout: -5 points
   - Insufficient hours: additional penalty
   
3. Total Score: (Emotion Score + Attendance Score) / 2
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

# Bad emotions that reduce KPI
BAD_EMOTIONS = ['Anger', 'Fear', 'Sad', 'Disgust', 'Surprise']

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


def calculate_emotion_score(user_id: int, date_local) -> float:
    """Calculate emotion score for a user on a specific date.
    
    Logic:
    - Start with 100 points
    - For each bad emotion in emotion_log for that day:
      * Deduct points based on confidence
      * More bad emotions = more deductions
    
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
        
        score = 100.0
        bad_emotion_count = 0
        
        for log in emotion_logs:
            emotion_type = log.emotion_type
            confidence = log.confidence
            
            if emotion_type in BAD_EMOTIONS:
                # Deduct points based on confidence
                # High confidence bad emotion = bigger penalty
                penalty = confidence * 2.0  # Max 2 points per bad emotion
                score -= penalty
                bad_emotion_count += 1
        
        # Additional penalty for frequent bad emotions
        if bad_emotion_count > 10:
            score -= (bad_emotion_count - 10) * 0.5
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))
        
    except Exception:
        return 100.0  # Default to perfect score on error


def calculate_attendance_score(checklog: dict, shift: str) -> float:
    """Calculate attendance score based on checklog data.
    
    Logic:
    - Start with 100 points
    - Late: -10 points
    - Early checkout: -5 points
    - Worked less than expected: -5 points per missing hour
    
    Returns: score between 0 and 100
    """
    try:
        score = 100.0
        status = checklog.get('status', '')
        
        # Penalty for late check-in
        if status == 'late':
            score -= 10.0
        
        # Penalty for early checkout
        if status == 'early':
            score -= 5.0
        
        # Check worked hours vs expected hours
        total_hours = checklog.get('total_hours')
        if total_hours is not None:
            expected_hours = get_shift_hours(shift)
            if total_hours < expected_hours:
                # Deduct 5 points per missing hour
                missing_hours = expected_hours - total_hours
                score -= missing_hours * 5.0
        
        # Absent = 0 score
        if status == 'absent':
            return 0.0
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))
        
    except Exception:
        return 100.0  # Default to perfect score on error


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
        
        shift = checklog.get('shift', 'day')
        
        # Calculate individual scores
        emotion_score = calculate_emotion_score(user_id, date_local)
        attendance_score = calculate_attendance_score(checklog, shift)
        
        # Total score is average of both
        total_score = (emotion_score + attendance_score) / 2.0
        
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
