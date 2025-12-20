# Sơ Đồ Luồng Hệ Thống IOT + Backend (Mermaid)

Các sơ đồ dưới đây mô tả chi tiết luồng hoạt động từ Raspberry Pi đến Backend Server cho các API: `/query`, `/check-in`, `/check-out`.

---

## 1. Luồng /query (Nhận Diện Thường Xuyên)

```mermaid
graph TD
    subgraph RPi["🔴 Raspberry Pi (IOT)"]
        A["Bắt đầu vòng lặp<br/>AUTO_SEND_INTERVAL=10s"]
        B["Camera 1: Phát hiện khuôn mặt<br/>Haar Cascade + Motion Detect"]
        C["Crop ảnh khuôn mặt"]
        D["Bản tin phát hiện khách?<br/>Customer Detector"]
        E["isServing = True"]
        F["isServing = False"]
        G["Gửi API POST /query<br/>image + isServing"]
        H["Nhận phản hồi từ server"]
        I["Hiển thị tên, cảm xúc trên UI<br/>Phát âm thanh TTS"]
    end

    subgraph Server["🟢 Backend Server"]
        J["Nhận POST /query<br/>multipart: image, isServing"]
        K["Anti-spoofing check<br/>Ảnh thật hay giả?"]
        L["Face Query Service<br/>Trích xuất embedding"]
        M["Tìm kiếm trong FAISS index"]
        N{Tìm thấy?<br/>score >= 0.5}
        O["Trả về class_id<br/>full_name, age, gender"]
        P["Thêm emotion log<br/>Detect cảm xúc"]
        Q["mark_seen<br/>user_id, is_serving"]
        R["KIỂM TRA EMOTION"]
        S{isServing = True<br/>serving_time = False?}
        T["Lấy shift_attendance"]
        U["TRỪ ĐIỂM KPI<br/>Theo EMOTION_PENALTIES"]
        V["Update KPI emotion_score"]
        W["Trả về JSON<br/>full_name, emotion, class_id"]
        X["404: Không tìm thấy"]
    end

    A --> B
    B --> C
    C --> D
    D -->|Có phát hiện khách| E
    D -->|Không phát hiện| F
    E --> G
    F --> G
    G --> J
    J --> K
    K -->|Ảnh giả| X
    K -->|Ảnh thật| L
    L --> M
    M --> N
    N -->|Có| O
    N -->|Không| X
    O --> P
    P --> Q
    Q --> R
    R --> S
    S -->|Có: Khách mới| T
    T --> U
    U --> V
    S -->|Không: Tiếp tục| W
    V --> W
    W --> H
    X --> H
    H --> I

    style RPi fill:#ffe6e6
    style Server fill:#e6f3ff
```

---

## 2. Luồng /check-in (Chấm Công Bắt Đầu)

```mermaid
graph TD
    subgraph RPi["🔴 Raspberry Pi (IOT)"]
        A["Người dùng bấm nút<br/>CHECK-IN"]
        B["Camera: Phát hiện khuôn mặt<br/>Haar Cascade"]
        C["Crop ảnh, gửi POST<br/>/query/checkin"]
        D["Nhận phản hồi"]
        E{Check-in<br/>thành công?}
        F["Hiển thị ✓ Thành công"]
        G["Phát âm: OK"]
        H["Hiển thị ✗ Lỗi"]
    end

    subgraph Server["🟢 Backend Server"]
        I["Nhận POST /query/checkin<br/>image"]
        J["Anti-spoofing check"]
        K["Face Query: Trích embedding<br/>Tìm kiếm FAISS"]
        L{Tìm thấy<br/>user_id?}
        M["Gọi checkin_service<br/>user_id, date=today"]
        N["Xác định ca làm<br/>day vs night"]
        O["Tính status:<br/>on_time vs late"]
        P["Tìm checklog hôm nay"]
        Q{Checklog<br/>tồn tại?}
        R["Status = pending<br/>hoặc absent?"]
        S["Update: check_in=now<br/>status = on_time/late"]
        T["Tạo mới checklog<br/>check_in=now"]
        U["Kiểm tra KPI<br/>ngày hôm nay"]
        V{KPI<br/>tồn tại?}
        W["Tạo KPI mới<br/>100/100/100"]
        X["Trả về success<br/>checkin response"]
        Y["Error: Không tìm thấy"]
    end

    A --> B
    B --> C
    C --> I
    I --> J
    J --> K
    K --> L
    L -->|Không| Y
    L -->|Có| M
    M --> N
    N --> O
    O --> P
    P --> Q
    Q -->|Không tồn tại| T
    Q -->|Tồn tại| R
    R -->|Đúng pending/absent| S
    S --> U
    T --> U
    U --> V
    V -->|Không| W
    V -->|Có| X
    W --> X
    X --> D
    Y --> D
    D --> E
    E -->|Có| F
    E -->|Không| H
    F --> G

    style RPi fill:#ffe6e6
    style Server fill:#e6f3ff
```

---

