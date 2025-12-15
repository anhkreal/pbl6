# Hướng dẫn cài đặt & chạy Face Recognition API

## 1. Tạo môi trường ảo Python
Khuyên dùng Python 3.10 để đảm bảo tương thích với các thư viện AI.

```bash
python -m venv venv310
```

Kích hoạt môi trường ảo:
- **Windows:**
  ```bash
  venv310\Scripts\activate
  ```
- **Linux/Mac:**
  ```bash
  source venv310/bin/activate
  ```

## 2. Cài đặt các thư viện cần thiết

```bash
pip install -r requirements.txt
```

Nếu gặp lỗi với tensorflow, hãy cài riêng:
```bash
pip install tensorflow==2.15.0
```

## 3. Chạy ứng dụng FastAPI

### Cách 1: Chạy trực tiếp bằng Python
Nếu file `app.py` có đoạn sau ở cuối:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
Thì chỉ cần chạy:
```bash
python app.py
```

### Cách 2: Chạy bằng Uvicorn (khuyên dùng)
```bash
 uvicorn app:app --host 0.0.0.0 --port 8000 --ssl-keyfile ./key.pem --ssl-certfile ./cert.pem
```

## 4. Truy cập API
- Mở trình duyệt và truy cập: [http://localhost:8000/docs](http://localhost:8000/docs) để xem Swagger UI.
- Hoặc [http://localhost:8000/redoc](http://localhost:8000/redoc) để xem tài liệu chi tiết.

## 5. Một số lưu ý
- Nếu thiếu thư viện, hãy cài bằng pip: `pip install <tên_thư_viện>`
- Nếu gặp lỗi về numpy trên Windows, có thể bỏ qua nếu không crash.
- Đảm bảo đã cài đặt MySQL và cấu hình kết nối đúng nếu dùng database.

---
**Mọi thắc mắc hoặc lỗi, vui lòng liên hệ hỗ trợ hoặc kiểm tra lại các bước trên.**
