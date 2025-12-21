# 🧪 IoT Backend Tests v2.1 - Hướng Dẫn






























rich>=13.5.2colorama>=0.4.6# Optional: Pretty outputlocust>=2.15.1  # For load testing# Performance testingcoverage>=7.3.0# Code coveragemock>=5.1.0# Mockingaiohttp>=3.8.5# Async/threadingpytz>=2023.3# Time handlingrequests>=2.31.0# HTTP requestspytest-mock>=3.11.1pytest-cov>=4.1.0pytest>=7.4.0unittest2>=1.1.0# Core testing## 📋 Tổng Quan

Test suite toàn diện cho logic v2.1 với các tính năng:
- ✅ Session tracking (no_serving_count >= 2)
- ✅ Emotion scoring (first bad emotion per session)
- ✅ Grace period (30 phút sau ca)
- ✅ Auto checkout (không bị early penalty)
- ✅ KPI calculation (70% attendance + 30% emotion)
- ✅ Thread-safe concurrent APIs

---

## 🚀 Cách Chạy Tests

### 1️⃣ Chuẩn Bị Môi Trường

```bash
cd face-recognition

# Install dependencies (nếu chưa có)
pip install requests pytz

# Đảm bảo backend đang chạy
python app.py
# hoặc
uvicorn app:app --reload
```

### 2️⃣ Cập Nhật Test Users

Mở [test_iot_v21_comprehensive.py](test_iot_v21_comprehensive.py) và update `TEST_USERS`:

```python
TEST_USERS = {
    "user1": {"id": 1, "name": "Nguyễn Văn A", "face_id": "face_001"},
    "user2": {"id": 2, "name": "Trần Thị B", "face_id": "face_002"},
    "user3": {"id": 3, "name": "Lê Văn C", "face_id": "face_003"},
}
```

### 3️⃣ Chạy Tests

#### Option A: Chạy Tất Cả Tests
```bash
python test_iot_v21_comprehensive.py
```

#### Option B: Sử dụng Test Runner
```bash
# Tất cả tests
python run_tests_v21.py

# Chỉ session tracking
python run_tests_v21.py --session

# Chỉ emotion scoring
python run_tests_v21.py --emotion

# Chỉ grace period (chạy trong grace period 14:00-14:30 hoặc 20:00-20:30)
python run_tests_v21.py --grace

# Chỉ thread-safety
python run_tests_v21.py --thread

# Quick tests (bỏ qua time-dependent tests)
python run_tests_v21.py --quick

# Verbose output
python run_tests_v21.py -v
```

#### Option C: Sử dụng pytest
```bash
# Install pytest
pip install pytest

# Run all tests
pytest test_iot_v21_comprehensive.py -v

# Run specific test class
pytest test_iot_v21_comprehensive.py::TestSessionTracking -v

# Run specific test method
pytest test_iot_v21_comprehensive.py::TestEmotionScoringFirstBad::test_first_bad_emotion_penalty -v
```

---

## 📊 Test Categories

### 1. **TestSessionTracking** 
Tests cho session tracking logic:

✅ `test_session_detection_starts_with_customer`
- Phát hiện khách → serving_time=True

✅ `test_session_ends_after_two_no_customer`
- 2 lần liên tiếp không thấy khách → serving_time=False

✅ `test_multiple_sessions_in_shift`
- Nhiều sessions trong 1 ca

**Chạy:**
```bash
python run_tests_v21.py --session
```

---

### 2. **TestEmotionScoringFirstBad**
Tests cho emotion scoring logic:

✅ `test_first_bad_emotion_penalty`
- Session: Happy → Anger → Sad → Disgust
- Expected: Chỉ trừ Anger (-8), bỏ qua Sad và Disgust

✅ `test_no_penalty_for_good_emotions`
- Tất cả emotions tốt → score = 100

✅ `test_emotion_without_serving_time_ignored`
- Emotion khi không phục vụ khách → không trừ điểm

**Chạy:**
```bash
python run_tests_v21.py --emotion
```

---

### 3. **TestGracePeriod**
Tests cho grace period logic (⚠️ time-dependent):