## 3. Luồng /check-out (Chấm Công Kết Thúc)

```mermaid
graph TD
    subgraph RPi["🔴 Raspberry Pi (IOT)"]
        A["Người dùng bấm nút<br/>CHECK-OUT"]
        B["Camera: Phát hiện khuôn mặt"]
        C["Crop ảnh, gửi POST<br/>/query/checkout"]
        D["Nhận phản hồi"]
        E{Check-out<br/>thành công?}
        F["Hiển thị ✓ Thành công"]
        G["Phát âm: OK"]
        H["Hiển thị ✗ Lỗi"]
    end

    subgraph Server["🟢 Backend Server"]
        I["Nhận POST /query/checkout<br/>image"]
        J["Anti-spoofing + Face Query"]
        K["Lấy user_id"]
        L["Gọi checkout_service<br/>user_id, date=today"]
        M["Tìm checklog hôm nay"]
        N{Checklog<br/>tồn tại?}
        O["Check_in<br/>tồn tại?"]
        P["Tính total_hours<br/>= (check_out - check_in)<br/>- (absence_count * 10s)"]
        Q["Xác định status<br/>early vs on_time vs late"]
        R["Update checklog<br/>check_out=now<br/>total_hours<br/>status"]
        S["TÍNH LẠI KPI"]
        T["Lấy emotion_log<br/>từ mark_seen đến giờ"]
        U["emotion_score từ DB"]
        V["Tính attendance_score<br/>từ status + total_hours"]
        W["Total_score = 0.3*emotion<br/>+ 0.7*attendance"]
        X["Thêm remark:<br/>Late/Early/Attend issues"]
        Y["update_kpi_service"]
        Z["Trả về success<br/>checkout response"]
        AA["Error: Không tìm thấy"]
    end

    A --> B
    B --> C
    C --> I
    I --> J
    J --> K
    K --> L
    L --> M
    M --> N
    N -->|Không| AA
    N -->|Có| O
    O -->|Không| AA
    O -->|Có| P
    P --> Q
    Q --> R
    R --> S
    S --> T
    T --> U
    U --> V
    V --> W
    W --> X
    X --> Y
    Y --> Z
    Z --> D
    AA --> D
    D --> E
    E -->|Có| F
    E -->|Không| H
    F --> G

    style RPi fill:#ffe6e6
    style Server fill:#e6f3ff
```

---

## 4. Chi Tiết: Serving Time + Emotion Penalty (Bên Trong /query)

```mermaid
graph TD
    A["Nhận emotion từ detect"]
    B{Emotion là<br/>bad emotion?<br/>Anger/Disgust/etc}
    C["Không trừ điểm<br/>Chỉ log"]
    D{isServing<br/>= true?}
    E["Không trong phục vụ<br/>Không trừ"]
    F["Lấy shift_attendance"]
    G{serving_time<br/>= false?}
    H["Lần đầu phục vụ<br/>khách này"]
    I["Lấy EMOTION_PENALTIES"]
    J["Anger: -8<br/>Disgust: -7<br/>Sad: -5<br/>Fear: -6<br/>Surprise: -3"]
    K["TRỪ emotion_score<br/>new_score = old - penalty"]
    L["Set serving_time = true<br/>Không trừ thêm cho khách này"]
    M["Đã phục vụ khách trước<br/>Không trừ lần nữa"]
    N["Ghi log"]
    O["Update KPI"]

    A --> B
    B -->|Không| C
    B -->|Có| D
    D -->|Không| E
    D -->|Có| F
    F --> G
    G -->|True: Tiếp tục| M
    G -->|False: Lần đầu| H
    H --> I
    I --> J
    J --> K
    K --> L
    L --> N
    M --> N
    E --> N
    C --> N
    N --> O

    style A fill:#fff3cd
    style K fill:#f8d7da
    style L fill:#d4edda
```

---

## 5. Tích Hợp Scheduler: Khởi Tạo + Catch-up + Finalize

