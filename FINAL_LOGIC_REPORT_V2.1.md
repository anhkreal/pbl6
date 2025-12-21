# BÁO CÁO LOGIC HỆ THỐNG - PHIÊN BẢN CẬP NHẬT MỚI NHẤT

**Ngày cập nhật:** 2025-12-21 (v2.1)  
**Các thay đổi mới:** Session tracking đơn giản hóa + Grace period 30 phút

---

## 🎯 TÓM TẮT CÁC THAY ĐỔI MỚI (v2.1)

### ✅ **THAY ĐỔI SO VỚI v2.0:**

| Thay đổi | Trước (v2.0) | Sau (v2.1) | Lý do |
|----------|--------------|------------|-------|
| **Emotion trừ điểm** | Emotion XẤU NHẤT/session | **Emotion TIÊU CỰC ĐẦU TIÊN/session** | Đơn giản hóa logic |
| **Session tracking** | Window 5 phút | **no_serving_count >= 2** (logic mark_seen) | Sử dụng cơ chế có sẵn |
| **Finalize shift** | Ngay khi kết thúc ca (14:00, 20:00) | **Sau 30 phút** (14:30, 20:30) | Grace period cho checkout |
| **Grace period tracking** | Không có | **14:00-14:30, 20:00-20:30**: KHÔNG track absence | Tránh phạt oan |
| **Auto checkout time** | 5 phút trước (13:55, 19:55) | **Đúng giờ kết thúc** (14:00, 20:00) | Không penalty early |

---

## 📊 1. EMOTION SCORING - LOGIC ĐƠN GIẢN HÓA

### **File:** `service/kpi_calculator.py`

### 1.1 Session Tracking Dựa Trên mark_seen()

**Logic mark_seen() có sẵn:**
```python
def mark_seen(user_id, is_serving):
    if is_serving:
        # Phát hiện khách
        serving_time = True
        no_serving_count = 0
    else:
        # Không phát hiện khách
        no_serving_count += 1
        
        if no_serving_count >= 2:
            # 2 lần liên tiếp không thấy khách → hết session
            serving_time = False
            no_serving_count = 0
```

**Ví dụ:**
```
10:00 → Phát hiện khách → serving_time=True (BẮT ĐẦU SESSION)
10:01 → Emotion: Anger
10:02 → Emotion: Sad
10:03 → Không thấy khách → no_serving_count=1
10:04 → Không thấy khách → no_serving_count=2 → serving_time=False (KẾT THÚC SESSION)

10:30 → Phát hiện khách → serving_time=True (SESSION MỚI)
10:31 → Emotion: Fear
...
```

### 1.2 Trừ Điểm Emotion ĐẦU TIÊN

**Trước (v2.0):**
```python
# ❌ Trừ emotion XẤU NHẤT
for session in sessions:
    worst_penalty = 0.0
    for log in session:
        penalty = PENALTIES.get(emotion, 0.0)
        worst_penalty = max(worst_penalty, penalty)
    
    score -= worst_penalty
```

**Sau (v2.1):**
```python
# ✅ Trừ emotion TIÊU CỰC ĐẦU TIÊN
for session in sessions:
    first_bad_emotion_penalty = 0.0
    for log in session:
        penalty = PENALTIES.get(emotion, 0.0)
        if penalty > 0:  # Tìm thấy emotion tiêu cực đầu tiên
            first_bad_emotion_penalty = penalty
            break  # DỪNG LẠI
    
    if first_bad_emotion_penalty > 0:
        score -= first_bad_emotion_penalty
```

**So sánh ví dụ:**

```
Session 1: Happy → Anger (-8) → Sad (-5) → Disgust (-7)

v2.0 (Xấu nhất):
→ Trừ Disgust (-7) ❌ Phức tạp, phải duyệt hết

v2.1 (Đầu tiên):
→ Trừ Anger (-8) ✅ Đơn giản, dừng ngay
```

**Lợi ích:**
- ✅ Logic đơn giản hơn
- ✅ Performance tốt hơn (break sớm)
- ✅ Khuyến khích giữ thái độ tốt NGAY TỪ ĐẦU

---

## ⏰ 2. GRACE PERIOD - 30 PHÚT SAU KẾT THÚC CA

