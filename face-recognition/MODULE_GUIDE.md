# 📚 Face Recognition System - Module Guide

**Version:** 2.0.0  
**Last Updated:** December 2025

---

## 📋 Table of Contents

1. [API Layer Modules](#api-layer-modules)
2. [Service Layer Modules](#service-layer-modules)
3. [Database Layer Modules](#database-layer-modules)
4. [Authentication Layer](#authentication-layer)
5. [AI Model Modules](#ai-model-modules)
6. [Index & Vector Search](#index--vector-search)

---

## 🌐 API Layer Modules (`api/`)

### Overview
API layer xử lý HTTP requests/responses. Mỗi file tương ứng với một hoặc nhiều endpoints.

---

### **1. Face Recognition APIs**

#### `face_query.py` - Single Face Recognition
```python
@router.post('/query')
async def query_face(file: UploadFile) → JSONResponse
```

**Purpose:** Tìm kiếm người giống nhất từ database (Top-1 match)

**Request:**
- Method: `POST`
- Endpoint: `/query`
- Body: Form data với `file` (image)

**Response:**
```json
{
  "image_id": 1,
  "image_path": "path/to/image.jpg",
  "class_id": "123",
  "score": 0.95,
  "emotion": {
    "emotion": "Happy",
    "prob": 0.92
  },
  "nguoi": {
    "id": 123,
    "username": "user123",
    "full_name": "Nguyễn Văn A",
    "role": "staff",
    "shift": "day"
  }
}
```

**Workflow:**
1. Upload ảnh
2. Extract ArcFace features (512-dim embedding)
3. Nhận diện cảm xúc (ResNeXt50-32x4d)
4. FAISS query (top-1)
5. MySQL lookup person details
6. Log emotion nếu negative

---

#### `face_query_top5.py` - Top-5 Face Recognition
```python
@track_operation("face_query_top5")
async def query_face_top5(file: UploadFile) → JSONResponse
```

**Purpose:** Tìm 5 người giống nhất từ database (Top-5 matches)

**Response:**
```json
{
  "results": [
    { "image_id": 1, "class_id": 123, "score": 0.95, "nguoi": {...} },
    { "image_id": 2, "class_id": 124, "score": 0.88, "nguoi": {...} },
    ...
  ],
  "total_time": 0.234
}
```

**Difference vs face_query:**
- Returns multiple matches (top-5)
- Includes performance tracking

---

### **2. Embedding Management APIs**

#### `add_embedding.py` - Add User Embedding (Traditional)
```python
@router.post('/add-embedding')
def add_embedding(
    class_id: int,
    image: UploadFile,
    image_path: str = None,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Purpose:** Thêm embedding cho một nhân viên (1 ảnh)

**Features:**
- Requires authentication (MySQL login)
- Extract ArcFace features
- Add to FAISS index
- Store metadata

**Request:**
```
POST /add-embedding
- class_id: 123 (user_id)
- image: <file>
- image_path: "path/to/image.jpg" (optional)
- Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Embedding added successfully",
  "image_id": 1001
}
```

---

#### `add_embedding_simple.py` - Add User Embedding (Batch)
```python
@router.post('/add-embedding-simple')
def add_embedding_simple(
    class_id: int,
    images: List[UploadFile],
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Purpose:** Thêm embeddings cho một nhân viên (nhiều ảnh)

**Features:**
- Batch processing
- More efficient for multiple images

---

### **3. Emotion & Sentiment APIs**

#### `emotion.py` - Query Emotion Logs
```python
@emotion_router.get('/emotion')
def query_emotion(
    user_id: int = None,
    emotion_type: str = None,
    start_ts: str = None,
    end_ts: str = None,
    limit: int = 100,
    offset: int = 0,
    include_image_base64: bool = False,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Purpose:** Lọc emotion logs với nhiều tiêu chí

**Request:**
```
GET /emotion?user_id=123&emotion_type=Sad&limit=20&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "records": [
    {
      "id": 1,
      "user_id": 123,
      "emotion_type": "Sad",
      "confidence": 0.92,
      "timestamp": "2025-12-20T10:30:00Z",
      "camera_id": 1,
      "image_thumb": "data:image/jpeg;base64,..."
    }
  ],
  "total": 5
}
```

**Filter Options:**
- `user_id`: Lọc theo nhân viên
- `emotion_type`: Lọc theo loại cảm xúc
- `start_ts`, `end_ts`: Lọc theo thời gian
- `limit`, `offset`: Phân trang

---

#### `add_emotion.py` - Log Emotion
```python
@add_emotion_router.post('/add-emotion')
def add_emotion(
    user_id: int = None,
    camera_id: int = None,
    emotion_type: str = Form(...),
    confidence: float = Form(...),
    image: UploadFile = None,
    note: str = None
) → JSONResponse
```

**Purpose:** Ghi nhận cảm xúc của nhân viên

**Features:**
- Optional user_id, camera_id
- Store emotion type & confidence
- Save image thumbnail
- Check if in working shift

**Request:**
```
POST /add-emotion
- user_id: 123
- camera_id: 1
- emotion_type: "Sad"
- confidence: 0.92
- image: <file>
- note: "Reason for emotion"
```

---

#### `delete_emotion.py` - Delete Emotion Log
```python
@router.post('/delete-emotion/{emotion_id}')
def delete_emotion(
    emotion_id: int,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

---

### **4. Attendance APIs**

#### `checkin.py` - Check-In
```python
@router.post('/checkin')
async def checkin(file: UploadFile = File(...)) → JSONResponse
```

**Purpose:** Ghi nhận check-in (vào làm việc)

**Workflow:**
1. Face recognition
2. Get person details
3. Check current shift
4. Verify within working hours
5. Create attendance log

**Response:**
```json
{
  "success": true,
  "message": "Check-in successful",
  "timestamp": "2025-12-20T08:00:00Z",
  "person": {
    "id": 123,
    "full_name": "Nguyễn Văn A",
    "shift": "day"
  }
}
```

---

#### `checkout.py` - Check-Out
```python
@router.post('/checkout')
async def checkout(file: UploadFile = File(...)) → JSONResponse
```

**Purpose:** Ghi nhận check-out (kết thúc ca làm việc)

---

### **5. User Management APIs**

#### `users.py` - User CRUD
```python
@users_router.get('/users')
def list_users(
    role: str = None,
    shift: str = None,
    limit: int = 100,
    offset: int = 0,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse

@users_router.get('/users/{user_id}')
def get_user(user_id: int, current_user: str = Depends(...)) → JSONResponse

@users_router.post('/users')
def create_user(user_data: dict, current_user: str = Depends(...)) → JSONResponse

@users_router.put('/users/{user_id}')
def update_user(user_id: int, updates: dict, current_user: str = Depends(...)) → JSONResponse

@users_router.delete('/users/{user_id}')
def delete_user(user_id: int, current_user: str = Depends(...)) → JSONResponse
```

**User Fields:**
- `id`: User ID
- `username`: Login username
- `pin`: PIN code
- `full_name`: Full name
- `age`: Age
- `gender`: Gender
- `phone`: Phone number
- `address`: Address
- `role`: Role (staff, manager, admin)
- `shift`: Shift (day, night)
- `status`: Status (active, inactive)
- `avatar_url`: Avatar BLOB

---

#### `add_users.py` - Batch Add Users
```python
@add_users_router.post('/add-users')
def add_users(
    file: UploadFile = File(...),  # Excel file
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Purpose:** Import nhân viên từ file Excel

---

#### `edit_users.py` - Update User
```python
@edit_users_router.put('/edit-user/{user_id}')
def edit_user(
    user_id: int,
    updates: dict = Body(...),
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

---

#### `update_avatar.py` - Upload Avatar
```python
@update_avatar_router.post('/update-avatar/{user_id}')
def update_avatar(
    user_id: int,
    avatar: UploadFile = File(...),
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

---

### **6. Account Management APIs**

#### `taikhoan_api.py` - Account CRUD
```python
# Manage MySQL account (username/password)
@taikhoan_router.get('/taikhoan')
@taikhoan_router.post('/taikhoan')
@taikhoan_router.put('/taikhoan/{username}')
@taikhoan_router.delete('/taikhoan/{username}')
```

---

#### `change_password.py` - Change Password
```python
@router.post('/change-password')
def change_password(
    old_password: str,
    new_password: str,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

---

#### `change_pin.py` - Change PIN
```python
@router.post('/change-pin')
def change_pin(
    user_id: int,
    old_pin: str,
    new_pin: str,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

---

#### `reset_password.py` - Reset Password
```python
@router.post('/reset-password/{user_id}')
def reset_password(
    user_id: int,
    new_password: str,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

---

### **7. KPI & Attendance Analytics**

#### `kpi.py` - KPI Scores
```python
@kpi_router.get('/kpi')
def get_kpi(
    user_id: int = None,
    start_date: str = None,
    end_date: str = None,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse

@kpi_router.get('/kpi/user/{user_id}')
def get_user_kpi(
    user_id: int,
    period: str = "month",  # day, week, month
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**KPI Components:**
- Attendance Score (check-in/out regularity)
- Emotion Score (positive emotions)
- Total Score (weighted average)

**Response:**
```json
{
  "user_id": 123,
  "full_name": "Nguyễn Văn A",
  "date_or_month": "2025-12-20",
  "attendance_score": 95.0,
  "emotion_score": 78.5,
  "total_score": 86.75
}
```

---

#### `checklog.py` - Attendance Logs
```python
@checklog_router.get('/checklog')
def get_checklog(
    user_id: int = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse

@checklog_router.get('/checklog/{checklog_id}')
def get_checklog_detail(
    checklog_id: int,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Attendance Log Fields:**
- `id`: Log ID
- `user_id`: User ID
- `check_in_time`: Check-in time
- `check_out_time`: Check-out time
- `date`: Date
- `status`: Present/Absent
- `note`: Notes

---

### **8. Vector & Index Management**

#### `vector_info.py` - Vector Database Info
```python
@router.get('/vector-info')
def get_vector_info() → JSONResponse
```

**Returns:**
```json
{
  "total_embeddings": 5000,
  "index_size_mb": 20.5,
  "embedding_dimension": 512,
  "index_type": "IndexFlatIP"
}
```

---

#### `index_status.py` - Index Status
```python
@status_router.get('/index-status')
def get_index_status(
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Returns:** FAISS index status and statistics

---

#### `reset_index.py` - Reset Index
```python
@reset_router.post('/reset-index')
def reset_index(
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Warning:** Xóa toàn bộ embeddings!

---

### **9. Search & Query APIs**

#### `search_embeddings.py` - Search Embeddings
```python
@embedding_search_router.get('/search-embeddings')
def search_embeddings(
    class_id: int = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "image_id_asc",
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

**Purpose:** Lọc embeddings theo class_id

**Sort Options:**
- `image_id_asc`, `image_id_desc`
- `class_id_asc`, `class_id_desc`
- `image_path_asc`, `image_path_desc`

---

#### `faces.py` - List Faces
```python
@faces_router.get('/faces')
def list_faces(
    class_id: int = None,
    limit: int = 100,
    offset: int = 0,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse

@faces_router.post('/faces')
def upload_faces(
    class_id: int,
    files: List[UploadFile],
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
```

---

### **10. Utility APIs**

#### `health.py` - Health Check
```python
@router.get('/health')
def health_check() → JSONResponse
```

**Public endpoint** (no auth required)

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-12-20T10:30:00Z"
}
```

---

#### `predict.py` - Predict
```python
@predict_router.post('/predict')
async def predict(file: UploadFile = File(...)) → JSONResponse
```

---

---

## 🔧 Service Layer Modules (`service/`)

### Overview
Service layer chứa logic xử lý chính, được gọi từ API layer.

---

### **1. Face Recognition Services**

#### `face_query_service.py`
```python
async def query_face_service(file: UploadFile) → dict
```

**Responsibilities:**
1. Decode image từ bytes
2. Extract ArcFace features
3. Predict emotion
4. FAISS query (top-1)
5. MySQL lookup
6. Log emotion nếu negative

**Key Functions:**
```python
def query_face_service(file: UploadFile = File(...)):
    # 1. Read image bytes
    # 2. Extract embedding (512-dim)
    # 3. Predict emotion (8 classes)
    # 4. FAISS search
    # 5. MySQL query
    # 6. Return response
```

---

#### `face_query_top5_service.py`
```python
@track_operation("face_query_top5")
async def query_face_top5_service(file: UploadFile) → dict
```

**Returns top-5 matches with timing**

---

### **2. Embedding Services**

#### `add_embedding_service.py`
```python
def add_embedding_service(
    class_id: int,
    image_file: UploadFile,
    image_path: str = None
) → dict
```

**Responsibilities:**
1. Extract ArcFace features
2. Add to FAISS index (normalized)
3. Save metadata
4. Store in MySQL

---

#### `edit_embedding_service.py`
```python
def edit_embedding_service(
    image_id: int,
    class_id: int,
    new_image_file: UploadFile = None
) → dict
```

**Update embedding in FAISS & MySQL**

---

### **3. Emotion Services**

#### `emonet_service.py` - **Custom ResNeXt50-32x4d Model**
```python
class ResNeXt50Emotion(nn.Module):
    def __init__(self, num_emotions=8):
        # ResNeXt50-32x4d backbone
        # Replace final FC layer for 8 emotions
        
    def forward(self, x):
        return self.backbone(x)  # logits

class EmoNetWrapper:
    def predict_from_image_bgr(img_bgr: np.ndarray):
        # Resize to 224x224
        # Normalize (ImageNet stats)
        # Forward pass
        # Return emotion & probability
```

**Model:** `model/emonet.pth`  
**Input:** 224x224 BGR image  
**Output:** 8 emotion classes

**Emotions:**
- 0: Neutral
- 1: Happy
- 2: Sad
- 3: Surprise
- 4: Fear
- 5: Disgust
- 6: Anger
- 7: Contempt

---

#### `add_emotion_service.py`
```python
def add_emotion_service(
    user_id: int = None,
    camera_id: int = None,
    emotion_type: str = None,
    confidence: float = None,
    image_file: UploadFile = None,
    note: str = None
) → dict
```

**Responsibilities:**
1. Validate user in assigned shift
2. Check working hours
3. Store emotion log
4. Save thumbnail

**Business Rules:**
- Only log emotions during assigned working shift
- Reject if outside shift time
- Save negative emotions automatically

---

#### `query_emotion_service.py`
```python
def query_emotion_service(
    user_id: int = None,
    emotion_type: str = None,
    start_ts: str = None,
    end_ts: str = None,
    limit: int = 100,
    offset: int = 0,
    include_image_base64: bool = False
) → dict
```

**Filter emotion logs with multiple criteria**

---

### **4. Attendance Services**

#### `checkin_service.py`
```python
def checkin_service(class_id: int) → dict
```

**Responsibilities:**
1. Get user details
2. Verify in assigned shift
3. Check within working hours
4. Create attendance log
5. Calculate shift type (day/night)

**Business Logic:**
```
- Check current time
- Verify against shift schedule
- If outside working hours → Error
- If in different assigned shift → Error
- If valid → Create checklog entry
```

---

#### `checkout_service.py`
```python
def checkout_service(class_id: int) → dict
```

---

#### `shift_attendance_service.py`
```python
def start_scheduler_background():
    # APScheduler job
    # Calculate daily/shift attendance
    # Update KPI scores
```

---

### **5. KPI Services**

#### `kpi_service.py`
```python
def get_kpi_service(
    user_id: int = None,
    start_date: str = None,
    end_date: str = None
) → dict
```

**Calculates:**
- Attendance score
- Emotion score
- Total score

---

#### `kpi_calculator.py`
```python
class KPICalculator:
    def calculate_attendance_score(user_id, date_range):
        # Count present/absent days
        # Calculate percentage
        
    def calculate_emotion_score(user_id, date_range):
        # Count positive emotions
        # Calculate percentage
        
    def calculate_total_score(attendance, emotion):
        # Weighted average
        # 60% attendance + 40% emotion
```

**Scoring Formula:**
```
Attendance Score = (Present Days / Total Days) * 100
Emotion Score = (Positive Emotions / Total Emotions) * 100
Total Score = (Attendance * 0.6) + (Emotion * 0.4)
```

---

### **6. User Management Services**

#### `add_users_service.py`
```python
def add_users_service(file: UploadFile) → dict
```

**Batch import từ Excel file**

---

#### `edit_users_service.py`
```python
def edit_users_service(user_id: int, updates: dict) → dict
```

---

#### `update_avatar_service.py`
```python
def update_avatar_service(user_id: int, avatar_file: UploadFile) → dict
```

---

### **7. Authentication Services**

#### `login_service.py`
```python
def login_service(username: str, password: str) → dict
```

**Returns:** Session token if valid

---

#### `reset_password_service.py`
```python
def reset_password_service(user_id: int, new_password: str) → dict
```

---

### **8. Shared Instances** - **CRITICAL!**

#### `shared_instances.py`
```python
class SharedInstances:
    _instance = None  # Singleton
    _lock = threading.Lock()
    
    def __init__(self):
        self.extractor = ArcFaceFeatureExtractor(...)  # Only ONCE
        self.faiss_manager = FaissIndexManager(...)    # Only ONCE
        self.faiss_lock = threading.Lock()             # Thread-safe

# Global functions
def get_extractor():
    return shared.get_extractor()

def get_faiss_manager():
    return shared.get_faiss_manager()

def get_faiss_lock():
    return shared.get_faiss_lock()
```

**Why Singleton?**
- Prevent duplicate model loading (memory leak)
- Ensure all requests use same FAISS index
- Thread-safe FAISS operations

---

### **9. Performance Monitoring**

#### `performance_monitor.py`
```python
@track_operation("face_query_top5")
async def query_face_top5_service(...):
    # Automatically measures execution time
    # Logs performance metrics
```

---

---

## 🗄️ Database Layer Modules (`db/`)

### Overview
Database layer quản lý MySQL operations

---

### **1. Data Models (`models.py`)**

#### `Nguoi` Class
```python
@dataclass
class Nguoi:
    id: int
    username: str
    pin: Optional[str]
    full_name: str
    age: Optional[int]
    address: Optional[str]
    phone: Optional[str]
    gender: Optional[str]
    role: str  # staff, manager, admin
    shift: str  # day, night
    status: str  # active, inactive
    avatar_url: Optional[bytes]  # BLOB
    embedding_vector: Optional[bytes]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self, include_avatar_base64: bool = False) → dict
```

**Methods:**
- `to_dict()`: Convert to JSON-serializable dict
- `from_row()`: Create from MySQL row

---

#### `TaiKhoan` Class
```python
@dataclass
class TaiKhoan:
    username: str
    passwrd: str  # Note: typo in original DB
    
    def from_row(row) → TaiKhoan
```

---

#### Other Models
```python
class CheckLog:  # Attendance log
    id, user_id, date, check_in_time, check_out_time, status

class EmotionLog:  # Emotion log
    id, user_id, emotion_type, confidence, image_bytes, timestamp

class EmbeddingVector:  # Stored embeddings
    id, user_id, embedding_bytes, created_at
```

---

### **2. Connection Management (`mysql_conn.py`)**

```python
class MySQLConnection:
    def __init__(self, host, user, password, database):
        self.connection = pymysql.connect(...)
    
    def execute(self, query, params=None):
        # Execute query
        # Return results
    
    def close(self):
        self.connection.close()
```

---

### **3. Repositories** (Repository Pattern)

#### `nguoi_repository.py` - User CRUD
```python
class NguoiRepository:
    def get_by_id(self, id: int) → Nguoi
    def get_by_username(self, username: str) → Nguoi
    def list_all(self, limit, offset) → List[Nguoi]
    def list_by_role(self, role: str) → List[Nguoi]
    def list_by_shift(self, shift: str) → List[Nguoi]
    
    def create(self, nguoi: Nguoi) → int  # Returns ID
    def update(self, id: int, updates: dict) → bool
    def delete(self, id: int) → bool
    
    # Embedding operations
    def add_embedding_vector(self, user_id: int, embedding_bytes: bytes)
    def get_embedding_vector(self, user_id: int) → bytes
    
    # Attendance operations
    def create_checklog(self, user_id: int, check_in_time, check_out_time)
    def get_checklogs(self, user_id: int, start_date, end_date) → List[CheckLog]
    
    # Emotion operations
    def add_emotion_log(self, user_id, emotion_type, confidence, image_bytes)
    def get_emotion_logs(self, user_id, start_ts, end_ts) → List[EmotionLog]
```

---

#### `taikhoan_repository.py` - Account CRUD
```python
class TaiKhoanRepository:
    def check_login(self, username: str, password: str) → bool
    def get_by_username(self, username: str) → TaiKhoan
    def create(self, username: str, password: str) → bool
    def update(self, username: str, new_password: str) → bool
    def delete(self, username: str) → bool
    def list_all(self) → List[TaiKhoan]
```

---

---

## 🔐 Authentication Layer (`auth/`)

### **MySQL Token Authentication**

#### `mysql_auth.py`
```python
class MySQLAuthService:
    def authenticate_user(self, username: str, password: str) → bool
        # Check against MySQL taikhoan table
    
    def create_session(self, username: str) → str
        # Generate session token
        # Store in active_sessions dict
    
    def get_current_user(self, session_token: str) → str
        # Get username from token
        # Check 24-hour expiration
    
    def logout(self, session_token: str)
        # Delete session
```

**Session Storage:**
```python
active_sessions = {
    "token_urlsafe_32chars": {
        "username": "user123",
        "created_at": timestamp,
        "role": "staff"
    }
}
```

---

#### `mysql_auth_api.py`
```python
@router.post('/auth/login')
def login(
    username: str = Form(...),
    password: str = Form(...)
) → JSONResponse
    # Verify credentials
    # Create session
    # Return token

@router.post('/auth/logout')
def logout(
    authorization: str = Header(...)
) → JSONResponse
    # Delete session
```

---

#### Dependency: `get_current_user_mysql`
```python
def get_current_user_mysql(
    request: Request,
    authorization: Optional[str] = Header(None)
) → str
    # Check Authorization header
    # Fall back to cookies
    # Verify token in active_sessions
    # Raise 401 if invalid
```

**Used in Protected Endpoints:**
```python
@router.post('/add-embedding')
def add_embedding(
    ...,
    current_user: str = Depends(get_current_user_mysql)
) → JSONResponse
    # User authenticated
```

---

---

## 🤖 AI Model Modules (`model/`)

### **1. ArcFace Feature Extractor** (`arcface_model.py`)

```python
class ArcFaceFeatureExtractor:
    def __init__(self, model_path, model_version='r100', device=None):
        # model_version: r18, r50, r100
        # model_path: path to .pth weights
        # device: cuda or cpu
        
    def extract(self, img) → np.ndarray:
        # Input: RGB image or path
        # Process:
        #   1. Resize to 112x112
        #   2. Normalize: (x - 0.5) / 0.5
        #   3. Forward pass
        #   4. L2 normalize embedding
        # Output: 512-dim float32 vector
```

**Model Details:**
- **Input:** 112x112 RGB image
- **Output:** 512-dim embedding vector
- **Backbone:** r100 (ResNet-100)
- **Normalization:** (x - 0.5) / 0.5

**Inference:**
```python
extractor = ArcFaceFeatureExtractor(
    model_path='model/glint360k_cosface_r100_fp16_0.1.pth',
    model_version='r100'
)

image = cv2.imread('face.jpg')
embedding = extractor.extract(image)  # (512,)
```

---

### **2. Custom Emotion Model** (`emonet_service.py`) - **NEW!**

```python
class ResNeXt50Emotion(nn.Module):
    def __init__(self, num_emotions=8):
        super().__init__()
        # ResNeXt50-32x4d backbone
        self.backbone = models.resnext50_32x4d(pretrained=True)
        
        # Replace FC layer
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Linear(num_features, num_emotions)
    
    def forward(self, x):
        return self.backbone(x)  # (batch_size, 8) logits

class EmoNetWrapper:
    def predict_from_image_bgr(self, img_bgr: np.ndarray):
        # Input: BGR image
        # Process:
        #   1. Convert BGR → RGB
        #   2. Resize to 224x224
        #   3. Normalize: (x/255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        #   4. Forward pass → logits
        #   5. Softmax → probabilities
        #   6. Argmax → emotion class
        # Output: (emotion_name, probability)
```

**Model Details:**
- **Backbone:** ResNeXt50-32x4d (pretrained)
- **Input:** 224x224 BGR image
- **Output:** 8 emotion classes
- **Weights:** `model/emonet.pth`

**Emotion Classes:**
```
0: Neutral
1: Happy
2: Sad
3: Surprise
4: Fear
5: Disgust
6: Anger
7: Contempt
```

**Inference:**
```python
wrapper = EmoNetWrapper(model_path='model/emonet.pth')
emotion_name, probability = wrapper.predict_from_image_bgr(img_bgr)
# emotion_name: "Happy"
# probability: 0.92
```

---

---

## 🔍 Index & Vector Search (`index/`)

### **FAISS Index Manager** (`faiss.py`)

```python
class FaissIndexManager:
    def __init__(self, embedding_size=512, index_path=None, meta_path=None):
        self.embedding_size = embedding_size
        self.index = faiss.IndexFlatIP(512)  # Inner Product (cosine)
        self.embeddings = []
        self.image_ids = []
        self.image_paths = []
        self.class_ids = []  # user_ids
    
    def add_embeddings(self, embeddings, image_ids, image_paths, class_ids):
        # Normalize embeddings
        # Add to index
        # Store metadata
    
    def query(self, query_embedding, topk=5):
        # Input: 512-dim query embedding
        # Return: top-5 matches with scores
        # Output: [{"image_id": 1, "class_id": 123, "score": 0.95, ...}]
    
    def save(self):
        # Save index to faiss_db_r18.index
        # Save metadata to faiss_db_r18_meta.npz
    
    def load(self):
        # Load index from files
    
    def reset_index(self):
        # Clear all embeddings
```

**Index Type:** `IndexFlatIP`
- **IndexFlatIP:** Inner Product (equivalent to cosine similarity for normalized vectors)
- **Complexity:** O(n) - brute force search
- **Accuracy:** 100% - exact search

**Files:**
- `faiss_db_r18.index`: Binary FAISS index (~20 MB for 5000 embeddings)
- `faiss_db_r18_meta.npz`: Metadata (image_ids, paths, class_ids)

---

---

## 📊 Complete Module Dependency Graph

```
┌─────────────┐
│  app.py     │ FastAPI application
└────┬────────┘
     │
     ├─► api/*.py (38 endpoints)
     │   ├─► service/*.py (44 services)
     │   │   ├─► db/*.py (Database layer)
     │   │   │   └─► mysql_conn.py
     │   │   │
     │   │   ├─► model/*.py (AI models)
     │   │   │   ├─► arcface_model.py
     │   │   │   └─► emonet_service.py
     │   │   │
     │   │   ├─► index/faiss.py
     │   │   │
     │   │   └─► shared_instances.py
     │   │
     │   └─► auth/mysql_auth.py (Dependency)
     │
     ├─► config.py (Configuration)
     │
     └─► Database (MySQL)
```

---

**Last Updated:** December 20, 2025
