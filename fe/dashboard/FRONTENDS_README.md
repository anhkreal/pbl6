# Frontends Overview

## Edge Stream (RPI)
Location: `edge_stream/`
Runs a Flask server providing realtime MJPEG at `/video` plus stats at `/stats`.
Components:
- `app.py` main Flask app.
- `camera.py` placeholder capture + overlay (replace with real detection, embedding, emotion inference).
- `identity_client.py` calls server `/query` for identity.
- `emotion_infer.py` stub random emotion classification.
- `log_batcher.py` batches negative emotion logs to POST `/emotions`.
- `templates/index.html`, `static/js/client.js` UI with image stream.

Start (PowerShell):
```
cd edge_stream
pip install -r requirements.txt
$env:SERVER_URL="http://<server-host>:8000"; python app.py
```

## Management Dashboard (Laptop)
Location: `dashboard/`
React + TypeScript (Vite) role-based routing for admin/staff.
Pages:
- Admin: Dashboard, EmotionLog, Attendance, KPIReport, Employees, EmployeeDetail, Profile
- Staff: Dashboard, EmotionLog, Attendance, KPIReport, Profile, ImageUpdate, Contact

Setup (PowerShell):
```
cd dashboard
npm install
npm run dev
```

Environment variables:
Create a file `.env.local` in `dashboard/` with:
```
VITE_API_URL=http://localhost:8000
```
Adjust host to your server backend. Access via `import.meta.env.VITE_API_URL`.

**Mock Credentials (for testing without backend):**

| Role  | Username | Password |
|-------|----------|----------|
| Admin | admin    | admin123 |
| Staff | staff    | staff123 |

Mock authentication is configured in `src/api/auth.ts`. Replace with real API calls when backend is ready.

Replace dummy auth & data by implementing API calls in `src/api/*` (to be added). Limit table queries to 30 rows with server `?limit=30` parameter.

## API Integration
- Đã thay mock bằng gọi API thực: auth, emotions, attendance, KPI, employees, PIN.
- ENV: VITE_API_URL trỏ backend Django/FastAPI (ví dụ http://localhost:8000).
- Token lưu localStorage: authToken.
- Pagination emotion logs: limit=30.
- PIN verify trước khi gọi shift/reset/delete.

## Admin Pages Implemented (mock)
- Dashboard: thống kê nhân sự, camera, cảm xúc tích cực
- EmotionLog: lọc thời gian + tên, tối đa 30 log tiêu cực, xóa với PIN
- Check in/out: lọc theo ngày + tên, chỉnh sửa trạng thái với PIN
- KPI Report: xem theo ngày/tháng, lọc tên, xem chi tiết nhân viên
- Quản lí nhân viên: tìm kiếm, lọc trạng thái, thêm mới (PIN), đổi ca, reset, xóa (PIN)
- Employee Detail: thông tin + KPI theo ngày trong tháng
- Profile: đổi thông tin, mật khẩu, PIN

## Staff Pages Implemented (mock)
- Dashboard cá nhân: KPI hôm nay, giờ làm, biểu đồ cảm xúc
- EmotionLog: lọc khoảng thời gian (<=30 dòng)
- Check in/out: xem theo ngày
- KPI Report: xem theo ngày/tháng
- Profile: đổi thông tin, mật khẩu
- Image Update: placeholder
- Contact: thông tin admin

PIN mock: 123456 (thay bằng API /admin/verify-pin sau).

## Layout Update
- Top bar (logo/title left, user name + ⋮ dropdown right).
- Dropdown contains: “Thông tin cá nhân”, “Đăng xuất”.

Layout fix: Added UserMenu (username + ⋮ with “Thông tin cá nhân”, “Đăng xuất”) and top bar in AdminLayout & StaffLayout.

Layout hotfix applied: added main.tsx router, UserMenu component, AdminLayout, StaffLayout to resolve blank screen render errors.

## Routing Fix
Thêm file src/main.tsx với đầy đủ Routes (admin + staff). Kiểm tra index.html có <div id="root"></div>. Nếu 404 xuất hiện là do route chưa được khai báo hoặc sai đường dẫn.

## Next Steps
- Implement real detection & emotion models on RPI.
- Add websocket overlay meta channel for lower latency.
- Flesh out API modules and PIN verification modal.
- Integrate KPI formula shared with backend.
 - Add layout shell (already added) and refine UI styling.