```mermaid
graph TD
    A["Server khởi động"]
    B["scheduler_loop() bắt đầu"]
    C["Mỗi 10s: Kiểm tra thời gian"]
    D{Thời gian<br/>= SHIFT_DAY_START?<br/>08:00}
    E{Lần đầu<br/>hôm nay?}
    F["init_shift_rows<br/>shift='day'<br/>Tạo shift_attendance<br/>checklog (pending)<br/>KPI (100/100/100)"]
    G["Log: Khởi tạo ca ngày"]
    H{Đang trong<br/>SHIFT_DAY_START<br/>~ SHIFT_DAY_END?<br/>và chưa init?}
    I["Catch-up:<br/>needs_initialization?<br/>Có nhân viên thiếu<br/>shift_attendance?"]
    J["init_shift_rows<br/>bổ sung"]
    K["Log: Catch-up init"]
    L{Thời gian<br/>= SHIFT_DAY_END?<br/>14:00}
    M{Lần đầu<br/>hôm nay?}
    N["finalize_shift_absents"]
    O["Tìm ai không có<br/>checklog"]
    P["Tạo checklog<br/>status='absent'"]
    Q["KPI = 0/0/0"]
    R["Log: Finalize ca ngày"]
    S{Thời gian<br/>= SHIFT_NIGHT_START<br/>14:00?}
    T["Tương tự ca tối"]
    U{Đang trong shift?}
    V["Mỗi 10s:<br/>increment_absences<br/>Ai không thấy > 30s<br/>absence_count++"]

    A --> B
    B --> C
    C --> D
    D -->|Đúng| E
    E -->|Đúng| F
    F --> G
    D -->|Không| H
    H -->|Đúng| I
    I -->|Có| J
    J --> K
    H -->|Không| L
    L -->|Đúng| M
    M -->|Đúng| N
    N --> O
    O --> P
    P --> Q
    Q --> R
    L -->|Không| S
    S -->|Đúng| T
    S -->|Không| U
    U -->|Đúng| V
    V --> C

    style F fill:#d4edda
    style J fill:#d4edda
    style N fill:#f8d7da
    style V fill:#fff3cd
```

---

## 6. Quy Trình Thêm Nhân Viên (Hoàn Tất Flow)

```mermaid
graph TD
    A["API POST /add-users<br/>full_name, shift, etc"]
    B["add_users_service"]
    C["Thêm vào DB nhanvien"]
    D["Lấy user_id mới"]
    E{Thời gian hiện tại<br/>trong shift<br/>khớp shift nhân viên?}
    F["KHỞI TẠO NGAY LẬP TỨC"]
    G["upsert_shift_attendance<br/>date=today, ca hiện tại"]
    H["Tạo checklog pending<br/>date=today"]
    I["Tạo KPI 100/100/100<br/>date=today"]
    J["Log: Init ngay<br/>user_id=..., ca=..."]
    K["KHÔNG INIT<br/>Sẽ init vào ca kế tiếp"]
    L["Log: Thêm nhân viên<br/>ngoài giờ, chờ ca mới"]
    M["Trả về success<br/>class_id=user_id"]

    A --> B
    B --> C
    C --> D
    D --> E
    E -->|Có| F
    F --> G
    G --> H
    H --> I
    I --> J
    E -->|Không| K
    J --> M
    K --> L
    L --> M

    style F fill:#d4edda
    style G fill:#d4edda
    style H fill:#d4edda
    style I fill:#d4edda
```

---

## 7. Mark_Seen: Serving State Machine

```mermaid
graph TD
    A["mark_seen(user_id,<br/>is_serving)"]
    B{is_serving<br/>= true?}
    C["Người dùng đang<br/>phục vụ khách"]
    D["Set serving_time<br/>= true"]
    E["Set no_serving_count<br/>= 0"]
    F["Update shift_attendance"]
    G["Log: Phục vụ khách"]
    H["Người dùng không<br/>phục vụ"]
    I["Lấy shift_attendance"]
    J["Tăng no_serving_count++"]
    K{no_serving_count<br/>>= 2?}
    L["Set serving_time<br/>= false"]
    M["Reset<br/>no_serving_count = 0"]
    N["Lần đầu gặp"]
    O["Giữ serving_time<br/>tùy trước đó"]
    P["Update shift_attendance"]
    Q["Log: Ngừng phục vụ<br/>sau 2 lần"]

    A --> B
    B -->|Đúng| C
    C --> D
    D --> E
    E --> F
    F --> G
    B -->|Sai| H
    H --> I
    I --> J
    J --> K
    K -->|Đúng| L
    L --> M
    M --> P
    K -->|Sai| O
    O --> P
    P --> Q

    style D fill:#d4edda
    style L fill:#f8d7da
    style M fill:#f8d7da
```

---

## Ghi Chú Sử Dụng Draw.io

1. **Sao chép mã Mermaid**: Chọn toàn bộ nội dung mã trong mỗi khối `` ```mermaid ... ``` ``
2. **Mở Draw.io**: https://app.diagrams.net/
3. **Chèn Mermaid**: 
   - Chọn menu **File** → **New** → **Blank Diagram**
   - Hoặc kéo thả mã vào canvas
   - Hoặc từ menu: **Arrange** → **Insert** → **SVG/Mermaid**
4. **Chỉnh sửa**: Draw.io sẽ render sơ đồ, bạn có thể thay đổi màu, vị trí, nhãn.
5. **Xuất**: **File** → **Export as** → PNG/SVG/PDF

---

## Huyền Thoại Màu Sắc

- 🔴 **Raspberry Pi (RPi)** = Màu hồng (`fill:#ffe6e6`)
- 🟢 **Backend Server** = Màu xanh (`fill:#e6f3ff`)
- **Khởi tạo/Success** = Màu xanh nhạt (`fill:#d4edda`)
- **Trừ điểm/Lỗi** = Màu đỏ nhạt (`fill:#f8d7da`)
- **Hành động liên tục** = Màu vàng (`fill:#fff3cd`)
