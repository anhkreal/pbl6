# BÁO CÁO LOGIC HỆ THỐNG SAU KHI CẬP NHẬT

**Ngày cập nhật:** 2025-12-21  
**Phiên bản:** 2.0 (Đã sửa các vấn đề theo yêu cầu)

---

## 📋 TÓM TẮT CÁC THAY ĐỔI

### ✅ **ĐÃ KHẮC PHỤC HOÀN TẤT:**

| Vấn Đề | Trạng Thái | File Đã Sửa |
|--------|------------|-------------|
| **1. Emotion trừ điểm không kiểm tra serving_time** | ✅ Đã sửa | `service/kpi_calculator.py` |
| **2. Emotion trừ nhiều lần cho 1 session** | ✅ Đã sửa | `service/kpi_calculator.py` |
| **3. Không xử lý quên check-out** | ✅ Đã sửa | `service/shift_attendance_service.py` |
| **4. Công thức attendance score sai** | ✅ Đã sửa | `service/kpi_calculator.py` |
| **5. Tỷ lệ KPI không đúng (50-50)** | ✅ Đã sửa | `service/kpi_calculator.py` |

---

## 🎯 1. EMOTION SCORE - LOGIC MỚI

### **File:** `service/kpi_calculator.py`

### 1.1 Kiểm Tra serving_time ✅

**Trước khi sửa:**
```python
# ❌ Trừ điểm TẤT CẢ emotion logs
for log in emotion_logs:
    emotion = log.emotion_type.lower()
    if emotion in PENALTIES:
        score -= PENALTIES[emotion]
```

**Sau khi sửa:**
```python
# ✅ CHỈ trừ điểm khi serving_time=True
filtered_logs = []
for log in emotion_logs:
    # Query shift_attendance tại thời điểm log
    attendance = nguoi_repo.get_shift_attendance(
        user_id=user_id,
        date_only=log_time.date(),
        shift=shift
    )
    
    # CHỈ giữ lại nếu đang phục vụ khách
    if attendance and attendance.get('serving_time') == True:
        filtered_logs.append(log)

if not filtered_logs:
    return 100.0  # Không có emotion khi phục vụ = điểm tối đa
```

**Kết quả:** Nhân viên không bị trừ điểm khi biểu hiện cảm xúc ngoài thời gian phục vụ khách!

---

### 1.2 Session Tracking - Chỉ Trừ 1 Lần/Khách ✅

**Hàm mới:** `group_emotions_by_session(emotion_logs, window_minutes=5)`

**Logic:**
```python
def group_emotions_by_session(emotion_logs, window_minutes=5):
    """
    Nhóm emotion logs thành các session dựa trên khoảng cách thời gian
    
    Quy tắc: Nếu 2 logs cách nhau > 5 phút → session mới
    """
    sessions = []
    current_session = [sorted_logs[0]]
    
    for i in range(1, len(sorted_logs)):
        time_gap = (curr_time - prev_time).total_seconds()
        
        if time_gap > 5 * 60:  # > 5 phút
            # Kết thúc session cũ, bắt đầu session mới
            sessions.append(current_session)
            current_session = [curr_log]
        else:
            # Cùng session
            current_session.append(curr_log)
    
    return sessions
```

**Xử lý mỗi session:**
```python
# Với MỖI session: CHỈ trừ emotion XẤU NHẤT
for session in sessions:
    worst_penalty = 0.0
    for log in session:
        emotion = log.emotion_type.lower()
        penalty = PENALTIES.get(emotion, 0.0)
        worst_penalty = max(worst_penalty, penalty)  # Lấy penalty lớn nhất
    
    # Trừ điểm 1 lần duy nhất
    score -= worst_penalty
```

**Ví dụ thực tế:**

```
Nhân viên A phục vụ khách từ 10:00-10:05:
  10:01 → Anger   (penalty -8)
  10:02 → Sad     (penalty -5)
  10:03 → Anger   (penalty -8)

→ Cùng 1 session (cách nhau < 5 phút)
→ CHỈ trừ emotion xấu nhất: Anger (-8 điểm)
→ Thay vì trừ -21 điểm, chỉ trừ -8 điểm ✅

Sau đó phục vụ khách khác từ 10:30-10:35:
  10:31 → Fear    (penalty -6)
  10:33 → Surprise (penalty -3)

→ Session mới (cách session trước > 5 phút)
→ CHỈ trừ emotion xấu nhất: Fear (-6 điểm)

Tổng trừ điểm: -8 + -6 = -14 điểm
Emotion Score = 100 - 14 = 86 điểm
```

