# 🧪 TEST SUITE v2.1 - HOÀN CHỈNH

## 📦 Đã Tạo Các File Test

### 1. **test_iot_v21_comprehensive.py** (790 dòng)
Integration tests hoàn chỉnh cho tất cả features v2.1.

**Test Classes:**
- `TestSessionTracking` - Session tracking với no_serving_count
- `TestEmotionScoringFirstBad` - Emotion scoring (first bad emotion)
- `TestGracePeriod` - Grace period logic ⏰
- `TestAutoCheckout` - Auto checkout (no early penalty) ⏰
- `TestKPICalculation` - KPI calculation (70-30 ratio)
- `TestThreadSafeConcurrentAPIs` - Thread-safety tests 🔥
- `TestRealWorldScenarios` - Real-world scenarios

**Đặc điểm:**
- ✅ 20+ test cases
- ✅ Thread-safety: 50+ concurrent requests
- ✅ Time-dependent tests (grace period)
- ⚠️ Cần backend chạy

---

### 2. **test_mock_v21.py** (550 dòng)
Unit tests với unittest.mock, không cần backend.

**Test Classes:**
- `TestKPICalculatorMocked` - Test kpi_calculator.py logic
- `TestShiftAttendanceServiceMocked` - Test shift_attendance_service.py
- `TestSessionTrackingMocked` - Test session logic
- `TestGracePeriodMocked` - Test grace period detection
- `TestThreadSafetyMocked` - Test thread-safety mechanisms

**Đặc điểm:**
- ✅ 15+ test cases
- ✅ Chạy nhanh (< 5 seconds)
- ✅ Không cần backend
- ✅ Mock database operations

---

### 3. **run_tests_v21.py** (120 dòng)
Test runner với nhiều options.

**Usage:**
```bash
python run_tests_v21.py                    # All tests
python run_tests_v21.py --session          # Session tracking only
python run_tests_v21.py --emotion          # Emotion scoring only
python run_tests_v21.py --grace            # Grace period only
python run_tests_v21.py --thread           # Thread-safety only
python run_tests_v21.py --quick            # Quick (time-independent)
python run_tests_v21.py -v                 # Verbose output
```

---

### 4. **test_dashboard.py** (220 dòng)
Dashboard để xem tổng quan test status.

**Features:**
- ✅ Check backend status
- ✅ Run mock tests automatically
- ✅ Run integration tests if backend available
- ✅ Show test coverage
- ✅ Show recommendations based on time

**Usage:**
```bash
python test_dashboard.py
```

**Output:**
```
================================================================================
🧪 TEST DASHBOARD - v2.1
================================================================================
📅 Date: 2025-12-21 10:30:00
================================================================================

🔹 Test Files Status
--------------------------------------------------------------------------------
   ✅ test_iot_v21_comprehensive.py           - Integration tests
   ✅ test_mock_v21.py                        - Mock unit tests
   ✅ run_tests_v21.py                        - Test runner
   ✅ test_config.ini                         - Test configuration
   ✅ TESTS_V21_README.md                     - Test documentation

🔹 Test Coverage by Feature
--------------------------------------------------------------------------------
   ✅ Covered   Session tracking (no_serving_count >= 2)
   ✅ Covered   Emotion scoring (first bad emotion)
   ✅ Covered   Grace period (30 min after shift)
   ✅ Covered   Auto checkout (no early penalty)
   ✅ Covered   KPI calculation (70-30 ratio)
   ✅ Covered   Thread-safety (concurrent APIs)
   ✅ Covered   Real-world scenarios

🔹 Running Mock Tests (No Backend Required)...
--------------------------------------------------------------------------------
✅ Mock Tests: PASSED
   Tests run: 15
   Passed: 15
   Failed: 0

🔹 Running Quick Integration Tests (Backend Required)...
--------------------------------------------------------------------------------
✅ Integration Tests: PASSED
   Tests run: 12
   Passed: 12
   Failed: 0

================================================================================
📊 OVERALL STATUS
================================================================================
✅ Mock Tests: PASSED
✅ Integration Tests: PASSED
================================================================================

🔹 Recommendations
--------------------------------------------------------------------------------
   ✅ Backend is running
   ⏰ Not in grace period
      → Grace period tests will be skipped
      → Run full tests at 14:00-14:30 or 20:00-20:30

   💡 Quick Commands:
      python test_mock_v21.py                    # Fast, no backend
      python run_tests_v21.py --quick            # Quick integration
      python test_iot_v21_comprehensive.py       # Full suite
```

