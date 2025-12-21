# PHÂN TÍCH LOGIC HỆ THỐNG QUẢN LÝ CA LÀM VIỆC & KPI

## 📋 MỤC LỤC
1. [CA LÀM VIỆC (SHIFT MANAGEMENT)](#1-ca-làm-việc-shift-management)
2. [ĐIỂM DANH & THEO DÕI](#2-điểm-danh--theo-dõi)
3. [EMOTION LOG & TRỪ ĐIỂM](#3-emotion-log--trừ-điểm)
4. [KPI - TÍNH TOÁN TỔNG HỢP](#4-kpi---tính-toán-tổng-hợp)
5. [CHECK-IN/CHECK-OUT](#5-check-incheck-out)
6. [CÔNG THỨC TÍNH ĐIỂM](#6-công-thức-tính-điểm)

---

## 1. CA LÀM VIỆC (SHIFT MANAGEMENT)

### 🕒 Cấu Hình Ca Làm
**File:** `utils/shift_config.py`

```
Ca sáng (day):   08:00 - 14:00
Ca tối (night): 14:00 - 20:00
```

### ⚙️ Cơ Chế Tự Động

#### 1.1 Khởi Tạo Ca Làm (Scheduler)
**File:** `service/shift_attendance_service.py` → `scheduler_loop()`

**Thời điểm chạy:**
- Tại thời điểm bắt đầu ca: 08:00 (ca sáng), 14:00 (ca tối)
- Catch-up: Nếu backend khởi động muộn nhưng vẫn trong giờ làm việc

**Hành động tự động khi bắt đầu ca (`init_shift_rows`):**

```python
# Với MỖI nhân viên có shift=day/night và status=working:

1. Tạo shift_attendance row:
   - user_id, date, shift
   - absence_count = 0
   - last_seen = NULL
   - serving_time = False
   - no_serving_count = 0

2. Tạo checklog với status='pending':
   - check_in = NULL (chờ check-in thực)
   - check_out = NULL
   - status = 'pending'
   - note = 'Auto-created at shift start'

3. Tạo KPI với điểm tối đa:
   - emotion_score = 100.0
   - attendance_score = 100.0
   - total_score = 100.0
   - remark = 'Auto-initialized at shift start'
```

#### 1.2 Theo Dõi Vắng Mặt (Real-time)
**Chạy mỗi 10 giây** trong khi ca đang hoạt động:

```python
increment_absences_for_inactive():
    # Với mỗi nhân viên trong ca:
    if (now - last_seen) >= 30 seconds:
        absence_count += 1
```

#### 1.3 Kết Thúc Ca Làm
**Thời điểm:** 14:00 (kết thúc ca sáng), 20:00 (kết thúc ca tối)

**Hành động (`finalize_shift_absents`):**

```python
# Tìm những nhân viên không có checklog (không check-in):
for user in working_users_in_shift:
    if NOT exists checklog for today:
        1. Thêm checklog với status='absent'
        2. Cập nhật/Tạo KPI:
           - emotion_score = 0.0
           - attendance_score = 0.0
           - total_score = 0.0
           - remark = 'auto-absent'
```

#### 1.4 Thêm Nhân Viên Vào Ca (Trùng Giờ)
**Kịch bản:** Admin thêm nhân viên vào shift trong khi ca đang chạy

**Logic thực tế:**
- ✅ Nếu thêm khi TRONG giờ làm việc (ca đang chạy):
  - Scheduler catch-up sẽ phát hiện thiếu dữ liệu
  - Tự động gọi `init_shift_rows()` để khởi tạo bổ sung
  - Tạo checklog 'pending' + KPI 100/100/100

- ❌ Nếu thêm khi NGOÀI giờ làm việc:
  - Phải đợi ca sau bắt đầu (08:00 hoặc 14:00)
  - Scheduler sẽ khởi tạo vào lần chạy tiếp theo

**Lưu ý:** Hiện tại không có trigger đặc biệt khi admin thêm người mới. Tốt nhất là:
- Gọi thủ công `init_shift_rows(shift, date)` sau khi thêm user
- Hoặc chờ scheduler catch-up (trong vòng 10 giây)

---

## 2. ĐIỂM DANH & THEO DÕI

### 🎯 Nguyên Tắc Chính

**"Chỉ những người trong ca mới được điểm danh"**

### 2.1 Kiểm Tra Ca Làm Việc
**Áp dụng cho:** Check-in, Check-out, Emotion log

```python
# Trong checkin_service.py, checkout_service.py, add_emotion_service.py

current_shift = get_shift_by_time(current_time)  # 'day', 'night', 'none'
user_shift = user.shift  # Ca của nhân viên

# Từ chối nếu:
if current_shift == 'none':
    return "Không thể thực hiện ngoài giờ làm việc"
    
if current_shift != user_shift:
    return "Bạn không thuộc ca này"
```

### 2.2 Theo Dõi Nhân Viên (mark_seen)
**File:** `service/shift_attendance_service.py`

```python
def mark_seen(user_id, is_serving=False):
    """
    Cập nhật last_seen và serving_time
    
    Args:
        is_serving: True nếu đang phục vụ khách
    
    Logic:
        - Luôn cập nhật last_seen = now
        
        Nếu is_serving = True:
            → serving_time = True
            → no_serving_count = 0
            
        Nếu is_serving = False:
            → no_serving_count += 1
            → Nếu no_serving_count >= 2:
                → serving_time = False (ngừng phục vụ)
                → no_serving_count = 0 (reset)
    """
```

**Ý nghĩa:**
- `serving_time=True`: Nhân viên đang phục vụ khách → cảm xúc tiêu cực SẼ bị trừ điểm
- `serving_time=False`: Nhân viên không phục vụ → cảm xúc tiêu cực KHÔNG bị trừ điểm

### 2.3 Chặn Người Ngoài Ca
**Quan trọng:** Tất cả dữ liệu đều gắn với shift

```sql
-- Chỉ lưu nếu current_shift == user.shift

INSERT INTO checklog (user_id, date, shift, ...)
INSERT INTO emotion_log (user_id, captured_at, ...)
UPDATE shift_attendance SET last_seen = ...
```

**Kết quả:** Người được phát hiện nhưng không trong ca → Bỏ qua hoàn toàn

---

## 3. EMOTION LOG & TRỪ ĐIỂM

### 📊 Quy Tắc Trừ Điểm Cảm Xúc

#### 3.1 Điều Kiện Áp Dụng
**File:** `service/kpi_calculator.py` → `calculate_emotion_score()`

```python
# Chỉ trừ điểm khi:
1. Nhân viên ĐANG TRONG CA làm việc (đã được kiểm tra ở add_emotion_service)
2. Có khách (serving_time = True) ← **QUAN TRỌNG**
3. Emotion thuộc loại tiêu cực
```

**Lưu ý:** Logic hiện tại **CHƯA kiểm tra serving_time** trong khi tính KPI!

#### 3.2 Công Thức Trừ Điểm Emotion

**Các loại cảm xúc tiêu cực:**

| Cảm Xúc | Mức Độ | Trừ Điểm/Lần | Lý Do |
|---------|--------|--------------|-------|
| **Anger** (Tức giận) | Cao | -8 điểm | Thái độ rất xấu với khách |
| **Disgust** (Ghê tởm) | Cao | -7 điểm | Biểu hiện khinh khách |
| **Fear** (Sợ hãi) | Trung bình | -6 điểm | Thiếu tự tin, làm khách ngại |
| **Sad** (Buồn bã) | Trung bình | -5 điểm | Ảnh hưởng không khí dịch vụ |
| **Surprise** (Ngạc nhiên) | Thấp | -3 điểm | Ít ảnh hưởng nhưng không chuyên nghiệp |

**Code:**
```python
def calculate_emotion_score(user_id, date_local):
    score = 100.0  # Điểm tối đa
    
    emotion_logs = query_emotion_logs(user_id, date_local)
    
    PENALTIES = {
        'anger': 8.0,
        'disgust': 7.0,
        'sad': 5.0,
        'fear': 6.0,
        'surprise': 3.0,
    }
    
    for log in emotion_logs:
        emotion = log.emotion_type.lower()
        if emotion in PENALTIES:
            score -= PENALTIES[emotion]
    
    return max(0.0, min(100.0, score))  # Giới hạn 0-100
```

#### 3.3 Cơ Chế "Chỉ Trừ 1 Lần/Khách"

**Vấn đề:** Code hiện tại **CHƯA có cơ chế này**!

**Giải pháp đề xuất:**
```python
# Cần thêm logic:
def calculate_emotion_score_with_customer_tracking(user_id, date_local):
    """
    Ý tưởng: Gom các emotion log theo session phục vụ khách
    
    Thuật toán:
    1. Lấy tất cả emotion_log trong ngày
    2. Gom thành các session dựa trên serving_time changes:
       - serving_time: False → True: Bắt đầu session mới
       - serving_time: True → False: Kết thúc session
    3. Với MỖI session: CHỈ trừ điểm emotion XẤU NHẤT
    
    Ví dụ:
        Session 1 (10:00-10:05): Anger, Sad, Anger
        → Chỉ trừ 1 lần Anger (-8 điểm)
        
        Session 2 (10:30-10:35): Fear, Surprise
        → Chỉ trừ 1 lần Fear (-6 điểm)
        
        Tổng trừ: -14 điểm (thay vì -30 nếu trừ tất cả)
    """
```

**Yêu cầu bổ sung:**
1. Cần thêm `serving_session_id` vào `emotion_log` table
2. Hoặc dùng logic time-window để nhóm emotion logs
3. Trong `mark_seen()`: Track serving_time changes để đánh dấu sessions

---

## 4. KPI - TÍNH TOÁN TỔNG HỢP

### 📈 Cấu Trúc KPI

```sql
CREATE TABLE kpi (
    id INT PRIMARY KEY,
    user_id INT,
    date DATE,
    emotion_score FLOAT,      -- 0-100
    attendance_score FLOAT,   -- 0-100
    total_score FLOAT,        -- 0-100
    remark VARCHAR(500)
);
```

### 4.1 Thời Điểm Tính KPI

| Sự Kiện | Hành Động | File |
|---------|-----------|------|
| **Bắt đầu ca** | Tạo KPI 100/100/100 | `shift_attendance_service.py` |
| **Check-in** | Tạo KPI nếu chưa có | `checkin_service.py` |
| **Check-out** | Tính lại KPI đầy đủ | `checkout_service.py` |
| **Kết thúc ca** | Đánh absent: KPI 0/0/0 | `shift_attendance_service.py` |

### 4.2 Logic Tính KPI
**File:** `service/kpi_calculator.py`

```python
def calculate_kpi_for_user_date(user_id, date_local):
    # 1. Lấy checklog
    checklog = find_checklog(user_id, date_local)
    if not checklog:
        return {emotion: 0, attendance: 0, total: 0}
    
    # 2. Tính Emotion Score
    emotion_score = calculate_emotion_score(user_id, date_local)
    
    # 3. Tính Attendance Score
    attendance_score = calculate_attendance_score(checklog, shift)
    
    # 4. Tính Total Score
    total_score = (emotion_score + attendance_score) / 2
    
    return {
        emotion_score: round(..., 2),
        attendance_score: round(..., 2),
        total_score: round(..., 2),
        remark: ...
    }
```

---

## 5. CHECK-IN/CHECK-OUT

### ✅ Check-in Logic
**File:** `service/checkin_service.py`

#### 5.1 Điều Kiện Check-in
```python
# 1. Kiểm tra ca làm việc
if current_shift == 'none':
    → Từ chối (ngoài giờ)
    
if current_shift != user.shift:
    → Từ chối (không phải ca của bạn)

# 2. Kiểm tra đã check-in chưa
existing = find_checklog(user_id, today)

if existing AND existing.check_in IS NOT NULL:
    → Từ chối (đã check-in rồi)
```

#### 5.2 Trạng Thái Check-in
```python
cutoff = SHIFT_DAY_START if shift=='day' else SHIFT_NIGHT_START

if check_in_time <= cutoff:
    status = 'on_time'  # Đúng giờ
else:
    status = 'late'     # Trễ
```

**Ví dụ:**
- Ca sáng (08:00-14:00), cutoff = 08:00
  - Check-in 07:55 → `on_time`
  - Check-in 08:01 → `late`

#### 5.3 Hành Động Sau Check-in
```python
# 1. Cập nhật/Tạo checklog
UPDATE checklog SET check_in = now, status = 'on_time'/'late'

# 2. Đảm bảo KPI tồn tại
if NOT exists KPI:
    CREATE KPI(100/100/100)
```

**Quan trọng:** Check-in CHỈ ĐƯỢC 1 LẦN DUY NHẤT mỗi ngày!

### 🔄 Check-out Logic
**File:** `service/checkout_service.py`

#### 5.4 Điều Kiện Check-out
```python
# 1. Phải trong ca làm việc
if current_shift == 'none' OR current_shift != user.shift:
    → Từ chối

# 2. Phải đã check-in
if checklog.check_in IS NULL:
    → Từ chối "Chưa check-in, không thể check-out"

# 3. Cho phép check-out NHIỀU LẦN (overwrite)
# Mỗi lần check-out sẽ ghi đè thời gian và tính lại total_hours
```

#### 5.5 Tính Giờ Làm Việc
```python
def calculate_total_hours():
    # Thời gian gốc
    total_seconds = checkout_time - checkin_time
    
    # Trừ thời gian vắng
    absence_count = get_absence_count(user_id, date, shift)
    absent_seconds = absence_count * 10  # Mỗi lần vắng = 10s
    
    total_seconds = max(0, total_seconds - absent_seconds)
    total_hours = round(total_seconds / 3600, 2)
    
    # Tránh 0.0 nếu có thời gian làm
    if total_seconds > 0 and total_hours == 0.0:
        total_hours = 0.01
    
    return total_hours
```

#### 5.6 Trạng Thái Check-out
```python
cutoff = SHIFT_DAY_END if shift=='day' else SHIFT_NIGHT_END

if checkout_time < cutoff:
    status = 'early'  # Về sớm
elif checklog.status == 'late':
    status = 'late'   # Giữ nguyên "trễ" nếu check-in trễ
else:
    status = 'on_time'
```

**Ví dụ:**
- Ca sáng (08:00-14:00)
  - Check-in 08:05 (late) → Check-out 13:55 → Status: `early`
  - Check-in 07:55 (on_time) → Check-out 14:00 → Status: `on_time`

#### 5.7 Xử Lý Không Check-out

**Trường hợp:** Nhân viên check-in nhưng quên check-out

**Logic hiện tại:**
```python
# Tại thời điểm kết thúc ca (14:00/20:00):
finalize_shift_absents():
    # CHỈ xử lý người KHÔNG có checklog
    # → Nếu đã check-in, KHÔNG tự động checkout
```

**Vấn đề:** Nếu check-in nhưng không check-out:
- `total_hours` = NULL
- Không tính KPI attendance_score chính xác
- Admin phải thủ công edit checklog

**Giải pháp đề xuất:**
```python
# Thêm vào finalize_shift_absents():
for user in shift_users:
    checklog = find_checklog(user, date)
    
    if checklog AND checklog.check_out IS NULL:
        # Auto checkout 5 phút trước kết thúc ca
        auto_checkout_time = shift_end - timedelta(minutes=5)
        
        update_checkout(
            checklog.id,
            check_out=auto_checkout_time,
            status='early',
            note='Auto checkout - missing manual checkout'
        )
        
        # Tính lại KPI với giờ làm bị trừ
```

**Công thức tính điểm khi auto checkout:**
- Check-out sớm 5 phút: -5 điểm (early checkout penalty)
- Kết hợp với absence_count để tính total_hours chính xác

---

## 6. CÔNG THỨC TÍNH ĐIỂM

### 🎯 6.1 Emotion Score (0-100)

**Điểm khởi tạo:** 100 điểm

**Công thức:**
```
Emotion_Score = 100 - Σ(Penalty_i)

Trong đó:
- Penalty_i: Mức trừ điểm của emotion thứ i
- Σ: Tổng tất cả emotion logs trong ngày

Điều kiện trừ điểm:
1. Emotion thuộc loại tiêu cực (Anger, Fear, Sad, Disgust, Surprise)
2. Trong ca làm việc (đã được filter bởi add_emotion_service)
3. [ĐỀ XUẤT] Đang phục vụ khách (serving_time = True)

Giới hạn: max(0, min(100, score))
```

**Bảng phạt:**
```
Anger    → -8 điểm
Disgust  → -7 điểm
Fear     → -6 điểm
Sad      → -5 điểm
Surprise → -3 điểm
```

**Ví dụ:**
```
Nhân viên A trong ngày có:
- 2 lần Anger → -16 điểm
- 1 lần Sad → -5 điểm
- 3 lần Surprise → -9 điểm

Emotion_Score = 100 - 16 - 5 - 9 = 70 điểm
```

### 📊 6.2 Attendance Score (Checklog Score) (0-100)

**Điểm khởi tạo:** 100 điểm

**Công thức:**
```
Attendance_Score = 100 - Late_Penalty - Early_Penalty - Hours_Penalty - Absent_Penalty

Trong đó:

1. Late_Penalty:
   if status == 'late':
       Late_Penalty = 10 điểm
   else:
       Late_Penalty = 0

2. Early_Penalty:
   if status == 'early':
       Early_Penalty = 5 điểm
   else:
       Early_Penalty = 0

3. Hours_Penalty:
   expected_hours = 6h (cho cả ca day và night: 8:00-14:00, 14:00-20:00)
   
   if total_hours < expected_hours:
       missing_hours = expected_hours - total_hours
       Hours_Penalty = missing_hours × 5 điểm/giờ
   else:
       Hours_Penalty = 0

4. Absent_Penalty:
   if status == 'absent':
       Attendance_Score = 0  (bỏ qua các penalty khác)

Giới hạn: max(0, min(100, score))
```

**Code:**
```python
def calculate_attendance_score(checklog, shift):
    score = 100.0
    status = checklog.get('status', '')
    
    # Vắng = 0 điểm
    if status == 'absent':
        return 0.0
    
    # Trễ: -10 điểm
    if status == 'late':
        score -= 10.0
    
    # Về sớm: -5 điểm
    if status == 'early':
        score -= 5.0
    
    # Thiếu giờ: -5 điểm/giờ
    total_hours = checklog.get('total_hours')
    if total_hours is not None:
        expected_hours = get_shift_hours(shift)  # 6.0 giờ
        if total_hours < expected_hours:
            missing_hours = expected_hours - total_hours
            score -= missing_hours * 5.0
    
    return max(0.0, min(100.0, score))
```

**Ví dụ:**

**Trường hợp 1: Nhân viên đúng giờ**
```
Check-in: 08:00 (on_time)
Check-out: 14:00
Total_hours: 6.0h (sau khi trừ absences)

Late_Penalty = 0
Early_Penalty = 0
Hours_Penalty = 0

Attendance_Score = 100 - 0 - 0 - 0 = 100 điểm
```

**Trường hợp 2: Đi trễ, về đúng giờ**
```
Check-in: 08:15 (late)
Check-out: 14:00
Total_hours: 5.75h

Late_Penalty = 10
Early_Penalty = 0
Hours_Penalty = (6.0 - 5.75) × 5 = 1.25

Attendance_Score = 100 - 10 - 0 - 1.25 = 88.75 điểm
```

**Trường hợp 3: Đúng giờ nhưng về sớm**
```
Check-in: 08:00 (on_time)
Check-out: 13:30 (early)
Total_hours: 5.5h

Late_Penalty = 0
Early_Penalty = 5
Hours_Penalty = (6.0 - 5.5) × 5 = 2.5

Attendance_Score = 100 - 0 - 5 - 2.5 = 92.5 điểm
```

**Trường hợp 4: Đi trễ, về sớm, nhiều lần vắng**
```
Check-in: 08:20 (late)
Check-out: 13:45 (early)
Absence_count: 10 lần (= 100s = 0.028h bị trừ)
Total_hours: 5.37h

Late_Penalty = 10
Early_Penalty = 5
Hours_Penalty = (6.0 - 5.37) × 5 = 3.15

Attendance_Score = 100 - 10 - 5 - 3.15 = 81.85 điểm
```

**Trường hợp 5: Vắng**
```
Không check-in (hoặc status='absent')

Attendance_Score = 0 điểm
```

### 🏆 6.3 Total Score (KPI Tổng Hợp) (0-100)

**Công thức:**
```
Total_Score = (Emotion_Score + Attendance_Score) / 2

Giới hạn: max(0, min(100, score))
Round: 2 chữ số thập phân
```

**Giải thích:**
- Trọng số bằng nhau cho cảm xúc và điểm danh (50% - 50%)
- Nhân viên cần cân bằng cả thái độ phục vụ và kỷ luật giờ giấc

**Ví dụ tổng hợp:**

**Nhân viên A - Xuất sắc:**
```
Emotion_Score = 95 (1 lần Surprise)
Attendance_Score = 100 (đúng giờ, đủ giờ)

Total_Score = (95 + 100) / 2 = 97.5 điểm
Xếp loại: Xuất sắc
```

**Nhân viên B - Khá:**
```
Emotion_Score = 82 (2 lần Sad, 1 lần Fear)
Attendance_Score = 88.75 (trễ 15 phút)

Total_Score = (82 + 88.75) / 2 = 85.375 → 85.38 điểm
Xếp loại: Khá
```

**Nhân viên C - Cần cải thiện:**
```
Emotion_Score = 65 (nhiều cảm xúc tiêu cực)
Attendance_Score = 70 (trễ + về sớm)

Total_Score = (65 + 70) / 2 = 67.5 điểm
Xếp loại: Trung bình
```

**Nhân viên D - Vắng mặt:**
```
Emotion_Score = 0 (không làm = không có dữ liệu)
Attendance_Score = 0 (absent)

Total_Score = (0 + 0) / 2 = 0 điểm
Xếp loại: Vắng
```

---

## 7. CÁC VẤN ĐỀ CẦN KHẮC PHỤC

### ⚠️ 7.1 Emotion Trừ Điểm Khi Không Có Khách

**Vấn đề:**
```python
# Trong kpi_calculator.py - calculate_emotion_score()
# KHÔNG kiểm tra serving_time!

emotion_logs = query_emotion_logs(user_id, date_local)
for log in emotion_logs:
    score -= PENALTIES[log.emotion_type]  # ❌ Trừ luôn
```

**Giải pháp:**
```python
def calculate_emotion_score_with_serving_check(user_id, date_local):
    score = 100.0
    
    for log in emotion_logs:
        # Lấy serving_time tại thời điểm log.captured_at
        attendance = get_shift_attendance_at_time(
            user_id, 
            log.captured_at
        )
        
        # CHỈ trừ điểm khi đang phục vụ khách
        if attendance and attendance.serving_time == True:
            emotion = log.emotion_type.lower()
            if emotion in PENALTIES:
                score -= PENALTIES[emotion]
    
    return max(0.0, min(100.0, score))
```

**Yêu cầu:**
- Cần lưu `serving_time` snapshot cho mỗi emotion_log
- Hoặc query shift_attendance history (nếu có log updated_at)

### ⚠️ 7.2 Emotion Trừ Nhiều Lần Cho 1 Khách

**Vấn đề:** Không có cơ chế session tracking

**Giải pháp:**
```python
# Option 1: Thêm session_id vào emotion_log
ALTER TABLE emotion_log ADD COLUMN serving_session_id INT;

# Option 2: Nhóm theo time window
def group_emotions_by_session(emotion_logs, window_minutes=5):
    """
    Gom các emotion logs thành sessions dựa trên khoảng cách thời gian
    
    Logic:
    - Nếu 2 logs cách nhau > 5 phút → session mới
    - Với mỗi session: Chỉ lấy emotion XẤU NHẤT để trừ điểm
    """
    sessions = []
    current_session = []
    
    for i, log in enumerate(emotion_logs):
        if i == 0:
            current_session.append(log)
        else:
            time_gap = (log.captured_at - emotion_logs[i-1].captured_at).total_seconds()
            
            if time_gap > window_minutes * 60:
                # Bắt đầu session mới
                sessions.append(current_session)
                current_session = [log]
            else:
                current_session.append(log)
    
    if current_session:
        sessions.append(current_session)
    
    return sessions

def calculate_emotion_score_by_session(user_id, date_local):
    score = 100.0
    emotion_logs = query_emotion_logs(user_id, date_local)
    sessions = group_emotions_by_session(emotion_logs)
    
    for session in sessions:
        # Tìm emotion xấu nhất trong session
        worst_penalty = 0
        for log in session:
            emotion = log.emotion_type.lower()
            if emotion in PENALTIES:
                worst_penalty = max(worst_penalty, PENALTIES[emotion])
        
        # Chỉ trừ 1 lần
        score -= worst_penalty
    
    return max(0.0, min(100.0, score))
```

### ⚠️ 7.3 Không Auto Check-out Cho Người Quên

**Vấn đề:** Hiện tại chỉ xử lý người vắng hoàn toàn

**Giải pháp đã mô tả ở mục 5.7**

---

## 8. KIẾN TRÚC TỔNG THỂ

### 📐 Flow Diagram

```
BẮT ĐẦU CA (08:00 / 14:00)
│
├─> Scheduler: init_shift_rows()
│   │
│   ├─> Với mỗi user (shift=day/night, status=working):
│   │   ├─> Tạo shift_attendance (absence_count=0, serving_time=False)
│   │   ├─> Tạo checklog (status='pending', check_in=NULL)
│   │   └─> Tạo KPI (100/100/100)
│   │
│   └─> Log: "Đã khởi tạo ca ... cho N nhân viên"
│
│
TRONG CA (mỗi 10 giây)
│
├─> Scheduler: increment_absences_for_inactive()
│   │
│   └─> Với mỗi user trong shift_attendance:
│       if (now - last_seen) > 30s:
│           absence_count += 1
│
│
NHÂN VIÊN CHECK-IN
│
├─> API: POST /checkin/{id}
│   │
│   ├─> Kiểm tra ca làm việc (current_shift == user.shift)
│   ├─> Kiểm tra đã check-in chưa
│   ├─> Cập nhật checklog: check_in=now, status='on_time'/'late'
│   └─> Đảm bảo KPI tồn tại
│
│
PHÁT HIỆN NHÂN VIÊN (Real-time từ camera)
│
├─> Service: mark_seen(user_id, is_serving)
│   │
│   └─> Cập nhật shift_attendance:
│       - last_seen = now
│       - serving_time logic (based on is_serving)
│       - no_serving_count tracking
│
│
PHÁT HIỆN CẢM XÚC (Real-time từ emotion detection)
│
├─> API: POST /add-emotion
│   │
│   ├─> Kiểm tra ca làm việc (current_shift == user.shift)
│   └─> Lưu emotion_log (user_id, emotion_type, confidence, captured_at)
│
│
NHÂN VIÊN CHECK-OUT
│
├─> API: POST /checkout/{id}
│   │
│   ├─> Kiểm tra đã check-in chưa
│   ├─> Tính total_hours (checkout - checkin - absences)
│   ├─> Cập nhật checklog: check_out=now, total_hours, status
│   │
│   └─> Tính lại KPI:
│       ├─> calculate_emotion_score(user_id, date)
│       ├─> calculate_attendance_score(checklog, shift)
│       ├─> total_score = (emotion + attendance) / 2
│       └─> update_kpi(...)
│
│
KẾT THÚC CA (14:00 / 20:00)
│
└─> Scheduler: finalize_shift_absents()
    │
    └─> Với mỗi user trong shift:
        if NOT exists checklog:
            ├─> Tạo checklog (status='absent')
            └─> Cập nhật KPI (0/0/0)
```

### 🗂️ Database Schema

```sql
-- Nhân viên
nhanvien (
    id, username, full_name, shift, status, ...
)

-- Điểm danh
checklog (
    id, user_id, date, 
    check_in, check_out, 
    total_hours, status, shift,
    edited_by, note
)

-- Theo dõi real-time
shift_attendance (
    id, user_id, date, shift,
    absence_count,          -- Số lần vắng trong ca
    last_seen,              -- Lần cuối thấy
    serving_time BOOLEAN,   -- Đang phục vụ khách
    no_serving_count INT,   -- Đếm liên tiếp không phục vụ
    updated_at
)

-- Cảm xúc
emotion_log (
    id, user_id, camera_id,
    emotion_type, confidence,
    captured_at, image, note
)

-- KPI
kpi (
    id, user_id, date,
    emotion_score,      -- 0-100
    attendance_score,   -- 0-100
    total_score,        -- 0-100
    remark
)
```

---

## 9. KẾT LUẬN & ĐÁNH GIÁ

### ✅ Điểm Mạnh

1. **Tự động hóa cao:**
   - Scheduler khởi tạo ca làm tự động
   - Theo dõi vắng mặt real-time
   - Finalize absent users tự động

2. **Bảo mật ca làm:**
   - Chặn check-in/check-out ngoài ca
   - Chặn emotion log cho người không trong ca
   - Đảm bảo dữ liệu đúng shift

3. **KPI tổng hợp:**
   - Cân bằng cảm xúc + điểm danh (50-50)
   - Tự động tính toán sau checkout
   - Lưu lịch sử đầy đủ

### ⚠️ Hạn Chế & Cần Cải Thiện

1. **Emotion scoring:**
   - ❌ Chưa kiểm tra `serving_time` (trừ điểm cả khi không có khách)
   - ❌ Chưa có cơ chế "1 lần/khách" (trừ nhiều lần cho cùng 1 session)
   - ✅ Cần: Session tracking + serving_time check

2. **Check-out logic:**
   - ❌ Không auto checkout cho người quên
   - ❌ Không xử lý trường hợp check-in nhưng không check-out
   - ✅ Cần: Auto checkout 5 phút trước kết thúc ca

3. **Thêm user vào ca:**
   - ⚠️ Phụ thuộc scheduler catch-up (delay 10s)
   - ✅ Nên: Trigger thủ công `init_shift_rows()` ngay sau khi thêm user

4. **Absence tracking:**
   - ✅ Đang hoạt động tốt
   - ⚠️ Mỗi lần vắng = 10s (có thể cần điều chỉnh)

### 📝 Khuyến Nghị

**Ưu tiên cao:**
1. Thêm logic kiểm tra `serving_time` vào `calculate_emotion_score()`
2. Implement session tracking cho emotion logs
3. Thêm auto checkout cho người quên

**Ưu tiên trung bình:**
4. Tối ưu scheduler: giảm interval xuống 5s cho responsive hơn
5. Thêm webhook/notification khi finalize absent
6. Dashboard theo dõi KPI real-time

**Ưu tiên thấp:**
7. Export báo cáo KPI tháng/quý
8. Machine learning để dự đoán performance
9. Integration với hệ thống lương/thưởng

---

**Ngày cập nhật:** 2025-12-21  
**Phiên bản:** 1.0  
**Tác giả:** GitHub Copilot Analysis