**Bảng phạt không đổi:**
```
Anger (Tức giận):    -8 điểm
Disgust (Ghê tởm):   -7 điểm
Fear (Sợ hãi):       -6 điểm
Sad (Buồn):          -5 điểm
Surprise (Ngạc nhiên): -3 điểm
```

---

## 📊 2. ATTENDANCE SCORE - CÔNG THỨC MỚI

### **File:** `service/kpi_calculator.py` → `calculate_attendance_score()`

### 2.1 Thay Đổi Penalty

| Trạng thái | Trước | Sau | Thay đổi |
|------------|-------|-----|----------|
| Late (đi trễ) | -10 | -10 | Không đổi |
| Early (về sớm) | **-5** | **-10** | ✅ Tăng phạt |

### 2.2 Công Thức Thiếu Giờ + Vắng (MỚI) ✅

**Trước khi sửa:**
```python
# ❌ Công thức cũ: trừ 5 điểm/giờ thiếu
if total_hours < expected_hours:
    missing_hours = expected_hours - total_hours
    score -= missing_hours * 5.0
```

**Sau khi sửa:**
```python
# ✅ Công thức mới: min(80 * (expected - missing - absence + 1) / expected, 80)

# 1. Lấy absence_count và convert sang giờ
absence_count = nguoi_repo.get_absence_count_for_shift(user_id, date_local, shift)
absence_hours = (absence_count * 10) / 3600.0  # Mỗi lần vắng = 10s

# 2. Tính giờ thiếu
missing_hours = max(0, expected_hours - total_hours)

# 3. Áp dụng công thức mới
if expected_hours > 0:
    hours_score = 80.0 * (expected_hours - missing_hours - absence_hours + 1.0) / expected_hours
    hours_score = min(hours_score, 80.0)  # Tối đa 80 điểm
    hours_score = max(hours_score, 0.0)   # Tối thiểu 0 điểm

# 4. Kết hợp với penalty late/early
final_score = hours_score
if status == 'late':
    final_score -= 10.0
if status == 'early':
    final_score -= 10.0
```

### 2.3 Ví Dụ Chi Tiết

#### **Ví dụ 1: Hoàn hảo**
```
Check-in: 08:00 (on_time)
Check-out: 14:00 (đúng giờ)
Total_hours: 6.0h
Absence_count: 0
Expected_hours: 6.0h

Missing_hours = 0
Absence_hours = 0

Hours_score = 80 * (6 - 0 - 0 + 1) / 6 = 80 * 7/6 = 93.33 → cap at 80

Late penalty: 0
Early penalty: 0

Final_score = 80 điểm ✅
```

#### **Ví dụ 2: Đi trễ, đủ giờ**
```
Check-in: 08:15 (late)
Check-out: 14:00
Total_hours: 5.75h
Absence_count: 0
Expected_hours: 6.0h

Missing_hours = 6 - 5.75 = 0.25h
Absence_hours = 0

Hours_score = 80 * (6 - 0.25 - 0 + 1) / 6 = 80 * 6.75/6 = 90 → cap at 80

Late penalty: -10
Early penalty: 0

Final_score = 80 - 10 = 70 điểm
```

#### **Ví dụ 3: Về sớm + nhiều vắng**
```
Check-in: 08:00 (on_time)
Check-out: 13:30 (early)
Total_hours: 5.5h
Absence_count: 360 lần (= 3600s = 1h vắng)
Expected_hours: 6.0h

Missing_hours = 6 - 5.5 = 0.5h
Absence_hours = 360 * 10 / 3600 = 1.0h

Hours_score = 80 * (6 - 0.5 - 1.0 + 1) / 6 
           = 80 * 5.5/6 
           = 73.33 điểm

Late penalty: 0
Early penalty: -10

Final_score = 73.33 - 10 = 63.33 điểm
```

#### **Ví dụ 4: Vắng quá nhiều**
```
Check-in: 08:00
Check-out: 14:00
Total_hours: 6.0h
Absence_count: 720 lần (= 7200s = 2h vắng) ⚠️ VỆT MỨC CHO PHÉP

Missing_hours = 0
Absence_hours = 2.0h

Hours_score = 80 * (6 - 0 - 2 + 1) / 6
           = 80 * 5/6
           = 66.67 điểm

⚠️ Vượt quá 1 giờ vắng → điểm giảm mạnh
```