---

### 5. **test_config.ini**
Configuration file cho tests.

**Sections:**
- `[test_environment]` - Backend URL, timezone
- `[test_users]` - Test user IDs
- `[shift_times]` - Shift configuration
- `[test_thresholds]` - Assertion thresholds
- `[concurrency]` - Thread-safety parameters
- `[penalties]` - Emotion penalties
- `[kpi_weights]` - KPI weights

---

### 6. **test_requirements.txt**
Dependencies cho tests.

**Key packages:**
- `unittest2`, `pytest` - Test frameworks
- `requests` - HTTP requests
- `pytz` - Timezone handling
- `mock` - Mocking
- `coverage` - Code coverage
- `locust` - Load testing (optional)

---

### 7. **TESTS_V21_README.md** (500 dòng)
Comprehensive documentation.

**Sections:**
- 📋 Tổng quan
- 🚀 Cách chạy tests
- 📊 Test categories chi tiết
- ⏰ Time-dependent tests
- 🎯 Expected results
- 🐛 Troubleshooting
- 📈 Performance benchmarks
- 🔧 Customization

---

## 🎯 Quick Start

### Option 1: Fastest (Mock Tests)
```bash
python test_mock_v21.py
```
- ⚡ Chạy trong < 5 giây
- ✅ Không cần backend
- ✅ Test logic trực tiếp

### Option 2: Dashboard (Auto)
```bash
python test_dashboard.py
```
- 🎨 Tổng quan đẹp mắt
- 🤖 Tự động detect backend
- 📊 Show coverage và recommendations

### Option 3: Quick Integration
```bash
python app.py                          # Terminal 1: Start backend
python run_tests_v21.py --quick        # Terminal 2: Run tests
```
- ✅ Test với API thực
- ⏭️  Skip time-dependent tests
- 🚀 Nhanh hơn full suite

### Option 4: Full Suite
```bash
python test_iot_v21_comprehensive.py
```
- 🔥 Tất cả tests (20+ cases)
- ⏰ Bao gồm grace period tests
- 🔒 Thread-safety với 50+ concurrent requests

---

## 📊 Test Coverage Summary

| Feature | Mock Tests | Integration Tests | Thread-Safety |
|---------|-----------|-------------------|---------------|
| Session tracking | ✅ 3 tests | ✅ 3 tests | ✅ Covered |
| Emotion scoring | ✅ 3 tests | ✅ 3 tests | ✅ Covered |
| Grace period | ✅ 2 tests | ✅ 2 tests | N/A |
| Auto checkout | ✅ 2 tests | ✅ 2 tests | N/A |
| KPI calculation | ✅ 3 tests | ✅ 2 tests | N/A |
| Concurrent APIs | ✅ 2 tests | ✅ 5 tests | ✅ 50+ load |
| **TOTAL** | **15 tests** | **17 tests** | **5 tests** |

**Overall: 37+ test cases**

---

## 🔥 Thread-Safety Load Testing

### Concurrent Request Loads:

| Operation | Concurrent Requests | Purpose |
|-----------|---------------------|---------|
| Check-in | 10 devices | Multiple devices check-in simultaneously |
| Emotion logs | 20 requests | Multiple emotion logs from different devices |
| Mark seen | 15 updates | Rapid customer detection changes |
| Check-out | 10 devices | Multiple devices check-out together |
| Race condition | 50 requests | Stress test same user, same operation |

**Total test load: ~100 concurrent requests**

---

## ✅ Checklist Deployment

### Before Deployment:
- [ ] ✅ All mock tests pass
  ```bash
  python test_mock_v21.py
  ```

- [ ] ✅ Quick integration tests pass
  ```bash
  python run_tests_v21.py --quick
  ```

- [ ] ✅ Thread-safety tests pass
  ```bash
  python run_tests_v21.py --thread
  ```