### **File:** `service/shift_attendance_service.py`

### 2.1 Timeline Mới

**Ca sáng (Day):**
```
08:00 ─────────────── 14:00 ──────── 14:30
  │                      │             │
  Bắt đầu ca         Kết thúc      Finalize
                         │             │
                         └─────────────┘
                         Grace Period
                      (30 phút checkout)
```

**Ca tối (Night):**
```
14:00 ─────────────── 20:00 ──────── 20:30
  │                      │             │
  Bắt đầu ca         Kết thúc      Finalize
                         │             │
                         └─────────────┘
                         Grace Period
                      (30 phút checkout)
```

### 2.2 Trong Grace Period

**KHÔNG được thực hiện:**
- ❌ Track absence (increment_absences_for_inactive)
- ❌ Đánh vắng nhân viên
- ❌ Phạt early checkout

**ĐƯỢC thực hiện:**
- ✅ Nhân viên có thể checkout bình thường
- ✅ Camera vẫn hoạt động
- ✅ Emotion vẫn được ghi (nhưng không trừ điểm do serving_time=False)

### 2.3 Code Scheduler

```python
def scheduler_loop():
    GRACE_PERIOD_MINUTES = 30
    
    while True:
        now_local = datetime.now(TZ)
        current_time = now_local.time()
        
        # Calculate grace period times
        day_end_grace = SHIFT_DAY_END + 30 phút = 14:30
        night_end_grace = SHIFT_NIGHT_END + 30 phút = 20:30
        
        # 1. Khởi tạo ca: đúng giờ (08:00, 14:00)
        if current_time == SHIFT_DAY_START:
            init_shift_rows('day', date)
        
        # 2. Finalize ca: SAU grace period (14:30, 20:30)
        if current_time == day_end_grace:  # 14:30
            finalize_shift_absents('day', date)
        
        # 3. Track absence: CHỈ NGOÀI grace period
        sh = current_shift(now_local)
        in_grace_period = False
        
        if sh == 'day' and 14:00 <= current_time < 14:30:
            in_grace_period = True
        elif sh == 'night' and 20:00 <= current_time < 20:30:
            in_grace_period = True
        
        if sh in ('day', 'night') and NOT in_grace_period:
            increment_absences_for_inactive(sh)
        
        sleep(10)
```

### 2.4 Auto Checkout

**Trước (v2.0):**
```python
# ❌ Checkout 5 phút trước (13:55, 19:55)
auto_checkout_time = shift_end - timedelta(minutes=5)
status = 'early'  # Bị phạt -10 điểm
```

**Sau (v2.1):**
```python
# ✅ Checkout ĐÚNG GIỜ kết thúc ca (14:00, 20:00)
auto_checkout_time = shift_end  # Không trừ 5 phút

# Giữ nguyên status (on_time/late)
if current_status == 'late':
    new_status = 'late'
else:
    new_status = 'on_time'

# KHÔNG đặt 'early' → KHÔNG bị phạt -10
```

**Impact:**

```
Nhân viên quên checkout:

v2.0:
- Auto checkout: 13:55
- Status: early
- Penalty: -10 điểm
- Điểm: 70

v2.1:
- Auto checkout: 14:00 (trong grace period)
- Status: on_time (giữ nguyên)
- Penalty: 0 điểm
- Điểm: 80

→ CÔNG BẰNG HƠN! ✅
```

---

## 📐 3. CÔNG THỨC TÍNH ĐIỂM (CẬP NHẬT)

### 🎯 **EMOTION SCORE**

```
Emotion_Score = 100 - Σ(first_bad_emotion_per_session)

Điều kiện:
1. CHỈ tính emotion khi serving_time = True
2. Session tự động phân tách bởi mark_seen():
   - no_serving_count >= 2 → hết session
3. Mỗi session: CHỈ trừ emotion TIÊU CỰC ĐẦU TIÊN

Penalties:
- Anger:    -8 điểm
- Disgust:  -7 điểm
- Fear:     -6 điểm
- Sad:      -5 điểm
- Surprise: -3 điểm

Giới hạn: 0 ≤ score ≤ 100
```

