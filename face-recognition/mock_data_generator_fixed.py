"""
Mock Data Generator for Testing (FIXED)
- emotion_log table (not emonet_logs)
- checklog has NO created_at column
- Clean script with correct schema
"""

import random
from datetime import datetime, timedelta, time
import pytz
from db.connection_helper import ConnectionHelper

# Initialize
TZ = pytz.timezone('Asia/Ho_Chi_Minh')

# Users info
USERS = [
    {'id': 10000000, 'username': 'user1', 'name': 'Nguyễn Thế Nhật', 'shift': 'night', 'bad_emotion': 'Anger'},
    {'id': 10000001, 'username': 'user2', 'name': 'Lê Văn Anh Khoa', 'shift': 'day', 'bad_emotion': 'Surprise'},
    {'id': 10000002, 'username': 'user3', 'name': 'Phan Trọng Dũng', 'shift': 'night', 'bad_emotion': 'Disgust'},
]

# Config
START_DATE = datetime(2025, 11, 1).date()
END_DATE = datetime(2025, 11, 30).date()
SHIFT_DAY_START = time(8, 0, 0)
SHIFT_DAY_END = time(14, 0, 0)
SHIFT_NIGHT_START = time(14, 0, 0)
SHIFT_NIGHT_END = time(20, 0, 0)

def get_shift_times(shift_name: str, date):
    """Get shift start and end times for a date."""
    if shift_name == 'day':
        start = datetime.combine(date, SHIFT_DAY_START).replace(tzinfo=TZ)
        end = datetime.combine(date, SHIFT_DAY_END).replace(tzinfo=TZ)
    else:  # night
        start = datetime.combine(date, SHIFT_NIGHT_START).replace(tzinfo=TZ)
        end = datetime.combine(date, SHIFT_NIGHT_END).replace(tzinfo=TZ)
    return start, end

def clean_old_data():
    """Delete old mock data for these 3 users from Nov 2025."""
    print("\n🗑️  Cleaning old data...")
    try:
        with ConnectionHelper() as cursor:
            user_ids = [10000000, 10000001, 10000002]
            user_ids_str = ','.join(map(str, user_ids))
            
            # Delete emotion logs
            cursor.execute(f"DELETE FROM emotion_log WHERE user_id IN ({user_ids_str}) AND MONTH(captured_at) = 11 AND YEAR(captured_at) = 2025")
            print(f"  ✅ Deleted emotion logs: {cursor.rowcount} rows")
            
            # Delete checklogs
            cursor.execute(f"DELETE FROM checklog WHERE user_id IN ({user_ids_str}) AND MONTH(date) = 11 AND YEAR(date) = 2025")
            print(f"  ✅ Deleted checklogs: {cursor.rowcount} rows")
            
            # Delete shift_attendance
            cursor.execute(f"DELETE FROM shift_attendance WHERE user_id IN ({user_ids_str}) AND MONTH(date) = 11 AND YEAR(date) = 2025")
            print(f"  ✅ Deleted shift_attendance: {cursor.rowcount} rows")
            
            # Delete kpi
            cursor.execute(f"DELETE FROM kpi WHERE user_id IN ({user_ids_str}) AND MONTH(date) = 11 AND YEAR(date) = 2025")
            print(f"  ✅ Deleted KPIs: {cursor.rowcount} rows")
            
    except Exception as e:
        print(f"  ❌ Error cleaning data: {e}")

