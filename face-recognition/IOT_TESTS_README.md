# IoT Backend Integration Tests

## 📋 Mục đích

Test suite toàn diện để verify tất cả các trường hợp IoT devices (Raspberry Pi) gửi data đến backend.

## 🧪 Test Coverage

### 1. **test_iot_integration.py** - Basic Integration Tests

Tests cơ bản cho tất cả operations:

#### ✅ Check-in Scenarios:
- Check-in đúng giờ (on-time)
- Check-in muộn (late)
- Check-in sai ca (wrong shift)
- Check-in ngoài giờ làm việc
- Check-in trùng lặp (duplicate prevention)

#### ✅ Check-out Scenarios:
- Check-out bình thường sau check-in
- Check-out sớm (early)
- Check-out nhiều lần (multiple checkouts)
- Check-out khi chưa check-in (should fail)

#### ✅ Emotion Log Scenarios:
- Log cảm xúc tốt khi có khách (happy, smile)
- Log cảm xúc xấu khi có khách (angry, sad, disgust)
- Log cảm xúc xấu khi không có khách (bored)
- Log cảm xúc không có ảnh

#### ✅ Concurrent Request Tests:
- Nhiều IoT devices check-in cùng lúc
- Nhiều devices gửi emotion logs đồng thời
- Nhiều devices check-out cùng lúc

#### ✅ Error Handling:
- User không tồn tại
- Data không hợp lệ
- Confidence score sai

#### ✅ KPI Calculation:
- Tính KPI sau checkout
- Verify emotion và attendance scores

---

### 2. **test_iot_scenarios.py** - Advanced Scenario Tests

Tests các tình huống phức tạp thực tế:

#### 📊 Emotion Scoring Scenarios:
- **Scenario 1**: Tất cả emotions tốt khi có khách → Emotion score = 100
- **Scenario 2**: Emotions xấu khi có khách → Heavy penalty
- **Scenario 3**: Emotions xấu khi không có khách → Light penalty
- **Scenario 4**: Mix emotions (50/50) → Medium score

#### 📊 Attendance Scenarios:
- **Scenario 5**: Check-in đúng giờ, làm đủ giờ → Attendance score = 100
- **Scenario 6**: Check-in muộn + Check-out sớm → Penalties applied

#### 📊 Real-World Full Day Scenarios:
- **Scenario 7**: Một ngày làm việc tốt
  - Check-in đúng giờ
  - 80% emotions tốt, 20% neutral
  - Check-out đúng giờ
  - **Expected**: Total score > 85

- **Scenario 8**: Một ngày khó khăn
  - Check-in có thể muộn
  - Nhiều bad emotions (stress, angry)
  - Check-out có thể sớm
  - **Expected**: Total score < 60

---

## 🚀 Cách chạy Tests

### ⏰ ĐỀ CẢI - Chạy Tests vào GIỜ LÀM VIỆC

Tests được thiết kế để kiểm tra hệ thống thực tế, nên **phụ thuộc vào thời gian hiện tại**.

**Giờ làm việc hợp lệ:**
- ☀️ **Ca sáng**: 08:00 - 14:00
- 🌙 **Ca chiều**: 14:00 - 20:00

**Nếu chạy ngoài giờ làm việc:**
- ✅ test_iot_scenarios.py sẽ **skip gracefully** 
- ⚠️ test_iot_integration.py sẽ **fail** cho tests check-in/emotion

### Chạy tất cả tests:
```bash
cd face-recognition

# Run basic integration tests (chạy trong giờ làm việc)
python test_iot_integration.py

# Run advanced scenario tests (chạy trong giờ làm việc)
python test_iot_scenarios.py

# Run cả hai
python test_iot_integration.py && python test_iot_scenarios.py
```

### Chạy với pytest (optional):
```bash
pytest test_iot_integration.py -v
pytest test_iot_scenarios.py -v
pytest test_iot_*.py -v  # Run all IoT tests
```

### Chạy specific test:
```bash
# Run một test class
python -m unittest test_iot_integration.TestIoTBackendIntegration

# Run một test method cụ thể
python -m unittest test_iot_integration.TestIoTBackendIntegration.test_checkin_on_time_day_shift
```

---

## 📊 Test Output

### Successful Test Output:
```
======================================================================
🤖 IoT BACKEND INTEGRATION TESTS
======================================================================

Testing all scenarios from IoT devices to backend:
  1. Check-in scenarios (on-time, late, wrong shift, outside hours)
  2. Check-out scenarios (normal, early, multiple, without check-in)
  3. Emotion logs (good/bad, with/without customers)
  4. Concurrent requests (multiple devices)
  5. Error handling (invalid users, data)
  6. KPI calculation
======================================================================

test_checkin_on_time_day_shift (__main__.TestIoTBackendIntegration)
Test check-in đúng giờ ca sáng (08:00-14:00) ... ok
✅ Check-in on-time (day shift): {'success': True, 'id': 123, 'status': 'on_time'}

test_emotion_log_good_with_customer (__main__.TestIoTBackendIntegration)
Test log cảm xúc tốt khi có khách (serving_time=True) ... ok
✅ Good emotion with customer: {'success': True, 'id': 456}

...

======================================================================
📊 TEST SUMMARY
======================================================================
✅ Tests run: 25
✅ Successes: 25
❌ Failures: 0
❌ Errors: 0

🎉 ALL TESTS PASSED! IoT integration is working correctly.
======================================================================
```

---

## 🔧 Requirements

### Dependencies:
```bash
# Already in requirements.txt
pymysql
pytz
numpy
opencv-python
fastapi
```

