# 🏗️ Face Recognition System - Architecture

**Version:** 2.0.0 - MySQL Authentication System  
**Last Updated:** December 2025  
**Language:** Python 3.10+

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Directory Structure](#directory-structure)

---

## 🎯 System Overview

Hệ thống **Face Recognition API** là một ứng dụng nhận diện khuôn mặt tiên tiến kết hợp các công nghệ:

- **ArcFace**: Trích xuất đặc trưng khuôn mặt (embeddings)
- **FAISS**: Tìm kiếm vector nhanh chóng (similarity search)
- **Custom ResNeXt50-32x4d**: Nhận diện cảm xúc (emotion recognition)
- **MySQL**: Lưu trữ dữ liệu người dùng và logs
- **FastAPI**: Backend API server

### 🎓 Chức Năng Chính

| Chức Năng | Mô Tả |
|-----------|-------|
| **Face Recognition** | Nhận diện khuôn mặt từ ảnh, tìm người giống nhất |
| **Emotion Detection** | Nhận diện 8 loại cảm xúc: Neutral, Happy, Sad, Surprise, Fear, Disgust, Anger, Contempt |
| **Attendance Tracking** | Ghi nhận check-in/check-out, tính KPI attendance score |
| **Emotion Logging** | Ghi lại cảm xúc của nhân viên theo thời gian và ca làm việc |
| **User Management** | CRUD nhân viên, tài khoản, avatar, thông tin cá nhân |
| **Authentication** | MySQL-based token authentication với session management |
| **Anti-Spoofing** | Kiểm tra ảnh có phải được chụp từ thiết bị thực không |
| **Vector Search** | Quản lý embeddings, tìm kiếm vector tương tự |

---

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
│                       (app.py, port 8000)                        │
└────────────┬────────────────────────────────────────────────────┘
             │
    ┌────────┴────────────┬────────────────┬─────────────────────┐
    │                     │                │                     │
┌───▼────┐    ┌──────────▼──────┐    ┌───▼────┐    ┌──────────▼──┐
│  API   │    │   Service       │    │  Auth  │    │  DB         │
│ Layer  │────│   Layer         │    │ Layer  │    │ Layer       │
└────────┘    └────────┬────────┘    └────────┘    └─────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐  ┌────▼────┐  ┌────▼─────┐
    │ Feature │  │  FAISS  │  │ Emotion  │
    │Extractor│  │ Manager │  │  Model   │
    │(ArcFace)│  │         │  │(ResNeXt50)
    └────┬────┘  └────┬────┘  └──────────┘
         │            │
    ┌────▼────────────▼────┐     ┌──────────┐
    │   shared_instances   │     │  MySQL   │
    │  (Singleton Pattern) │────►│ Database │
    └──────────────────────┘     └──────────┘
         │
    ┌────▼─────────┐
    │ Model Files  │
    │ .pth weights │
    └──────────────┘

┌─────────────────────────────────────────────────────┐
│           Index Storage (FAISS)                     │
│  - faiss_db_r18.index (vector embeddings)           │
│  - faiss_db_r18_meta.npz (metadata)                 │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. **API Layer** (`api/`)
Xử lý HTTP requests/responses. Mỗi file tương ứng với một tính năng:

| Module | Chức Năng |
|--------|----------|
| `face_query.py` | Tìm kiếm khuôn mặt (top-1) |
| `face_query_top5.py` | Tìm kiếm khuôn mặt (top-5) |
| `add_embedding.py` | Thêm embeddings cho nhân viên |
| `emotion.py` | Truy vấn emotion logs |
| `add_emotion.py` | Ghi lại cảm xúc |
| `checkin.py` / `checkout.py` | Ghi nhận attendance |
| `users.py` | Quản lý thông tin nhân viên |
| `taikhoan_api.py` | Quản lý tài khoản MySQL |
| `kpi.py` | Tính toán KPI scores |

### 2. **Service Layer** (`service/`)
Logic xử lý chính của hệ thống:

| Service | Mục Đích |
|---------|---------|
| `face_query_service.py` | Xử lý tìm kiếm khuôn mặt |
| `add_embedding_service.py` | Thêm embeddings vào FAISS |
| `emonet_service.py` | Nhận diện cảm xúc (ResNeXt50-32x4d) |
| `add_emotion_service.py` | Ghi emotion logs |
| `kpi_service.py` | Tính toán KPI |
| `checkin_service.py` / `checkout_service.py` | Ghi attendance |
| `shift_attendance_service.py` | Tính toán shift attendance |
| `shared_instances.py` | **Singleton instances** (critical!) |

### 3. **Database Layer** (`db/`)
Giao tiếp với MySQL:

| Module | Chức Năng |
|--------|----------|
| `models.py` | Data classes (Nguoi, TaiKhoan, etc.) |
| `mysql_conn.py` | MySQL connection management |
| `nguoi_repository.py` | CRUD người dùng |
| `taikhoan_repository.py` | CRUD tài khoản |

### 4. **Authentication Layer** (`auth/`)
Bảo mật API endpoints:

| Module | Chức Năng |
|--------|----------|
| `mysql_auth.py` | MySQL-based token authentication |
| `mysql_auth_api.py` | Login/logout endpoints |

### 5. **AI Models** (`model/`)
Deep learning models:

| Model | Chức Năng | Kích Thước |
|-------|----------|----------|
| `arcface_model.py` | Feature extraction (ArcFace r100) | 512-dim |
| `emonet_service.py` | Emotion recognition (ResNeXt50-32x4d) | 8 classes |

### 6. **Vector Search** (`index/`)
FAISS vector database:

| File | Mô Tả |
|------|--------|
| `faiss.py` | FaissIndexManager - quản lý embeddings |
| `faiss_db_r18.index` | FAISS index file |
| `faiss_db_r18_meta.npz` | Metadata (image_ids, paths, class_ids) |

---

## 🔄 Data Flow

### **Flow 1: Face Recognition (Top-1)**

```
User Upload Image
       │
       ▼
┌─────────────────────────────────────┐
│ face_query_service.query_face_service │
└────────┬────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ 1. ArcFace Extract Features (embeddings)│
    │    Input: RGB image, Output: 512-dim   │
    └────┬───────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ 2. Emotion Recognition                 │
    │    ResNeXt50-32x4d → 8 emotion classes │
    └────┬───────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ 3. FAISS Query (similarity search)    │
    │    Find Top-1 matching person         │
    └────┬───────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ 4. MySQL Query                        │
    │    Get person details (name, role)   │
    └────┬───────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │ 5. Emotion Logging (if negative emotion)│
    │    Log to emotion table                 │
    └────┬───────────────────────────────────┘
         │
         ▼
   Return JSON Response
   {
     "image_id": 1,
     "class_id": 123,
     "score": 0.95,
     "emotion": {"emotion": "Happy", "prob": 0.92},
     "nguoi": { "id": 123, "full_name": "Nguyễn Văn A", ...}
   }
```

### **Flow 2: Add User Embedding**

```
User Upload Image + Class ID
       │
       ▼
┌──────────────────────────────────────────┐
│ add_embedding_service.add_embedding_service │
└──────┬──────────────────────────────────┘
       │
   ┌───▼─────────────────────────┐
   │ 1. Extract ArcFace features │
   └───┬─────────────────────────┘
       │
   ┌───▼────────────────────────────────┐
   │ 2. Add to FAISS Index              │
   │    - Normalize embedding            │
   │    - Add to index                   │
   │    - Save metadata                  │
   └───┬────────────────────────────────┘
       │
   ┌───▼────────────────────────────────┐
   │ 3. Save to MySQL                   │
   │    - Store embedding_vector        │
   │    - Link to user_id               │
   └───┬────────────────────────────────┘
       │
       ▼
   Return Success JSON
```

### **Flow 3: Attendance Check-In/Out**

```
User Face Scan → Recognized
       │
       ▼
┌────────────────────────────┐
│ checkin_service            │
└────┬───────────────────────┘
     │
 ┌───▼──────────────────────────────┐
 │ 1. Get current shift timing      │
 │    Based on user's assigned shift│
 └───┬──────────────────────────────┘
     │
 ┌───▼──────────────────────────────┐
 │ 2. Check if in working hours     │
 │    Compare with shift schedule   │
 └───┬──────────────────────────────┘
     │
 ┌───▼──────────────────────────────┐
 │ 3. Create Attendance Log         │
 │    - timestamp                   │
 │    - check_in_time               │
 │    - status (present/absent)     │
 └───┬──────────────────────────────┘
     │
 ┌───▼──────────────────────────────┐
 │ 4. Store to MySQL (checklog)     │
 └───┬──────────────────────────────┘
     │
     ▼
 Return JSON with timestamp
```

---

## 🛠️ Technology Stack

### **Backend Framework**
- **FastAPI** (v0.124.0+): Modern async web framework
- **Uvicorn**: ASGI server
- **Python** 3.10+

### **Deep Learning**
- **PyTorch** (v2.9.0+): Neural network framework
- **TorchVision** (v0.24.0+): CV models
- **OpenCV** (v4.8.0+): Image processing
- **Numpy** (v2.2.0+): Numerical computing

### **Vector Search**
- **FAISS** (v1.13.1+): Fast similarity search
- Uses **IndexFlatIP** (Inner Product) for cosine similarity

### **Database**
- **MySQL**: User data, embeddings, logs
- **PyMySQL**: Python MySQL driver

### **Utilities**
- **Pydantic** (v2.6.0+): Data validation
- **Pandas** (v2.2.0+): Data processing
- **APScheduler**: Background job scheduling (for shift calculations)

---

## 📁 Directory Structure

```
face-recognition/
├── app.py                          # FastAPI application entry point
├── config.py                       # Configuration (model paths, FAISS paths)
├── requirements.txt                # Python dependencies
│
├── api/                            # HTTP API Layer (38 endpoints)
│   ├── face_query.py              # Query top-1 face
│   ├── face_query_top5.py         # Query top-5 faces
│   ├── add_embedding.py           # Add embedding
│   ├── emotion.py                 # Query emotion logs
│   ├── add_emotion.py             # Add emotion log
│   ├── checkin.py                 # Check-in
│   ├── checkout.py                # Check-out
│   ├── users.py                   # User CRUD
│   ├── taikhoan_api.py            # Account CRUD
│   ├── kpi.py                     # KPI queries
│   └── ... (35 more endpoints)
│
├── service/                        # Business Logic (44 services)
│   ├── face_query_service.py      # Face recognition logic
│   ├── face_query_top5_service.py # Top-5 logic
│   ├── add_embedding_service.py   # Embedding addition
│   ├── emonet_service.py          # **Emotion detection (ResNeXt50-32x4d)**
│   ├── add_emotion_service.py     # Emotion logging
│   ├── checkin_service.py         # Check-in logic
│   ├── checkout_service.py        # Check-out logic
│   ├── kpi_service.py             # KPI calculation
│   ├── kpi_calculator.py          # KPI computation
│   ├── shift_attendance_service.py # Shift attendance
│   ├── shared_instances.py        # **Singleton Pattern (CRITICAL)**
│   └── ... (33 more services)
│
├── db/                            # Database Layer
│   ├── models.py                  # Data classes (Nguoi, TaiKhoan, etc.)
│   ├── mysql_conn.py              # MySQL connection
│   ├── connection_helper.py       # Connection helpers
│   ├── nguoi_repository.py        # User CRUD
│   ├── taikhoan_repository.py     # Account CRUD
│   └── init_db.py                 # DB initialization
│
├── auth/                          # Authentication
│   ├── mysql_auth.py              # Token-based auth
│   └── mysql_auth_api.py          # Auth endpoints
│
├── model/                         # AI Models
│   ├── arcface_model.py           # ArcFace feature extractor
│   ├── glint360k_cosface_r100_fp16_0.1.pth  # Model weights (r100)
│   ├── ModelAge.pth               # Age model
│   ├── ModelGender.pth            # Gender model
│   └── emonet.pth                 # **Custom Emotion Model (ResNeXt50-32x4d)**
│
├── index/                         # FAISS Vector Database
│   ├── faiss.py                   # FaissIndexManager
│   ├── faiss_db_r18.index         # Vector index
│   └── faiss_db_r18_meta.npz      # Metadata
│
├── Depend/
│   └── depend.py
│
├── logs/                          # Application logs
│
├── migrations/
│   └── add_serving_time_columns.sql
│
├── scripts/
│   ├── seed_mock_data.py
│   ├── update_data_fix.py
│   └── _test_kpi_*.py
│
└── insightface/                   # External: ArcFace library
    ├── recognition/
    ├── detection/
    └── ...
```

---

## 🔐 Security Architecture

### **Authentication Flow**

```
┌──────────────┐
│ User         │
└────┬─────────┘
     │
     │ POST /auth/login
     │ { username, password }
     ▼
┌──────────────────────────────────┐
│ mysql_auth_api.login             │
└────┬──────────────────────────────┘
     │
 ┌───▼─────────────────────────────┐
 │ Verify username/password from   │
 │ MySQL taikhoan table            │
 └───┬─────────────────────────────┘
     │
 ┌───▼─────────────────────────────┐
 │ Create session token            │
 │ (secrets.token_urlsafe(32))     │
 └───┬─────────────────────────────┘
     │
     │ Return Session Token
     ▼
┌──────────────┐
│ Client       │
│ Stores token │
└──────────────┘

┌─────────────────────────────────────────┐
│ Protected API Call                      │
│ GET /query                              │
│ Header: Authorization: Bearer <token>   │
└────┬────────────────────────────────────┘
     │
 ┌───▼──────────────────────────────────┐
 │ get_current_user_mysql() Dependency  │
 │ - Check Authorization header         │
 │ - Lookup in active_sessions dict     │
 │ - Verify token not expired (24h)     │
 └───┬──────────────────────────────────┘
     │
 ✓ Token Valid → Process Request
 ✗ Token Invalid → 401 Unauthorized
```

### **API Security Levels**

| Level | Description | Examples |
|-------|-------------|----------|
| **Public** | No authentication required | `/health`, `/query` (face search) |
| **Protected** | Require MySQL login | `/add-embedding`, `/edit-user`, `/delete-class` |
| **Admin** | Admin role only | Future: admin endpoints |

---

## 💡 Key Design Patterns

### 1. **Singleton Pattern** (Critical!)
```python
# shared_instances.py
class SharedInstances:
    _instance = None
    _lock = threading.Lock()
    
    # Ensures only ONE instance of:
    # - ArcFaceFeatureExtractor
    # - FaissIndexManager
    # - Threading Lock for FAISS
```
**Why:** Prevent memory leaks and duplicate model loading

### 2. **Repository Pattern**
```python
# db/nguoi_repository.py
class NguoiRepository:
    def get_by_id(self, id: int) → Nguoi
    def add_embedding_vector(...)
    def add_emotion_log(...)
```

### 3. **Service Layer Pattern**
```python
# Each API endpoint calls corresponding service
# Separates business logic from HTTP handling
api/face_query.py → service/face_query_service.py
```

### 4. **Thread-Safe FAISS Access**
```python
# Thread lock prevents concurrent FAISS modifications
faiss_lock = shared.get_faiss_lock()
with faiss_lock:
    results = faiss_manager.query(emb, topk=5)
```

---

## ⚡ Performance Optimization

1. **Singleton Pattern**: Avoid reloading models on each request
2. **FAISS IndexFlatIP**: O(n) similarity search with fast inner product
3. **Async FastAPI**: Handle concurrent requests efficiently
4. **Connection Pooling**: MySQL connection reuse
5. **Embedding Cache**: Store embeddings in FAISS for fast retrieval

---

## 🚀 Next Steps

1. Prepare `model/emonet.pth` - custom ResNeXt50-32x4d weights
2. Initialize MySQL database with schema
3. Seed sample data using `scripts/seed_mock_data.py`
4. Start server: `python -m uvicorn app:app --reload`
5. Access API docs: `http://localhost:8000/docs`

---

**Last Updated:** December 20, 2025  
**Maintainer:** Face Recognition Team