**Lưu ý:** Công thức cho phép tối đa **1 giờ vắng** mà vẫn giữ được điểm tốt (80). Vượt quá sẽ bị phạt nặng.

---

## 🏆 3. TOTAL SCORE - TỶ LỆ MỚI

### **File:** `service/kpi_calculator.py` → `calculate_kpi_for_user_date()`

**Trước khi sửa:**
```python
# ❌ 50% Emotion + 50% Attendance
total_score = (emotion_score + attendance_score) / 2.0
```

**Sau khi sửa:**
```python
# ✅ 30% Emotion + 70% Attendance (ưu tiên điểm danh)
total_score = (attendance_score * 0.7) + (emotion_score * 0.3)
```

### **Tại sao thay đổi?**

- **Attendance (70%):** Kỷ luật giờ giấc quan trọng hơn
- **Emotion (30%):** Thái độ vẫn quan trọng nhưng không quyết định chính

### **So sánh:**

| Emotion | Attendance | **Cũ (50-50)** | **Mới (30-70)** | Chênh lệch |
|---------|------------|----------------|----------------|------------|
| 100 | 100 | 100.0 | 100.0 | 0 |
| 80 | 100 | 90.0 | **94.0** | +4.0 |
| 100 | 80 | 90.0 | **86.0** | -4.0 |
| 70 | 90 | 80.0 | **84.0** | +4.0 |
| 90 | 70 | 80.0 | **76.0** | -4.0 |
| 60 | 60 | 60.0 | **60.0** | 0 |

**Kết luận:** Nhân viên có điểm danh tốt sẽ được ưu ái hơn!

---

## 🔄 4. AUTO CHECKOUT - XỬ LÝ QUÊN CHECK-OUT

### **File:** `service/shift_attendance_service.py` → `finalize_shift_absents()`

### 4.1 Kịch Bản Xử Lý

**Trước khi sửa:**
```python
# ❌ Chỉ xử lý người KHÔNG có checklog (vắng hoàn toàn)
if not existing:
    nguoi_repo.add_absence(user_id, shift, note='auto-absent')
    # KPI = 0/0/0
```

**Sau khi sửa:**
```python
# ✅ Xử lý 2 trường hợp:

# Case 1: Không có checklog → Vắng (giữ nguyên)
if not existing:
    nguoi_repo.add_absence(user_id, shift, note='auto-absent')
    # KPI = 0/0/0

# Case 2: Có check-in nhưng KHÔNG check-out → Auto checkout (MỚI)
elif existing.get('check_in') and not existing.get('check_out'):
    # Tự động checkout 5 phút trước kết thúc ca
    auto_checkout_time = shift_end - timedelta(minutes=5)
    
    # Tính total_hours (bao gồm trừ absences)
    total_seconds = (auto_checkout_time - check_in_time).total_seconds()
    absence_count = nguoi_repo.get_absence_count_for_shift(user_id, date, shift)
    total_seconds -= (absence_count * 10)
    total_hours = round(total_seconds / 3600, 2)
    
    # Update checkout
    nguoi_repo.update_checkin_checkout(
        row_id=existing['id'],
        check_out=auto_checkout_time,
        total_hours=total_hours,
        status='early',  # Về sớm 5 phút
        note='Auto checkout - forgotten manual checkout'
    )
    
    # Recalculate KPI
    kpi_data = calculate_kpi_for_user_date(user_id, date_local)
    update_kpi_service(...)
```

### 4.2 Thời Điểm Auto Checkout

| Ca làm | Kết thúc | Auto checkout time |
|--------|----------|-------------------|
| Day | 14:00 | **13:55** (5 phút trước) |
| Night | 20:00 | **19:55** (5 phút trước) |

### 4.3 Ví Dụ Thực Tế

```
Nhân viên B:
- Check-in: 08:00 ✅
- Quên check-out ❌

Khi kết thúc ca (14:00):
→ Hệ thống phát hiện: check_in ≠ NULL, check_out = NULL
→ Tự động checkout lúc 13:55
→ Status = 'early' (về sớm 5 phút)
→ Total_hours = (13:55 - 08:00) - absences
→ Tính lại KPI tự động

KPI tính toán:
- Emotion_score: tính bình thường
- Attendance_score: 
  + Hours_score: dựa trên 5h 55p làm việc
  + Early penalty: -10 điểm
- Total_score = attendance * 0.7 + emotion * 0.3

Remark: "... (auto checkout)"
```

