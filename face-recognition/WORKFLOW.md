# 🔄 Face Recognition System - Workflow & Execution Flow

**Version:** 2.0.0  
**Last Updated:** December 2025

---

## 📋 Table of Contents

1. [System Startup Flow](#system-startup-flow)
2. [Face Recognition Workflow](#face-recognition-workflow)
3. [Emotion Detection Workflow](#emotion-detection-workflow)
4. [Attendance Tracking Workflow](#attendance-tracking-workflow)
5. [Authentication & Authorization](#authentication--authorization)
6. [Data Synchronization](#data-synchronization)
7. [Error Handling](#error-handling)

---

## 🚀 System Startup Flow

### **Step-by-Step Initialization**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Start Server: python -m uvicorn app:app --reload        │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Load Configuration (config.py)                           │
│    - MODEL_PATH (ArcFace weights)                           │
│    - EMOTION_MODEL_PATH (ResNeXt50-32x4d)                   │
│    - FAISS_INDEX_PATH, FAISS_META_PATH                      │
│    - MySQL connection params                                │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Initialize Shared Instances (SharedInstances Singleton) │
│    ⚠️ CRITICAL SECTION - Only happens ONCE                  │
└────────────┬────────────────────────────────────────────────┘
             │
        ┌────┴────────────┬─────────────────┬─────────────────┐
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
   ┌─────────┐      ┌──────────┐      ┌───────────┐    ┌──────────┐
   │ Load    │      │ Load     │      │ Create    │    │ Load     │
   │ ArcFace │      │ FAISS    │      │ FAISS     │    │ Emotion  │
   │ Model   │      │ Index    │      │ Lock      │    │ Model    │
   │(GPU)    │      │from disk │      │(threading)│    │(GPU)     │
   └────┬────┘      └────┬─────┘      └─────┬─────┘    └────┬─────┘
        │                │                  │              │
        └────────────────┼──────────────────┴──────────────┘
                         │
                         ▼
                  ┌─────────────────┐
                  │ Singleton Ready │
                  │ All instances   │
                  │ loaded in memory│
                  └────────┬────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────────┐
        │ 4. Connect to MySQL                          │
        │    - Test connection                         │
        │    - Verify schema exists                    │
        │    - Initialize repositories                 │
        └────────────┬─────────────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────────────────┐
        │ 5. Start FastAPI Application                 │
        │    - Register all 38 API endpoints           │
        │    - Enable CORS middleware                  │
        │    - Set up logging                          │
        └────────────┬─────────────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────────────────┐
        │ 6. Server Ready!                             │
        │    ✅ Listening on http://localhost:8000     │
        │    📚 Docs: http://localhost:8000/docs       │
        └──────────────────────────────────────────────┘
```

### **Critical: Singleton Pattern**

```python
# First request triggers initialization
class SharedInstances:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:  # Thread-safe
                if cls._instance is None:
                    # LOAD MODELS HERE - ONLY ONCE
                    cls._instance = super().__new__(cls)
                    cls._instance._load_models()
        return cls._instance

# Subsequent requests reuse same instance
Request 1: Initializes models (slow, ~10 seconds)
Request 2: Reuses models (fast, ~100ms)
Request 3: Reuses models (fast, ~100ms)
...
```

---

## 🔍 Face Recognition Workflow

### **Complete End-to-End Flow: Query Image → Identified Person**

#### **Sequence Diagram**

```
User                API Layer            Service Layer         Model Layer          DB Layer
│                     │                      │                   │                    │
│─ POST /query ───────>                      │                   │                    │
│  (image file)        │                      │                   │                    │
│                      │                      │                   │                    │
│                      │─ Read image bytes ──>                    │                    │
│                      │  (decode JPEG/PNG)   │                   │                    │
│                      │                      │                   │                    │
│                      │─ Extract ArcFace ───────────────────────>                    │
│                      │  embeddings          │   Model Inference │                    │
│                      │                      │   (112x112 norm)   │                    │
│                      │<──── 512-dim ────────────────────────────                    │
│                      │      embedding       │                   │                    │
│                      │                      │                   │                    │
│                      │─ Predict emotion ───────────────────────>                    │
│                      │  (ResNeXt50-32x4d)   │   Model Inference │                    │
│                      │                      │   (224x224 img)    │                    │
│                      │<─ Emotion result ────────────────────────                    │
│                      │  (Happy, 0.92)       │                   │                    │
│                      │                      │                   │                    │
│                      │─ FAISS query ───────>                    │                    │
│                      │  (top-1)             │   Similarity Search│                    │
│                      │<─ Match result ──────                    │                    │
│                      │  {id:1, score:0.95}  │                   │                    │
│                      │                      │                   │                    │
│                      │─ MySQL lookup ──────────────────────────────────────────────>
│                      │  (SELECT * FROM      │                   │                    │
│                      │   Nguoi WHERE id=123)│                   │                    │
│                      │<────── Person data ───────────────────────────────────────────
│                      │  {name, role, shift} │                   │                    │
│                      │                      │                   │                    │
│                      │─ Log emotion ───────────────────────────────────────────────>
│                      │  (if negative)       │                   │                    │
│                      │                      │                   │                    │
│<─ 200 JSON ──────────                      │                   │                    │
│  Response            │                      │                   │                    │
│  {nguoi, emotion}    │                      │                   │                    │
```

#### **Detailed Step-by-Step**

### **Step 1: Image Upload & Decoding**

```python
# face_query.py
@router.post('/query')
async def query_face(file: UploadFile):
    image_bytes = await file.read()  # Read from upload
    
    # Decode to OpenCV format
    buf = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    
    if image is None:
        return {"error": "Invalid image format"}
```

**Input Formats:** JPEG, PNG, BMP, etc.  
**Output:** BGR numpy array (H, W, 3)

---

### **Step 2: Extract ArcFace Embedding**

```python
# service/face_query_service.py
from service.shared_instances import get_extractor

extractor = get_extractor()  # Singleton - same instance
embedding = extractor.extract(image)  # ArcFace inference

# ArcFaceFeatureExtractor.extract():
# 1. Convert BGR → RGB
# 2. Resize to 112x112
# 3. Normalize: (x - 0.5) / 0.5
# 4. Forward pass through ResNet-100
# 5. Output: 512-dim embedding (L2 normalized)

# embedding shape: (512,)
# embedding dtype: float32
```

**Performance:** ~50ms on GPU (RTX 3060+)

---

### **Step 3: Emotion Detection**

```python
# service/emonet_service.py
from service.emonet_service import predict_emotion_from_bytes

emo_result = predict_emotion_from_bytes(image_bytes)
# Returns: {"emotion": "Happy", "prob": 0.92}

# ResNeXt50Emotion Inference:
# 1. Convert BGR → RGB
# 2. Resize to 224x224
# 3. Normalize with ImageNet stats: 
#    (x/255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
# 4. Forward pass through ResNeXt50-32x4d
# 5. Softmax on 8 logits
# 6. Argmax to get emotion class
# 7. Get max probability
```

**Emotion Classes:**
- 0: Neutral (default)
- 1: Happy
- 2: Sad
- 3: Surprise
- 4: Fear (negative)
- 5: Disgust (negative)
- 6: Anger (negative)
- 7: Contempt (negative)

**Performance:** ~30ms on GPU

---

### **Step 4: FAISS Similarity Search**

```python
# service/face_query_service.py
from service.shared_instances import get_faiss_manager, get_faiss_lock

faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()

# Thread-safe FAISS query
with faiss_lock:
    results = faiss_manager.query(embedding, topk=1)

# results = [
#   {
#     "image_id": 1001,
#     "image_path": "avatars/user123/face_001.jpg",
#     "class_id": 123,
#     "score": 0.9523
#   }
# ]

# Score = cosine similarity (0.0 to 1.0)
# 1.0 = identical, 0.0 = completely different
```

**Search Algorithm:**
- **Index Type:** IndexFlatIP (Inner Product)
- **Complexity:** O(n) - brute force, but very fast
- **Distance Metric:** L2 + Cosine (normalized vectors)

**Score Interpretation:**
```
score > 0.85: High confidence match
0.60-0.85: Medium confidence
< 0.60: Low confidence / No match
```

**Threshold Used:** 0.57 (configured in code)

---

### **Step 5: MySQL Person Lookup**

```python
# service/face_query_service.py
class_id = str(results[0]['class_id'])  # 123

# Query MySQL
try:
    nguoi = nguoi_repo.get_by_id(int(class_id))
    # SELECT * FROM Nguoi WHERE id = 123
    
    # Returns Nguoi object:
    # id: 123
    # username: "user123"
    # full_name: "Nguyễn Văn A"
    # role: "staff"
    # shift: "day"
    # avatar_url: <BLOB>
    # ... other fields
except Exception as e:
    nguoi = None
```

**Database Query:**
```sql
SELECT id, username, full_name, age, gender, phone, 
       role, shift, status, avatar_url 
FROM Nguoi 
WHERE id = 123;
```

---

### **Step 6: Emotion Logging (Conditional)**

```python
# service/face_query_service.py
negative_set = {"Sad", "Fear", "Disgust", "Anger", "Contempt"}

if nguoi and emo_label in negative_set:
    # Only log NEGATIVE emotions automatically
    try:
        add_emotion_service(
            user_id=int(class_id),
            emotion_type=str(emo_label),
            confidence=float(emo_prob),
            image_file=file_obj
        )
        # INSERT INTO EmotionLog (...)
    except Exception as e:
        print(f"Failed to log emotion: {e}")
```

**Business Rule:**
- Only negative emotions are auto-logged
- Prevents spam from happy faces
- Useful for early warning system

---

### **Step 7: Return Response**

```python
# Return full response
response = {
    'image_id': 1001,
    'image_path': 'avatars/user123/face_001.jpg',
    'class_id': '123',
    'score': 0.9523,
    'emotion': {
        'emotion': 'Happy',
        'prob': 0.92
    },
    'nguoi': {
        'id': 123,
        'username': 'user123',
        'full_name': 'Nguyễn Văn A',
        'role': 'staff',
        'shift': 'day',
        'avatar_url': 'data:image/jpeg;base64,...'
    }
}

return JSONResponse(content=response, status_code=200)
```

**Response Time:** ~150-200ms total
- Image decode: 10ms
- ArcFace inference: 50ms
- Emotion inference: 30ms
- FAISS search: 10ms
- MySQL query: 20ms
- JSON serialization: 10ms

---

---

## 😊 Emotion Detection Workflow

### **Detailed: How Emotion Recognition Works**

#### **Flow Diagram**

```
Input Image
    │
    ▼
┌──────────────────────────────────┐
│ 1. Image Preprocessing           │
│    - BGR → RGB conversion        │
│    - Resize to 224x224           │
│    - Normalize (ImageNet stats)  │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ 2. ResNeXt50-32x4d Backbone      │
│    Forward Pass                  │
│    (Pre-trained on ImageNet)     │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ 3. Custom FC Layer               │
│    [feature_dim] → [8]           │
│    (Emotion classifier)          │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ 4. Output Logits                 │
│    shape: (8,)                   │
│    logits for 8 emotions         │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ 5. Softmax Normalization         │
│    σ(logits) = exp(logits) / Σ   │
│    Probabilities: [0.0 - 1.0]    │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ 6. Argmax Selection              │
│    idx = argmax(probabilities)   │
│    emotion = class_names[idx]    │
└────────────┬─────────────────────┘
             │
             ▼
        Output:
    "Happy" (0.92)
```

#### **Implementation Details**

```python
# model/emonet_service.py

class ResNeXt50Emotion(nn.Module):
    def __init__(self, num_emotions=8):
        super().__init__()
        # Load ImageNet pretrained ResNeXt50-32x4d
        self.backbone = models.resnext50_32x4d(pretrained=True)
        
        # Replace final FC layer for emotion classification
        num_features = self.backbone.fc.in_features  # 2048
        self.backbone.fc = nn.Linear(num_features, num_emotions)  # 2048 → 8
    
    def forward(self, x):
        # x shape: (batch_size, 3, 224, 224)
        logits = self.backbone(x)  # (batch_size, 8)
        return logits

# Inference
class EmoNetWrapper:
    def predict_from_image_bgr(self, img_bgr: np.ndarray):
        """
        Args:
            img_bgr: BGR numpy array (H, W, 3)
        
        Returns:
            (emotion_name: str, probability: float)
        """
        # 1. Convert BGR → RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # 2. Resize to 224x224
        img_resized = cv2.resize(img_rgb, (224, 224))
        
        # 3. Normalize (divide by 255 to [0, 1])
        tensor = torch.from_numpy(
            img_resized.astype(np.float32) / 255.0
        ).permute(2, 0, 1).unsqueeze(0).to(device)  # (1, 3, 224, 224)
        
        # 4. Apply ImageNet normalization
        mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
        tensor = (tensor - mean) / std
        
        # 5. Forward pass
        with torch.no_grad():
            logits = self.net(tensor)  # (1, 8)
        
        # 6. Softmax to get probabilities
        probs = torch.nn.functional.softmax(logits, dim=1)  # (1, 8)
        
        # 7. Get argmax (predicted class)
        pred_idx = int(torch.argmax(probs, dim=1).cpu().item())  # 0-7
        
        # 8. Get max probability
        pred_prob = float(probs[0, pred_idx].cpu().item())  # 0.0-1.0
        
        # 9. Map to emotion name
        emotion_name = EMOTION_CLASSES.get(pred_idx, str(pred_idx))
        
        return emotion_name, pred_prob
```

#### **Emotion Classes Mapping**

```python
EMOTION_CLASSES = {
    0: "Neutral",      # No clear emotion
    1: "Happy",        # ✓ Positive
    2: "Sad",          # ✗ Negative
    3: "Surprise",     # ? Neutral
    4: "Fear",         # ✗ Negative
    5: "Disgust",      # ✗ Negative
    6: "Anger",        # ✗ Negative
    7: "Contempt"      # ✗ Negative
}

NEGATIVE_EMOTIONS = {"Sad", "Fear", "Disgust", "Anger", "Contempt"}
POSITIVE_EMOTIONS = {"Happy"}
```

---

### **When Emotions are Logged**

```
Face Recognition Query
    ↓
    ├─ Detect emotion from uploaded image
    ├─ Find matching person in FAISS
    │
    ├─ IF emotion is NEGATIVE AND person found:
    │   │
    │   └─► Auto-log to EmotionLog table
    │       - INSERT INTO EmotionLog (user_id, emotion_type, confidence, image_bytes, timestamp)
    │
    └─ IF emotion is positive/neutral:
        └─► Don't log (no action)
```

**Business Logic:**
- Early warning for employee mood issues
- Track negative emotions over time
- Calculate emotion KPI scores

---

---

## 📋 Attendance Tracking Workflow

### **Check-In/Check-Out Complete Flow**

#### **Sequence Diagram: Check-In**

```
Employee                API                Service              DB           Time
    │                   │                   │                   │             │
    │─ Scan face ──────>│                   │                   │             │
    │  (POST /checkin)  │                   │                   │             │
    │                   │                   │                   │             │
    │                   │─ Face recognition─>                   │             │
    │                   │  (query_face)     │                   │             │
    │                   │                   │                   │             │
    │                   │<─ Person found ───                   │             │
    │                   │  {id: 123}        │                   │             │
    │                   │                   │                   │             │
    │                   │─ Get current time ──────────────────────────────>   │
    │                   │  (now = 08:00 AM) │                   │             │
    │                   │<─ current time ───────────────────────────────────  │
    │                   │                   │                   │             │
    │                   │─ Check shift ────>                    │             │
    │                   │  (user shift=day) │                   │             │
    │                   │  (working hours   │                   │             │
    │                   │   = 8:00-17:00)   │                   │             │
    │                   │                   │                   │             │
    │                   ├─ Verify timing───>                    │             │
    │                   │  (in working hours│                   │             │
    │                   │   and correct     │                   │             │
    │                   │   shift)          │                   │             │
    │                   │                   │                   │             │
    │                   │─ Create attendance log ──────────────>│             │
    │                   │  (INSERT checklog)│                   │             │
    │                   │                   │                   │             │
    │<─ Success ────────                    │                   │             │
    │  (Check-in OK)    │                   │                   │             │
    │  timestamp: 08:00 │                   │                   │             │
    │                   │                   │                   │             │
```

#### **Detailed Steps**

### **Step 1: Face Recognition**
```python
# Identify employee
# (Same as query_face workflow)
class_id = 123  # Identified employee
```

---

### **Step 2: Get Current Time & Shift**
```python
# Get employee's assigned shift
user = nguoi_repo.get_by_id(int(class_id))
shift = getattr(user, 'shift', 'day')  # 'day' or 'night'

# Get current local time (Vietnam timezone)
TZ = pytz.timezone('Asia/Ho_Chi_Minh')
now_local = datetime.now(TZ)
current_time = now_local.time()

# Example: 08:30 AM
# shift: 'day'
```

---

### **Step 3: Check Working Hours**
```python
# Define shift times (configurable)
SHIFT_DAY_START = time(8, 0)      # 08:00
SHIFT_DAY_END = time(17, 0)       # 17:00
SHIFT_NIGHT_START = time(17, 0)   # 17:00
SHIFT_NIGHT_END = time(8, 0)      # 08:00 next day

# Determine current shift period
def get_shift_by_time(current_time):
    if SHIFT_DAY_START <= current_time < SHIFT_DAY_END:
        return 'day'
    elif current_time >= SHIFT_NIGHT_START or current_time < SHIFT_NIGHT_END:
        return 'night'
    else:
        return 'none'  # Outside working hours

current_shift = get_shift_by_time(current_time)  # 'day'
```

---

### **Step 4: Validate Shift Match**
```python
# Check if employee is in the correct shift
if current_shift == 'none':
    # Outside working hours
    return {
        "success": False,
        "message": f"Cannot check-in outside working hours. "
                  f"Working hours: Day {SHIFT_DAY_START}-{SHIFT_DAY_END}, "
                  f"Night {SHIFT_NIGHT_START}-{SHIFT_NIGHT_END}",
        "status_code": 403
    }

if current_shift != shift:
    # Employee assigned to wrong shift
    return {
        "success": False,
        "message": f"Cannot check-in in {current_shift} shift. "
                  f"Employee assigned to {shift} shift",
        "status_code": 403
    }

# ✓ Valid: Create check-in record
```

---

### **Step 5: Create Attendance Log**
```python
# Insert into checklog table
rowid = nguoi_repo.create_checklog(
    user_id=int(class_id),
    check_in_time=now_local,
    check_out_time=None,  # Filled on checkout
    date=now_local.date(),
    status='present'
)

# SQL generated:
# INSERT INTO checklog (user_id, check_in_time, date, status)
# VALUES (123, '2025-12-20 08:00:00', '2025-12-20', 'present')
```

---

### **Step 6: Return Response**
```python
return {
    "success": True,
    "message": "Check-in successful",
    "timestamp": "2025-12-20T08:00:00+07:00",
    "person": {
        "id": 123,
        "full_name": "Nguyễn Văn A",
        "shift": "day"
    }
}
```

---

### **Check-Out Flow** (Similar, with check_out_time)

```python
# UPDATE checklog SET check_out_time = NOW()
# WHERE id = <last_checkin_id> AND user_id = 123
```

---

---

## 🔐 Authentication & Authorization

### **Login Flow**

```
User                API                Auth Service         MySQL
 │                   │                   │                    │
 │─ POST /auth/login─>                   │                    │
 │  {username, pwd}  │                   │                    │
 │                   │                   │                    │
 │                   │─ Check credentials>                    │
 │                   │                   │                    │
 │                   │─ Query MySQL ─────────────────────────>
 │                   │  SELECT * FROM    │                    │
 │                   │  taikhoan WHERE   │                    │
 │                   │  username = ?     │                    │
 │                   │                   │                    │
 │                   │<─ User found ─────────────────────────<
 │                   │                   │                    │
 │                   │─ Verify password ─>                    │
 │                   │  (compare hashes) │                    │
 │                   │                   │                    │
 │                   ├─ Password matches?│                    │
 │                   │  YES ✓            │                    │
 │                   │                   │                    │
 │                   │─ Create session ──>                    │
 │                   │  token = secrets. │                    │
 │                   │  token_urlsafe(32)│                    │
 │                   │                   │                    │
 │                   │─ Store in dict ──>                    │
 │                   │  active_sessions  │                    │
 │                   │  [token] = {      │                    │
 │                   │    username,      │                    │
 │                   │    created_at     │                    │
 │                   │  }                │                    │
 │                   │                   │                    │
 │<─ 200 OK ─────────                   │                    │
 │  {                │                   │                    │
 │    "session_token": │                 │                    │
 │    "abc123..."   │                   │                    │
 │  }               │                    │                    │
 │                   │                   │                    │
```

#### **Code**

```python
# auth/mysql_auth_api.py
@router.post('/auth/login')
def login(
    username: str = Form(...),
    password: str = Form(...)
):
    # 1. Verify credentials
    if not mysql_auth.authenticate_user(username, password):
        return JSONResponse(
            {"success": False, "message": "Invalid credentials"},
            status_code=401
        )
    
    # 2. Create session token
    session_token = mysql_auth.create_session(username)
    
    # 3. Return token
    return {
        "success": True,
        "session_token": session_token
    }
```

---

### **Protected API Call Flow**

```
Client                API               Dependency            Auth Service
 │                    │                  │                      │
 │─ GET /users ──────>│                  │                      │
 │  Header:           │                  │                      │
 │  Authorization:    │                  │                      │
 │  Bearer abc123... │                  │                      │
 │                    │                  │                      │
 │                    │─ get_current_user_mysql() ────>        │
 │                    │  (Dependency injection)  │              │
 │                    │                  │                      │
 │                    │                  │─ Extract token ───>
 │                    │                  │  from Authorization │
 │                    │                  │  header             │
 │                    │                  │                      │
 │                    │                  │─ Lookup in dict ─>
 │                    │                  │  active_sessions   │
 │                    │                  │                      │
 │                    │                  │  Token found? ✓     │
 │                    │                  │  Not expired? ✓     │
 │                    │                  │                      │
 │                    │                  │<─ Return username ─<
 │                    │<─ current_user ──                      │
 │                    │  "user123"       │                      │
 │                    │                  │                      │
 │                    ├─ Handler logic ──                       │
 │                    │  (can use user)  │                      │
 │                    │                  │                      │
 │<─ 200 JSON ────────                  │                      │
 │  Users list        │                  │                      │
 │                    │                  │                      │
```

#### **Code**

```python
# auth/mysql_auth.py
def get_current_user_mysql(
    request: Request,
    authorization: Optional[str] = Header(None)
) → str:
    """FastAPI Dependency for authentication"""
    
    session_token = None
    
    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        session_token = authorization.replace("Bearer ", "")
    
    # Fall back to cookies
    if not session_token:
        session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not logged in"
        )
    
    # Validate token
    current_user = mysql_auth.get_current_user(session_token)
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    return current_user

# Usage in endpoint
@router.get('/users')
def list_users(
    current_user: str = Depends(get_current_user_mysql)
):
    # Only reaches here if authenticated
    # current_user = "user123"
    ...
```

---

### **Logout Flow**

```python
# auth/mysql_auth_api.py
@router.post('/auth/logout')
def logout(
    authorization: str = Header(...)
):
    # Extract token
    session_token = authorization.replace("Bearer ", "")
    
    # Delete from active_sessions
    mysql_auth.logout(session_token)
    
    return {"success": True, "message": "Logged out"}
```

**Result:** Token deleted from `active_sessions` dict → Subsequent requests fail

---

---

## 🔄 Data Synchronization

### **FAISS Index Synchronization**

#### **Problem:** Multiple processes/requests modifying FAISS

#### **Solution:** Thread-safe locks

```python
# shared_instances.py
faiss_lock = threading.Lock()

# Usage in services
with faiss_lock:
    # Only one thread executes this block at a time
    faiss_manager.add_embeddings(emb, img_ids, paths, class_ids)
    faiss_manager.save()
    # All other threads wait here...

# Another thread
with faiss_lock:
    results = faiss_manager.query(emb, topk=5)
    # Can execute only after first thread releases lock
```

---

### **MySQL Transaction Management**

```python
# db/mysql_conn.py
class MySQLConnection:
    def execute_transaction(self, queries: List[str]):
        try:
            cursor = self.connection.cursor()
            for query in queries:
                cursor.execute(query)
            self.connection.commit()  # ✓ All or nothing
        except Exception as e:
            self.connection.rollback()  # Undo all changes
            raise e
```

---

---

## ⚠️ Error Handling

### **Hierarchy**

```
┌─────────────────────────────────────────┐
│ FastAPI Exception Handlers              │
└──────┬──────────────────────────────────┘
       │
   ┌───┴───────────────────────┬─────────┐
   │                           │         │
   ▼                           ▼         ▼
ValidationError          HTTPException  ServerError
(400 Bad Request)        (custom codes) (500 Server Error)

Examples:
- 400: Invalid image format
- 401: Unauthorized (not logged in)
- 403: Forbidden (outside shift hours)
- 404: User not found
- 500: Model inference failed
```

---

### **Error Response Format**

```json
{
  "success": false,
  "message": "User error message",
  "error_code": "ERROR_CODE",
  "status_code": 400,
  "timestamp": "2025-12-20T10:30:00Z"
}
```

---

### **Common Error Scenarios**

| Scenario | Status | Message |
|----------|--------|---------|
| Invalid image | 400 | "Invalid image format" |
| No match found | 200 | {} (empty response) |
| Outside shift hours | 403 | "Cannot check-in outside..." |
| Not logged in | 401 | "Not logged in or session..." |
| User not found | 404 | "User not found" |
| Model inference failed | 500 | "Model inference error" |
| MySQL connection failed | 500 | "Database connection error" |

---

---

## 📊 Performance Metrics

### **Typical Response Times**

| Operation | Time | Notes |
|-----------|------|-------|
| Image decode | 10ms | Depends on image size |
| ArcFace inference | 50ms | GPU: RTX 3060+ |
| Emotion inference | 30ms | GPU |
| FAISS search (5000 embeddings) | 10ms | IndexFlatIP |
| MySQL query | 20ms | Simple SELECT |
| JSON response build | 10ms | - |
| **Total: Face Recognition** | **150ms** | End-to-end |
| **Total: Check-in** | **200ms** | With attendance logging |

---

**Last Updated:** December 20, 2025