✅ `test_no_absence_tracking_during_grace_period`
- Grace period: KHÔNG track absence
- **Chạy lúc:** 14:00-14:30 hoặc 20:00-20:30

✅ `test_finalize_after_grace_period`
- Finalize xảy ra ở 14:30 hoặc 20:30
- **Chạy lúc:** 14:30 hoặc 20:30

**Chạy:**
```bash
# Chỉ chạy trong grace period!
python run_tests_v21.py --grace
```

---

### 4. **TestAutoCheckout**
Tests cho auto checkout logic (⚠️ time-dependent):

✅ `test_auto_checkout_at_shift_end`
- Checkout ĐÚNG giờ (14:00, 20:00), không phải 13:55 hoặc 19:55

✅ `test_no_early_penalty_for_auto_checkout`
- Auto checkout KHÔNG bị early penalty
- Status = 'on_time' hoặc 'late', KHÔNG phải 'early'

**Chạy:**
```bash
# Chỉ chạy trong grace period!
python run_tests_v21.py --checkout
```

---

### 5. **TestKPICalculation**
Tests cho KPI calculation:

✅ `test_kpi_ratio_70_30`
- KPI = attendance × 0.7 + emotion × 0.3

✅ `test_attendance_impact_higher_than_emotion`
- Attendance ảnh hưởng nhiều hơn (70% vs 30%)

**Chạy:**
```bash
python run_tests_v21.py --kpi
```

---

### 6. **TestThreadSafeConcurrentAPIs** 🔥
Tests cho thread-safety và concurrent requests:

✅ `test_concurrent_checkin`
- Nhiều devices check-in cùng lúc
- **Load:** 10 concurrent requests

✅ `test_concurrent_emotion_logs`
- Nhiều devices log emotions đồng thời
- **Load:** 20 concurrent requests

✅ `test_concurrent_mark_seen`
- Nhiều devices update serving_time
- **Load:** 15 concurrent requests

✅ `test_concurrent_checkout`
- Nhiều devices checkout cùng lúc
- **Load:** 10 concurrent requests

✅ `test_race_condition_prevention`
- Test race condition với cùng 1 user
- **Load:** 50 concurrent requests cùng user

**Chạy:**
```bash
python run_tests_v21.py --thread
```

---

### 7. **TestRealWorldScenarios**
Tests cho tình huống thực tế:

✅ `test_full_shift_with_grace_period`
- Mô phỏng 1 ca làm việc hoàn chỉnh với grace period

✅ `test_multiple_bad_sessions`
- Nhiều sessions với bad emotions

**Chạy:**
```bash
python run_tests_v21.py --scenario
```

---

## ⏰ Lưu Ý Về Thời Gian

### Time-Independent Tests (Chạy bất cứ lúc nào)
- ✅ TestSessionTracking
- ✅ TestEmotionScoringFirstBad
- ✅ TestKPICalculation
- ✅ TestThreadSafeConcurrentAPIs

### Time-Dependent Tests (Chạy trong giờ cụ thể)
- ⏰ TestGracePeriod → **14:00-14:30** hoặc **20:00-20:30**
- ⏰ TestAutoCheckout → **14:00-14:30** hoặc **20:00-20:30**

### Chạy Quick Tests (Bỏ qua time-dependent)
```bash
python run_tests_v21.py --quick
```

---

## 🎯 Expected Results

### ✅ Successful Test Output
```
======================================================================
🧪 IoT BACKEND COMPREHENSIVE TESTS (v2.1)
======================================================================

Test Coverage:
  1. ✅ Session tracking (no_serving_count >= 2)
  2. ✅ Emotion scoring (first bad emotion)
  3. ✅ Grace period (30 min after shift)
  4. ✅ Auto checkout (no early penalty)
  5. ✅ KPI calculation (70-30 ratio)
  6. ✅ Thread-safe concurrent APIs
======================================================================

test_session_detection_starts_with_customer (test_iot_v21_comprehensive.TestSessionTracking)
🧪 Test: Session starts when customer detected ... ok
✅ Session started: serving_time=True

...

======================================================================
📊 TEST SUMMARY
======================================================================
Tests run: 20
✅ Passed: 20
❌ Failed: 0
⚠️  Errors: 0
⏭️  Skipped: 0
======================================================================

🎉 ALL TESTS PASSED!
```