### 4.4 Impact Lên Điểm

```
Giả sử nhân viên làm việc hoàn hảo nhưng quên checkout:

Total_hours = 5.92h (13:55 - 08:00)
Expected = 6.0h
Missing = 0.08h
Absence = 0

Hours_score = 80 * (6 - 0.08 - 0 + 1) / 6 = 80 * 6.92/6 = 92.27 → cap at 80
Early penalty = -10

Attendance_score = 80 - 10 = 70 điểm

So với checkout đúng giờ:
- Đúng giờ: 80 điểm
- Auto checkout: 70 điểm
→ Mất 10 điểm (do early penalty)
```

**Kết luận:** Nhân viên vẫn được tính điểm, không bị 0 điểm như trước!

---

## 📐 5. TÓM TẮT CÔNG THỨC MỚI

### 🎯 **EMOTION SCORE**

```
Emotion_Score = 100 - Σ(worst_penalty_per_session)

Điều kiện:
1. CHỈ tính emotion khi serving_time = True
2. Nhóm thành sessions (window 5 phút)
3. Mỗi session: CHỈ trừ emotion xấu nhất

Penalties:
- Anger:    -8 điểm
- Disgust:  -7 điểm
- Fear:     -6 điểm
- Sad:      -5 điểm
- Surprise: -3 điểm

Giới hạn: 0 ≤ score ≤ 100
```

### 📊 **ATTENDANCE SCORE**

```
if status == 'absent':
    Attendance_Score = 0
else:
    # 1. Tính hours_score
    absence_hours = (absence_count * 10) / 3600
    missing_hours = max(0, expected - total_hours)
    
    hours_score = min(80 * (expected - missing - absence + 1) / expected, 80)
    hours_score = max(hours_score, 0)
    
    # 2. Áp dụng penalties
    final_score = hours_score
    if status == 'late':
        final_score -= 10
    if status == 'early':
        final_score -= 10
    
    Attendance_Score = max(0, min(100, final_score))

Giới hạn: 0 ≤ score ≤ 100
Tối đa hours_score: 80 điểm (cho phép 1h vắng)
```

### 🏆 **TOTAL SCORE (KPI)**

```
Total_Score = (Attendance_Score × 0.7) + (Emotion_Score × 0.3)

Giới hạn: 0 ≤ score ≤ 100
Round: 2 chữ số thập phân
```

---

## 🎬 6. WORKFLOW HOÀN CHỈNH

```
08:00 - BẮT ĐẦU CA SÁNG
│
├─> Scheduler: init_shift_rows('day', date)
│   ├─> Tạo shift_attendance (serving_time=False)
│   ├─> Tạo checklog (status='pending', check_in=NULL)
│   └─> Tạo KPI (100/100/100)
│
│
TRONG CA (08:00 - 14:00)
│
├─> Nhân viên check-in
│   ├─> Kiểm tra ca làm việc ✅
│   ├─> Cập nhật checklog: check_in=now, status='on_time'/'late'
│   └─> Đảm bảo KPI tồn tại
│
├─> Camera phát hiện nhân viên
│   └─> mark_seen(user_id, is_serving)
│       ├─> Cập nhật last_seen
│       └─> Cập nhật serving_time (based on is_serving)
│
├─> Camera phát hiện emotion
│   ├─> Kiểm tra ca làm việc ✅
│   └─> Lưu emotion_log (user_id, emotion_type, captured_at)
│       → Sẽ được filter bởi serving_time khi tính KPI
│
├─> Mỗi 10s: increment_absences_for_inactive()
│   └─> Nếu (now - last_seen) > 30s: absence_count += 1
│
├─> Nhân viên check-out
│   ├─> Tính total_hours (checkout - checkin - absences)
│   ├─> Cập nhật checklog: check_out, total_hours, status
│   └─> Tính lại KPI:
│       ├─> calculate_emotion_score() ← CHỈ tính khi serving_time=True ✅
│       │   └─> Session tracking: 1 lần/session ✅
│       ├─> calculate_attendance_score() ← Công thức mới ✅
│       │   ├─> Late: -10
│       │   ├─> Early: -10
│       │   └─> Hours: min(80*(expected-missing-absence+1)/expected, 80)
│       └─> total = attendance*0.7 + emotion*0.3 ✅
│
│
14:00 - KẾT THÚC CA SÁNG
│
└─> Scheduler: finalize_shift_absents('day', date)
    │
    ├─> Case 1: Không có checklog
    │   ├─> Tạo checklog (status='absent')
    │   └─> KPI = 0/0/0
    │
    └─> Case 2: Có check-in, KHÔNG check-out ✅ MỚI
        ├─> Auto checkout lúc 13:55 (5 phút trước)
        ├─> Tính total_hours (bao gồm trừ absences)
        ├─> Status = 'early'
        └─> Tính lại KPI với công thức mới
```