**Ví dụ:**
```
Session 1 (10:00-10:04):
  10:01 → Happy     (không trừ)
  10:02 → Anger     (trừ -8) ← ĐẦU TIÊN
  10:03 → Sad       (bỏ qua)
  10:04 → Disgust   (bỏ qua)
→ Trừ -8 điểm

Session 2 (10:30-10:33):
  10:30 → Fear      (trừ -6) ← ĐẦU TIÊN
  10:31 → Happy     (bỏ qua)
→ Trừ -6 điểm

Emotion_Score = 100 - 8 - 6 = 86 điểm
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

Lưu ý GRACE PERIOD:
- Auto checkout trong grace period: KHÔNG bị early penalty
- Status giữ nguyên (on_time/late)
```

### 🏆 **TOTAL SCORE (KPI)**

```
Total_Score = (Attendance_Score × 0.7) + (Emotion_Score × 0.3)

Giới hạn: 0 ≤ score ≤ 100
Round: 2 chữ số thập phân
```

---

## 🎬 4. WORKFLOW HOÀN CHỈNH (CẬP NHẬT)

```
08:00 - BẮT ĐẦU CA SÁNG
│
├─> Scheduler: init_shift_rows('day', date)
│   ├─> Tạo shift_attendance (serving_time=False, no_serving_count=0)
│   ├─> Tạo checklog (status='pending', check_in=NULL)
│   └─> Tạo KPI (100/100/100)
│
│
TRONG CA (08:00 - 14:00)
│
├─> Nhân viên check-in (08:05)
│   ├─> Status: 'late' (trễ 5 phút)
│   └─> Đảm bảo KPI tồn tại
│
├─> Camera: Phát hiện khách (10:00)
│   └─> mark_seen(user_id, is_serving=True)
│       ├─> serving_time = True
│       └─> no_serving_count = 0
│
├─> Camera: Emotion Anger (10:01)
│   └─> Lưu emotion_log (serving_time=True tại 10:00)
│       → Sẽ bị trừ điểm khi tính KPI
│
├─> Camera: Không thấy khách (10:03)
│   └─> mark_seen(user_id, is_serving=False)
│       └─> no_serving_count = 1
│
├─> Camera: Không thấy khách (10:04)
│   └─> mark_seen(user_id, is_serving=False)
│       ├─> no_serving_count = 2
│       └─> serving_time = False ← KẾT THÚC SESSION 1
│
├─> Camera: Phát hiện khách (10:30)
│   └─> mark_seen(user_id, is_serving=True) ← BẮT ĐẦU SESSION 2
│
├─> Mỗi 10s (08:00-14:00): Track absence
│   └─> Nếu (now - last_seen) > 30s: absence_count += 1
│
│
14:00 - KẾT THÚC CA (BẮT ĐẦU GRACE PERIOD)
│
├─> Scheduler: KHÔNG track absence (14:00-14:30)
│   └─> in_grace_period = True → SKIP increment_absences
│
├─> Nhân viên checkout (14:10)
│   ├─> Tính total_hours
│   ├─> Status: giữ nguyên 'late'
│   └─> Tính lại KPI:
│       ├─> Emotion: 100 - 8 (Session 1: Anger) = 92
│       ├─> Attendance: 
│       │   hours_score = 80
│       │   late penalty = -10
│       │   → 70 điểm
│       └─> Total = 70*0.7 + 92*0.3 = 76.6 điểm
│
│
14:30 - FINALIZE SHIFT (SAU GRACE PERIOD)
│
└─> Scheduler: finalize_shift_absents('day', date)
    │
    └─> Nhân viên X: Có check-in, KHÔNG check-out
        ├─> Auto checkout lúc 14:00 (đúng giờ kết thúc ca)
        ├─> Status: giữ nguyên 'on_time' (KHÔNG bị early)
        ├─> Total_hours: 6.0h (đầy đủ)
        └─> Tính lại KPI:
            ├─> Emotion: 100 (không có emotion tiêu cực)
            ├─> Attendance: 80 (không penalty)
            └─> Total = 80*0.7 + 100*0.3 = 86 điểm ✅
```

---

## 📊 5. SO SÁNH v2.0 vs v2.1

### **Trường hợp 1: Quên checkout**