- [ ] ✅ Grace period tests pass (chạy đúng giờ)
  ```bash
  # At 14:00-14:30 or 20:00-20:30
  python run_tests_v21.py --grace
  ```

- [ ] ✅ KPI calculation verified
  ```bash
  python run_tests_v21.py --kpi
  ```

- [ ] ✅ Full suite pass
  ```bash
  python test_iot_v21_comprehensive.py
  ```

- [ ] ✅ Load test với production-like concurrency
  ```bash
  # Optional: Use locust for load testing
  locust -f locustfile.py
  ```

---

## 📈 Performance Expectations

### Mock Tests:
- Runtime: < 5 seconds
- Memory: < 50 MB
- Success rate: 100%

### Integration Tests (Quick):
- Runtime: 30-60 seconds
- Memory: < 100 MB
- Success rate: 100% (if backend healthy)

### Full Suite:
- Runtime: 2-3 minutes
- Memory: < 150 MB
- Success rate: 95%+ (time-dependent tests may skip)

### Thread-Safety:
- 50 concurrent requests: < 500ms response time
- 100 concurrent requests: < 1000ms response time
- No race conditions
- No data corruption

---

## 🐛 Common Issues & Fixes

### 1. Import Errors
```
ModuleNotFoundError: No module named 'service'
```
**Fix:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# hoặc
cd face-recognition && python test_mock_v21.py
```

### 2. Connection Refused
```
requests.exceptions.ConnectionError
```
**Fix:**
```bash
# Start backend first
python app.py
```

### 3. Tests Skipped
```
⏭️  Skipped: Not in grace period
```
**Fix:** Chạy `--quick` hoặc chờ đến grace period (14:00-14:30, 20:00-20:30)

### 4. Test Users Not Found
```
❌ User ID not found
```
**Fix:** Update `TEST_USERS` trong test files với IDs thực tế

---

## 🎓 Advanced Usage

### Run with pytest
```bash
pip install pytest pytest-cov

# Run all tests
pytest test_iot_v21_comprehensive.py -v

# With coverage
pytest test_mock_v21.py --cov=service --cov-report=html

# Parallel execution
pytest test_mock_v21.py -n auto
```

### Generate Coverage Report
```bash
coverage run test_mock_v21.py
coverage report
coverage html
# Open htmlcov/index.html
```

### Load Testing with Locust
```bash
pip install locust

# Create locustfile.py (sample IoT load)
locust -f locustfile.py --host=http://localhost:8000
# Open http://localhost:8089
```

---

## 📞 Support

Nếu gặp vấn đề:

1. **Kiểm tra dashboard:**
   ```bash
   python test_dashboard.py
   ```

2. **Chạy mock tests (nhanh nhất):**
   ```bash
   python test_mock_v21.py
   ```

3. **Check backend health:**
   ```bash
   curl http://localhost:8000/api/health
   ```

4. **Review logs:**
   - Backend logs: `face-recognition/logs/`
   - Test output: terminal output

---

## 🏆 Success Criteria

### Để xác nhận v2.1 hoạt động đúng:

1. ✅ **Mock tests**: 15/15 passed
2. ✅ **Quick integration**: 12/12 passed
3. ✅ **Thread-safety**: 5/5 passed, no race conditions
4. ✅ **Grace period**: 2/2 passed (when in grace period)
5. ✅ **Full suite**: 95%+ success rate

### Performance:
- ✅ Response time < 500ms (normal load)
- ✅ Response time < 1s (50+ concurrent)
- ✅ No database deadlocks
- ✅ No data corruption

### Logic Correctness:
- ✅ Session ends after 2 no-customer
- ✅ First bad emotion only penalized
- ✅ Grace period: no absence tracking
- ✅ Auto checkout: no early penalty
- ✅ KPI ratio: 70% attendance + 30% emotion

---

**🎉 Test Suite v2.1 is Production-Ready!**

**Tổng số files test:** 7 files  
**Tổng số test cases:** 37+ cases  
**Test coverage:** Session tracking, Emotion scoring, Grace period, Auto checkout, KPI calculation, Thread-safety  
**Load test capability:** 100+ concurrent requests