def create_emotion_logs(user_id: int, user_info: dict, date):
    """Create 0-3 bad emotion logs per day."""
    num_logs = random.choice([0, 1, 1, 1, 2, 3])  # More likely 1 log
    if num_logs == 0:
        return
    
    shift_start, shift_end = get_shift_times(user_info['shift'], date)
    bad_emotion = user_info['bad_emotion']
    
    try:
        with ConnectionHelper() as cursor:
            for _ in range(num_logs):
                # Random time within shift
                time_offset = random.randint(0, int((shift_end - shift_start).total_seconds()))
                log_time = shift_start + timedelta(seconds=time_offset)
                
                sql = """INSERT INTO emotion_log 
                        (user_id, emotion_type, confidence, captured_at)
                        VALUES (%s, %s, %s, %s)"""
                cursor.execute(sql, (user_id, bad_emotion, 0.95, log_time.replace(tzinfo=None)))
                print(f"  ✅ Emotion: {bad_emotion} @ {log_time.strftime('%H:%M')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def create_checklog(user_id: int, user_info: dict, date):
    """Create checklog for a user on a date."""
    shift_name = user_info['shift']
    shift_start, shift_end = get_shift_times(shift_name, date)
    
    # 80% on_time, 15% late, 5% early
    status_roll = random.random()
    if status_roll < 0.8:
        status = 'on_time'
        check_in = shift_start + timedelta(minutes=random.randint(-5, 5))
        check_out = shift_end + timedelta(minutes=random.randint(-5, 5))
    elif status_roll < 0.95:
        status = 'late'
        check_in = shift_start + timedelta(minutes=random.randint(5, 30))
        check_out = shift_end + timedelta(minutes=random.randint(-5, 5))
    else:
        status = 'early'
        check_in = shift_start + timedelta(minutes=random.randint(-5, 5))
        check_out = shift_end + timedelta(minutes=random.randint(-30, -5))
    
    # Calculate total_hours
    total_seconds = max(0, (check_out - check_in).total_seconds())
    total_hours = round(total_seconds / 3600.0, 2)
    
    try:
        with ConnectionHelper() as cursor:
            sql = """INSERT INTO checklog 
                    (user_id, date, shift, status, check_in, check_out, total_hours)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                user_id,
                date,
                shift_name,
                status,
                check_in.replace(tzinfo=None),
                check_out.replace(tzinfo=None),
                total_hours
            ))
            print(f"  ✅ Checklog: {status}, {total_hours}h")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def create_shift_attendance(user_id: int, user_info: dict, date):
    """Create shift_attendance record."""
    shift_name = user_info['shift']
    presence_pct = random.randint(30, 70)
    
    try:
        with ConnectionHelper() as cursor:
            shift_start, shift_end = get_shift_times(shift_name, date)
            
            sql = """INSERT INTO shift_attendance 
                    (user_id, date, shift, last_seen, serving_time, no_serving_count)
                    VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                user_id,
                date,
                shift_name,
                shift_end.replace(tzinfo=None),
                presence_pct > 50,
                0
            ))
            print(f"  ✅ Shift attendance: {presence_pct}%")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def create_kpi(user_id: int, date):
    """Create KPI record for a user on a date."""
    try:
        from service.kpi_calculator import calculate_kpi_for_user_date
        from service.kpi_service import add_kpi_service
        
        kpi_data = calculate_kpi_for_user_date(user_id, date)
        date_str = date.strftime('%Y-%m-%d')
        
        add_kpi_service(
            user_id=user_id,
            date=date_str,
            emotion_score=kpi_data['emotion_score'],
            attendance_score=kpi_data['attendance_score'],
            total_score=kpi_data['total_score'],
            remark=kpi_data['remark']
        )
        print(f"  ✅ KPI: {kpi_data['total_score']:.2f}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def generate_all_data():
    """Generate mock data for all users and dates."""
    print("\n" + "=" * 80)
    print("🚀 Mock Data Generation (FIXED)")
    print("=" * 80)
    
    # Clean old data first
    clean_old_data()
    
    current_date = START_DATE
    day_count = 0
    
    while current_date <= END_DATE:
        day_count += 1
        print(f"\n📅 [{day_count}/30] {current_date.strftime('%Y-%m-%d (%A)')}")
        
        for user_info in USERS:
            user_id = user_info['id']
            print(f"  👤 {user_info['name']} (shift={user_info['shift']})")
            
            create_emotion_logs(user_id, user_info, current_date)
            create_checklog(user_id, user_info, current_date)
            create_shift_attendance(user_id, user_info, current_date)
            create_kpi(user_id, current_date)
        
        current_date += timedelta(days=1)
    
    print("\n" + "=" * 80)
    print("✅ Mock Data Generation Complete!")
    print("=" * 80)

if __name__ == '__main__':
    try:
        generate_all_data()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