---

## ✅ 7. CHECKLIST XÁC NHẬN

| Yêu cầu | Trạng thái | Chi tiết |
|---------|------------|----------|
| ✅ Kiểm tra serving_time | **Hoàn thành** | Chỉ trừ điểm emotion khi đang phục vụ khách |
| ✅ Session tracking (1 lần/khách) | **Hoàn thành** | Nhóm theo window 5 phút, chỉ trừ emotion xấu nhất/session |
| ✅ Auto checkout khi quên | **Hoàn thành** | Tự động checkout 5 phút trước kết thúc ca |
| ✅ Penalty late = 10 điểm | **Hoàn thành** | Đã kiểm tra |
| ✅ Penalty early = 10 điểm | **Hoàn thành** | Đã tăng từ -5 lên -10 |
| ✅ Công thức thiếu giờ + vắng mới | **Hoàn thành** | `min(80*(expected-missing-absence+1)/expected, 80)` |
| ✅ Tỷ lệ KPI: 70% attendance + 30% emotion | **Hoàn thành** | Đã thay đổi từ 50-50 |

---

## 📊 8. VÍ DỤ TỔNG HỢP

### **Nhân viên A - Xuất sắc (hoàn hảo)**

```
ATTENDANCE:
- Check-in: 08:00 (on_time)
- Check-out: 14:00 (đúng giờ)
- Total_hours: 6.0h
- Absence_count: 0

Hours_score = 80 * (6-0-0+1)/6 = 93.33 → cap at 80
Late penalty: 0
Early penalty: 0
→ Attendance_score = 80 điểm

EMOTION:
- Phục vụ 3 khách trong ngày
- Session 1: Happy → không trừ
- Session 2: Happy → không trừ  
- Session 3: 1 lần Surprise
  → Trừ -3 điểm
→ Emotion_score = 100 - 3 = 97 điểm

TOTAL:
Total_score = 80*0.7 + 97*0.3 = 56 + 29.1 = 85.1 điểm
Xếp loại: Khá
```

### **Nhân viên B - Tốt (trễ nhẹ, emotion tốt)**

```
ATTENDANCE:
- Check-in: 08:10 (late)
- Check-out: 14:00
- Total_hours: 5.83h
- Absence_count: 0

Missing = 6 - 5.83 = 0.17h
Hours_score = 80 * (6-0.17-0+1)/6 = 80 * 6.83/6 = 91.07 → cap at 80
Late penalty: -10
→ Attendance_score = 80 - 10 = 70 điểm

EMOTION:
- Phục vụ 2 khách
- Session 1: 1 Sad
- Session 2: Happy
→ Emotion_score = 100 - 5 = 95 điểm

TOTAL:
Total_score = 70*0.7 + 95*0.3 = 49 + 28.5 = 77.5 điểm
Xếp loại: Khá
```

### **Nhân viên C - Trung bình (về sớm, emotion tệ)**

```
ATTENDANCE:
- Check-in: 08:00 (on_time)
- Check-out: 13:30 (early)
- Total_hours: 5.5h
- Absence_count: 180 (= 30 phút vắng)

Missing = 6 - 5.5 = 0.5h
Absence = 180*10/3600 = 0.5h
Hours_score = 80 * (6-0.5-0.5+1)/6 = 80 * 6/6 = 80
Early penalty: -10
→ Attendance_score = 80 - 10 = 70 điểm

EMOTION:
- Phục vụ 4 khách
- Session 1: Anger, Sad → worst = Anger (-8)
- Session 2: Fear, Surprise → worst = Fear (-6)
- Session 3: Disgust → (-7)
- Session 4: Sad → (-5)
→ Emotion_score = 100 - 8 - 6 - 7 - 5 = 74 điểm

TOTAL:
Total_score = 70*0.7 + 74*0.3 = 49 + 22.2 = 71.2 điểm
Xếp loại: Trung bình
```