### ⚠️ Skipped Tests (Ngoài giờ)
```
test_no_absence_tracking_during_grace_period ... skipped 'Not in grace period'
test_finalize_after_grace_period ... skipped 'Not at finalize time'
```

---

## 🐛 Troubleshooting

### 1. Connection Error
```
requests.exceptions.ConnectionError: Connection refused
```
**Fix:** Đảm bảo backend đang chạy ở `http://localhost:8000`

### 2. User Not Found
```
❌ Failed: User ID not found
```
**Fix:** Update `TEST_USERS` trong test file với user IDs thực tế

### 3. Tests Skipped
```
⏭️  Skipped: Not in grace period
```
**Fix:** Chạy tests trong grace period (14:00-14:30, 20:00-20:30) hoặc dùng `--quick`

### 4. Thread-Safety Failures
```
❌ Failed: Race condition detected
```
**Fix:** Kiểm tra database locks trong backend code

---

## 📈 Performance Benchmarks

### Thread-Safety Tests Load:
- **Concurrent check-ins:** 10 devices × 1 request = 10 requests
- **Concurrent emotions:** 3 users × 5 emotions = 15 requests  
- **Concurrent mark_seen:** 3 users × 3 updates = 9 requests
- **Race condition:** 1 user × 50 requests = 50 requests

**Total load:** ~100 concurrent requests

**Expected response time:** < 500ms per request

---

## 🔧 Customization

### Thay Đổi Base URL
```python
# Trong test_iot_v21_comprehensive.py
BASE_URL = "http://192.168.1.100:8000"  # Your backend URL
```

### Thay Đổi Số Lượng Concurrent Requests
```python
# Trong TestThreadSafeConcurrentAPIs
with ThreadPoolExecutor(max_workers=50) as executor:  # Tăng từ 10 lên 50
    ...
```

### Thêm Test Users
```python
TEST_USERS = {
    "user1": {"id": 1, ...},
    "user2": {"id": 2, ...},
    "user3": {"id": 3, ...},
    "user4": {"id": 4, ...},  # Thêm users
}
```

---

## 📚 Related Files

### Test Files
- [test_iot_v21_comprehensive.py](test_iot_v21_comprehensive.py) - Integration tests (cần backend chạy)
- [test_mock_v21.py](test_mock_v21.py) - Unit tests với mocks (không cần backend)
- [run_tests_v21.py](run_tests_v21.py) - Test runner script
- [test_config.ini](test_config.ini) - Test configuration

### Documentation
- [FINAL_LOGIC_REPORT_V2.1.md](../FINAL_LOGIC_REPORT_V2.1.md) - Logic documentation v2.1
- [TESTS_V21_README.md](TESTS_V21_README.md) - This file

### Source Code Being Tested
- [kpi_calculator.py](service/kpi_calculator.py) - KPI calculation logic
- [shift_attendance_service.py](service/shift_attendance_service.py) - Shift & grace period logic

---

## 🎯 Quick Start Guide

### Option 1: Mock Tests (No Backend Required) ⚡
```bash
# Fastest way to test logic
python test_mock_v21.py
```

### Option 2: Integration Tests (Backend Required) 🔌
```bash
# Start backend first
python app.py

# In another terminal
python run_tests_v21.py --quick
```

### Option 3: Full Test Suite (All Tests) 🚀
```bash
# Backend running + correct time (grace period)
python test_iot_v21_comprehensive.py
```

---

## ✅ Checklist Trước Khi Deploy

- [ ] Tất cả unit tests pass (quick mode)
- [ ] Thread-safety tests pass với 50+ concurrent requests
- [ ] Grace period tests pass (chạy đúng giờ)
- [ ] KPI calculation accuracy verified
- [ ] Auto checkout không bị early penalty
- [ ] Emotion scoring chỉ trừ first bad emotion
- [ ] Session tracking hoạt động đúng với no_serving_count

---

**📝 Note:** Tests được thiết kế để chạy với backend thực. Để test mà không cần backend, có thể sử dụng mocking (unittest.mock).

**🎯 Goal:** 100% test coverage cho logic v2.1!