| Thuộc tính | v2.0 | v2.1 |
|------------|------|------|
| Auto checkout time | 13:55 (5p trước) | **14:00 (đúng giờ)** |
| Status | early | **on_time** |
| Early penalty | -10 điểm | **0 điểm** |
| Total_hours | 5.92h | **6.0h** |
| Hours_score | 80 | **80** |
| Attendance_score | 70 | **80** |
| Total (giả sử emotion=100) | 79 | **86** |
| **Chênh lệch** | | **+7 điểm** ✅ |

### **Trường hợp 2: Emotion trong session**

| Session | Emotions | v2.0 (Xấu nhất) | v2.1 (Đầu tiên) | So sánh |
|---------|----------|-----------------|-----------------|---------|
| 1 | Happy, Anger, Disgust, Sad | -7 (Disgust) | **-8 (Anger)** | Đầu tiên nặng hơn |
| 2 | Sad, Fear, Surprise | -6 (Fear) | **-5 (Sad)** | Đầu tiên nhẹ hơn |
| 3 | Surprise, Anger | -8 (Anger) | **-3 (Surprise)** | Đầu tiên nhẹ hơn |

**Kết luận:** 
- v2.1 đơn giản hơn về logic
- Khuyến khích giữ thái độ tốt NGAY TỪ ĐẦU với khách
- Điểm số phụ thuộc vào impression đầu tiên

---

## ✅ 6. CHECKLIST XÁC NHẬN (v2.1)

| Yêu cầu | Trạng thái | Chi tiết |
|---------|------------|----------|
| ✅ Kiểm tra serving_time | **Hoàn thành** | Chỉ trừ điểm emotion khi đang phục vụ khách |
| ✅ Session tracking (2 lần không thấy khách) | **Hoàn thành** | Sử dụng no_serving_count trong mark_seen() |
| ✅ Trừ điểm emotion đầu tiên | **Hoàn thành** | Đơn giản hóa, không cần tìm xấu nhất |
| ✅ Grace period 30 phút | **Hoàn thành** | 14:00-14:30, 20:00-20:30 |
| ✅ KHÔNG track absence trong grace period | **Hoàn thành** | Kiểm tra in_grace_period trước khi track |
| ✅ Auto checkout đúng giờ | **Hoàn thành** | 14:00, 20:00 (không trừ 5 phút) |
| ✅ KHÔNG penalty early cho auto checkout | **Hoàn thành** | Giữ nguyên status on_time/late |
| ✅ Finalize sau grace period | **Hoàn thành** | 14:30, 20:30 |

---

## 📝 7. KẾT LUẬN

### ✅ **CÁC CẢI TIẾN (v2.1):**

1. ✅ **Logic đơn giản hơn:**
   - Emotion: trừ điểm ĐẦU TIÊN thay vì xấu nhất
   - Session: dựa vào no_serving_count có sẵn

2. ✅ **Công bằng hơn:**
   - Grace period 30 phút cho checkout
   - Auto checkout đúng giờ, không bị early penalty
   - Không track absence trong grace period

3. ✅ **Performance tốt hơn:**
   - Break sớm khi tìm emotion đầu tiên
   - Giảm số lần duyệt loop

4. ✅ **Khuyến khích hành vi tốt:**
   - Impression đầu tiên quan trọng
   - Nhân viên có thời gian checkout thoải mái

### 🎯 **HIỆU QUẢ DỰ KIẾN:**

- Nhân viên quên checkout: **+7 điểm** (80 thay vì 70)
- Logic emotion đơn giản hơn: dễ debug và maintain
- Grace period: giảm stress cho nhân viên cuối ca
- Công thức vẫn giữ nguyên: 70% attendance + 30% emotion

---

**🏆 Hệ thống v2.1 đã sẵn sàng với logic tối ưu hơn!**

---

**File được sửa:**
1. `service/kpi_calculator.py` - Trừ điểm emotion đầu tiên
2. `service/shift_attendance_service.py` - Grace period + scheduler timing

**Khuyến nghị:**
- Test kỹ grace period logic (14:00-14:30, 20:00-20:30)
- Verify auto checkout không bị early penalty
- Monitor emotion scoring với logic mới