### **Nhân viên D - Kém (quên checkout)**

```
ATTENDANCE:
- Check-in: 08:15 (late)
- Quên check-out ❌
→ Auto checkout lúc 13:55

Total_hours = (13:55 - 08:15) = 5.67h
Absence_count: 60 (10 phút)

Missing = 6 - 5.67 = 0.33h
Absence = 60*10/3600 = 0.17h
Hours_score = 80 * (6-0.33-0.17+1)/6 = 80 * 6.5/6 = 86.67 → cap at 80
Late penalty: -10
Early penalty: -10 (auto checkout = early)
→ Attendance_score = 80 - 10 - 10 = 60 điểm

EMOTION:
- Emotion_score = 85 điểm (giả sử)

TOTAL:
Total_score = 60*0.7 + 85*0.3 = 42 + 25.5 = 67.5 điểm
Xếp loại: Trung bình (do quên checkout + trễ)
```

### **Nhân viên E - Vắng**

```
ATTENDANCE:
- Không check-in
→ status = 'absent'
→ Attendance_score = 0 điểm

EMOTION:
- Không làm việc
→ Emotion_score = 0 điểm

TOTAL:
Total_score = 0*0.7 + 0*0.3 = 0 điểm
Xếp loại: Vắng
```

---

## 🎓 9. HƯỚNG DẪN SỬ DỤNG

### Cho Developer:

1. **Test emotion scoring:**
   ```python
   # Test với serving_time=False → không trừ điểm
   # Test với serving_time=True → trừ điểm
   # Test session tracking: emotions cách nhau < 5 phút
   ```

2. **Test attendance scoring:**
   ```python
   # Test late: -10
   # Test early: -10
   # Test công thức: min(80*(6-missing-absence+1)/6, 80)
   ```

3. **Test auto checkout:**
   ```python
   # Tạo checklog với check_in, không checkout
   # Chờ đến kết thúc ca
   # Verify: auto checkout lúc shift_end - 5 phút
   ```

### Cho Admin:

1. **Giám sát KPI:**
   - Kiểm tra `remark` field: "(auto checkout)" = quên checkout
   - So sánh emotion_score: cao = phục vụ tốt
   - So sánh attendance_score: cao = kỷ luật tốt

2. **Điều chỉnh tham số:**
   - Session window: 5 phút (có thể tăng/giảm)
   - Auto checkout: 5 phút trước (có thể điều chỉnh)
   - Penalty values: có thể tùy chỉnh

---

## 📝 10. KẾT LUẬN

### ✅ **ĐÃ ĐẠT YÊU CẦU:**

1. ✅ **Emotion chỉ trừ điểm khi đang phục vụ khách** (serving_time=True)
2. ✅ **Session tracking: 1 lần/khách** (window 5 phút, trừ emotion xấu nhất)
3. ✅ **Auto checkout khi quên** (5 phút trước kết thúc ca)
4. ✅ **Penalty mới: Late -10, Early -10**
5. ✅ **Công thức thiếu giờ + vắng mới** với tối đa 80 điểm
6. ✅ **Tỷ lệ KPI: 70% attendance + 30% emotion**

### 🎯 **ĐIỂM MẠNH:**

- **Công bằng hơn:** Không trừ điểm emotion khi không phục vụ
- **Khoa học hơn:** Session tracking phản ánh đúng thực tế
- **Tự động hơn:** Auto checkout tránh mất điểm oan
- **Ưu tiên đúng:** 70% attendance khuyến khích kỷ luật

### 📈 **HIỆU QUẢ DỰ KIẾN:**

- Nhân viên không bị trừ điểm oan (emotion ngoài giờ phục vụ)
- Khuyến khích giữ thái độ tốt liên tục với khách (1 lần xấu = 1 session xấu)
- Giảm tranh cãi về quên checkout (tự động xử lý)
- Tăng trọng số kỷ luật giờ giấc (70% vs 30%)

---

**🏆 Hệ thống đã sẵn sàng hoạt động với logic mới!**

---

**File được sửa:**
1. `service/kpi_calculator.py` - Logic tính emotion và attendance
2. `service/shift_attendance_service.py` - Auto checkout logic

**Backup khuyến nghị:** Tạo branch mới hoặc backup database trước khi deploy!