### Database Setup:
```bash
# Ensure MySQL is running
# Database: testtest2
# Tables: nhanvien, checklog, emotion_log, shift_attendance, kpi

# Run migrations if needed
python db/init_db.py
```

---

## 🎯 Test Scenarios Matrix

| Scenario | Test File | Test Method | Expected Result |
|----------|-----------|-------------|-----------------|
| Check-in on-time | test_iot_integration.py | test_checkin_on_time_day_shift | success, status='on_time' |
| Check-in late | test_iot_integration.py | test_checkin_late_day_shift | success, status='late' |
| Check-in duplicate | test_iot_integration.py | test_checkin_duplicate | second fails |
| Check-out normal | test_iot_integration.py | test_checkout_normal | success, total_hours > 0 |
| Check-out without check-in | test_iot_integration.py | test_checkout_without_checkin | fail |
| Good emotion + customer | test_iot_integration.py | test_emotion_log_good_with_customer | success |
| Bad emotion + customer | test_iot_scenarios.py | test_scenario_2_bad_emotions_with_customers | emotion_score < 70 |
| Bad emotion - customer | test_iot_scenarios.py | test_scenario_3_bad_emotions_without_customers | emotion_score > 70 |
| Concurrent check-ins | test_iot_integration.py | test_concurrent_checkins | all success |
| Full good day | test_iot_scenarios.py | test_scenario_7_typical_good_day | total_score > 85 |
| Full difficult day | test_iot_scenarios.py | test_scenario_8_difficult_day | total_score < 80 |

---

## 📝 Test Data

### Test Users Created:
```python
User IDs: 9000-9004  # For basic integration tests
User IDs: 9100-9102  # For advanced scenario tests
```

### Shifts:
- Day shift: 08:00 - 14:00
- Night shift: 14:00 - 20:00

### Emotion Types Tested:
- Good: `happy`, `surprise`, `neutral`
- Bad: `angry`, `sad`, `disgust`, `fear`, `bored`

---

## ⚠️ Important Notes

### 1. **Timezone**
Tests sử dụng Asia/Ho_Chi_Minh (UTC+7). Đảm bảo:
```python
TZ = pytz.timezone('Asia/Ho_Chi_Minh')
```

### 2. **Test Isolation**
Mỗi test tự động:
- Setup: Tạo test data cần thiết
- Teardown: Cleanup test data (checklogs, emotions)

### 3. **Time-Dependent Tests**
Một số tests phụ thuộc vào thời gian thực:
- Check-in on-time vs late → phụ thuộc current time
- Check-out early → phụ thuộc shift end time

### 4. **Concurrent Tests**
Tests concurrent sử dụng threading:
- Verify thread-safety của MySQL connection pool
- Verify thread-safety của FAISS operations

### 5. **Cleanup**
Nếu tests fail và không cleanup:
```sql
-- Manual cleanup
DELETE FROM checklog WHERE user_id BETWEEN 9000 AND 9102;
DELETE FROM emotion_log WHERE user_id BETWEEN 9000 AND 9102;
DELETE FROM kpi WHERE user_id BETWEEN 9000 AND 9102;
DELETE FROM shift_attendance WHERE user_id BETWEEN 9000 AND 9102;
```

---

## 🐛 Troubleshooting

### Problem: Tests fail với "User not found"
**Solution:** Ensure test users được tạo trong setUpClass
```bash
# Check if users exist
mysql -u root testtest2 -e "SELECT * FROM nhanvien WHERE id BETWEEN 9000 AND 9102"
```

### Problem: "Connection pool timeout"
**Solution:** Tăng POOL_SIZE trong mysql_conn.py hoặc giảm concurrent tests

### Problem: "Cannot check-in outside working hours"
**Solution:** Chạy tests trong giờ làm việc (08:00-20:00) hoặc mock time

### Problem: Tests chạy chậm
**Solution:** 
- Giảm `time.sleep()` delays
- Chạy subset của tests
- Sử dụng pytest với `-n auto` (parallel)

---

## 📈 Metrics Tracked

Tests track các metrics sau:
- ✅ Success rate của mỗi operation
- ⏱️ Response time (implicit)
- 🔢 Concurrent request handling
- 📊 KPI calculation accuracy
- 🛡️ Error handling completeness

---

## 🎓 Learning Outcomes

Sau khi chạy tests, bạn có thể verify:

1. **Thread-Safety**: Multiple IoT devices có thể gửi data đồng thời
2. **Data Integrity**: Không có race conditions hoặc data corruption
3. **Business Logic**: KPI calculation đúng theo rules
4. **Error Handling**: System xử lý errors gracefully
5. **Performance**: System handle được load từ nhiều devices

---

## 🚀 Next Steps

### Extend Tests:
1. Add tests cho shift_attendance absence counting
2. Add tests cho serving_time detection
3. Add load tests (100+ concurrent requests)
4. Add integration tests với real Raspberry Pi

### Integration với CI/CD:
```yaml
# .github/workflows/test.yml
- name: Run IoT Integration Tests
  run: |
    python test_iot_integration.py
    python test_iot_scenarios.py
```

---

## 📚 Related Documentation

- [THREAD_SAFETY_GUIDE.md](THREAD_SAFETY_GUIDE.md) - Thread-safety implementation
- [test_thread_safety.py](test_thread_safety.py) - Thread-safety tests
- [ARCHITECTURE_THREAD_SAFETY.md](ARCHITECTURE_THREAD_SAFETY.md) - Architecture diagrams

---

**Status**: ✅ Comprehensive test coverage for all IoT → Backend scenarios

**Last Updated**: December 20, 2025
