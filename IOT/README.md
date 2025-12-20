# 🌐 IoT Raspberry Pi Face Recognition Module

**Version:** 1.0.0  
**Last Updated:** December 2025  
**Platform:** Raspberry Pi 4B+ / Raspberry Pi 5

---

## 📋 Table of Contents

1. [Module Overview](#module-overview)
2. [Architecture](#architecture)
3. [Hardware Setup](#hardware-setup)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Main Components](#main-components)
7. [Execution Flow](#execution-flow)
8. [API Integration](#api-integration)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Module Overview

### **Purpose**
The IoT Raspberry Pi module provides a **lightweight edge device** for real-time face recognition and emotion detection. It communicates with the central Face Recognition API server to:

- Capture video from camera
- Perform face detection
- Send frames to API server
- Receive recognition results
- Display results on screen
- Log attendance
- Alert based on emotions

### **Key Features**

| Feature | Description |
|---------|-----------|
| **Real-time Video** | Capture from camera/USB device |
| **Face Detection** | Lightweight MTCNN or MediaPipe |
| **API Integration** | HTTPS communication with central server |
| **Emotion Tracking** | Receive emotion results from server |
| **Display & Logging** | Show results on screen, log to file |
| **Low Power** | Optimized for Raspberry Pi hardware |
| **Offline Fallback** | Works with cached results if server down |

---

## 🏛️ Architecture

### **System Diagram**

```
┌──────────────────────────────────────┐
│      Raspberry Pi 4B+ / Pi 5         │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │   Face Recognition App          │ │
│  │   (python, OpenCV)              │ │
│  └──┬─────────────────────────────┬┘ │
│     │                             │  │
│  ┌──▼──────────┐    ┌────────────▼──┐
│  │   Camera    │    │  Video Display │
│  │   Module    │    │   (HDMI/LCD)   │
│  └─────────────┘    └────────────────┘
│        │                               │
│        ▼                               │
│  ┌────────────────────────────┐       │
│  │ Face Detection (MediaPipe) │       │
│  │ Lightweight inference      │       │
│  └────────┬───────────────────┘       │
│           │                           │
│           ▼                           │
│  ┌────────────────────────────┐       │
│  │ Send to API Server via     │       │
│  │ HTTPS/REST API             │       │
│  └────────┬───────────────────┘       │
│           │                           │
└───────────┼───────────────────────────┘
            │
            │ HTTP POST /query
            │ (image bytes)
            │
            ▼
   ┌────────────────────┐
   │  Central Server    │
   │  Face Recognition  │
   │  (GPU instance)    │
   └────────┬───────────┘
            │
   Results: │
   - Person │
   - Score  │
   - Emotion│
            │
            ▼
   ┌────────────────────┐
   │  Raspberry Pi      │
   │  Display & Log     │
   │  Results           │
   └────────────────────┘
```

---

## 🔌 Hardware Setup

### **Required Components**

| Component | Specification | Purpose |
|-----------|--------------|---------|
| **Raspberry Pi** | 4B+ or 5 (4GB+ RAM) | Main processor |
| **Camera** | CSI Camera or USB webcam | Video capture |
| **Display** | HDMI or 7" touchscreen | Display results |
| **Cooling** | Case + heat sink + fan | Thermal management |
| **Power** | USB-C 5V/3A+ | Power supply |
| **Storage** | microSD 32GB+ | OS & app storage |
| **Network** | WiFi or Ethernet | Connection to server |

### **Camera Connection**

```
Option 1: CSI Camera (Recommended)
┌─────────────────┐
│  Raspberry Pi   │
│  Camera Port    │
└────────┬────────┘
         │ Flat ribbon cable
         ▼
    ┌─────────┐
    │ Camera  │ (up to 5MP)
    └─────────┘

Option 2: USB Webcam
┌─────────────────┐
│  Raspberry Pi   │
│  USB Port       │
└────────┬────────┘
         │ USB cable
         ▼
    ┌─────────┐
    │ Webcam  │ (1080p+)
    └─────────┘
```

---

## 💾 Installation

### **Step 1: OS Setup**

```bash
# 1. Download Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# 2. Flash Raspberry Pi OS Lite to microSD
# Recommended: Bullseye or Bookworm

# 3. Boot Pi and update system
sudo apt update
sudo apt upgrade -y

# 4. Enable camera interface
sudo raspi-config
# Interface Options > Camera > Enable > Reboot
```

### **Step 2: Install Dependencies**

```bash
# Python and pip
sudo apt install python3-pip python3-dev -y

# OpenCV dependencies
sudo apt install libatlas-base-dev libjasper-dev libharfbuzz0b libwebp6 -y
sudo apt install libharfbuzz0b libwebpdemux0 libwebpmux3 -y

# Media processing
sudo apt install python3-opencv -y

# Networking
sudo apt install curl wget -y
```

### **Step 3: Install Python Packages**

```bash
# Clone repository
git clone <repo-url>
cd face-recognition/IOT

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Main packages:
# - opencv-python
# - numpy
# - requests
# - pillow
# - mediapipe (for face detection)
```

### **Step 4: Configure Settings**

Edit `raspberry_face_app.py`:

```python
# API Server configuration
API_SERVER = "http://192.168.1.100:8000"  # IP of central server
API_ENDPOINT = f"{API_SERVER}/query"
AUTH_TOKEN = "your_session_token"

# Camera settings
CAMERA_SOURCE = 0  # 0 for CSI, path for USB
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# Display settings
DISPLAY_RESULT_TIME = 3  # seconds
SHOW_FPS = True
SHOW_EMOTIONS = True
```

### **Step 5: Run Application**

```bash
# Start the app
python3 raspberry_face_app.py

# Output:
# 🚀 Starting Face Recognition IoT Module
# 📹 Camera initialized: 640x480 @ 30fps
# 🌐 Connected to server: http://192.168.1.100:8000
# ▶️ Running... Press CTRL+C to exit
```

---

## ⚙️ Configuration

### **File: `raspberry_face_app.py` Configuration Section**

```python
# ============================================================
# CONFIGURATION
# ============================================================

# Server Configuration
API_SERVER = "http://192.168.1.100:8000"
API_ENDPOINT = f"{API_SERVER}/query"
AUTH_TOKEN = "session_token_here"  # From login
TIMEOUT = 10  # seconds

# Camera Configuration
CAMERA_SOURCE = 0  # 0 = CSI/default, or path to USB device
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30
FRAME_SKIP = 2  # Skip frames for performance (process every 2nd)

# Display Configuration
WINDOW_NAME = "🤖 Face Recognition - Raspberry Pi"
DISPLAY_RESULT_TIME = 3  # Show result for 3 seconds
SHOW_FPS = True
SHOW_EMOTIONS = True
SHOW_DEBUG = False

# Logging Configuration
LOG_FILE = "face_recognition.log"
LOG_EMOTIONS = True
LOG_EVERY_N_FRAMES = 5

# Detection Thresholds
MIN_DETECTION_CONFIDENCE = 0.5
EMOTION_THRESHOLD = 0.3  # Only log if confidence > 30%

# Emotion Categories
NEGATIVE_EMOTIONS = ["Sad", "Fear", "Disgust", "Anger", "Contempt"]
POSITIVE_EMOTIONS = ["Happy"]
```

---

## 🔧 Main Components

### **1. Video Capture Module**

```python
class VideoCapture:
    def __init__(self, source=0, width=640, height=480, fps=30):
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        
    def read_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def release(self):
        self.cap.release()
```

**Features:**
- Multiple source support (CSI, USB, RTSP stream)
- Frame size & FPS configuration
- Error handling for camera disconnection

---

### **2. Face Detection Module**

```python
import mediapipe as mp

class FaceDetector:
    def __init__(self):
        self.mp_face = mp.solutions.face_detection
        self.detector = self.mp_face.FaceDetection(
            model_selection=1,  # 0=short range, 1=full range
            min_detection_confidence=0.5
        )
    
    def detect_faces(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector.process(rgb)
        
        faces = []
        if results.detections:
            for detection in results.detections:
                # Extract bounding box
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = frame.shape
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                faces.append({
                    'bbox': (x, y, width, height),
                    'confidence': detection.score[0]
                })
        
        return faces
```

**Performance:**
- MediaPipe is lightweight (~5ms on Pi 4B)
- GPU acceleration available on Pi 5

---

### **3. API Integration Module**

```python
class APIClient:
    def __init__(self, server_url, token, timeout=10):
        self.server_url = server_url
        self.token = token
        self.timeout = timeout
    
    def recognize_face(self, frame):
        """Send frame to server and get recognition result"""
        try:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Send to API
            files = {'file': ('frame.jpg', frame_bytes, 'image/jpeg')}
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.post(
                f"{self.server_url}/query",
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.status_code}
        
        except requests.Timeout:
            return {"error": "API timeout"}
        except Exception as e:
            return {"error": str(e)}
```

**Network Optimization:**
- JPEG compression for bandwidth
- Adaptive frame resizing based on connection
- Retry logic for failed requests

---

### **4. Result Display Module**

```python
class ResultDisplay:
    def __init__(self, window_name="Face Recognition"):
        self.window_name = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
    def display_result(self, frame, result, faces):
        """Draw results on frame"""
        display_frame = frame.copy()
        
        # Draw detected faces
        for face in faces:
            x, y, w, h = face['bbox']
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # If recognition result exists
        if 'nguoi' in result:
            person = result['nguoi']
            emotion = result.get('emotion', {})
            
            # Draw person info
            cv2.putText(display_frame, f"Name: {person['full_name']}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Draw emotion if available
            if emotion.get('emotion'):
                emotion_text = f"😊 {emotion['emotion']} ({emotion['prob']:.1%})"
                cv2.putText(display_frame, emotion_text,
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        cv2.imshow(self.window_name, display_frame)
```

---

### **5. Logging Module**

```python
class Logger:
    def __init__(self, log_file="face_recognition.log"):
        self.log_file = log_file
    
    def log_result(self, result):
        """Log recognition result to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if 'nguoi' in result:
            person = result['nguoi']
            emotion = result.get('emotion', {})
            
            log_entry = (
                f"[{timestamp}] Person: {person['full_name']} | "
                f"Score: {result['score']:.2f} | "
                f"Emotion: {emotion.get('emotion', 'N/A')}\n"
            )
        else:
            log_entry = f"[{timestamp}] No match found\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
```

---

## 🔄 Execution Flow

### **Main Loop Sequence**

```
┌────────────────────────────────┐
│ Start Application              │
└────────────┬────────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ Initialize Components:         │
│ - Camera                       │
│ - Face Detector                │
│ - API Client                   │
│ - Display                      │
└────────────┬────────────────────┘
             │
             ▼
   ┌─────────────────────────────────┐
   │ MAIN LOOP (until CTRL+C)        │
   │                                 │
   ├─ 1. Capture Frame              │
   │    └─ Read from camera         │
   │                                 │
   ├─ 2. Skip Frame Check           │
   │    └─ If skip_count > 0: skip  │
   │                                 │
   ├─ 3. Detect Faces (MediaPipe)   │
   │    └─ Get face bounding boxes  │
   │                                 │
   ├─ 4. For Each Face:             │
   │    │                            │
   │    ├─ 4a. Crop Face ROI        │
   │    │                            │
   │    ├─ 4b. Send to API          │
   │    │    POST /query            │
   │    │    (image bytes)           │
   │    │                            │
   │    ├─ 4c. Receive Result       │
   │    │    {nguoi, emotion, score}│
   │    │                            │
   │    └─ 4d. Log Result           │
   │         (to file)              │
   │                                 │
   ├─ 5. Display Results            │
   │    └─ Draw on frame            │
   │        Show person name        │
   │        Show emotion            │
   │        Show timestamp          │
   │                                 │
   ├─ 6. Show Frame                 │
   │    └─ OpenCV imshow()          │
   │                                 │
   ├─ 7. Calculate FPS              │
   │    └─ Display on screen        │
   │                                 │
   ├─ 8. Check Exit (CTRL+C)        │
   │                                 │
   └─ 9. Loop back to step 1        │
       (30 FPS / frame_skip)        │
   │                                 │
   └────────────────────────────────┘
             │
             ▼
   ┌─────────────────────────────────┐
   │ Cleanup                         │
   │ - Release camera               │
   │ - Close windows                │
   │ - Save logs                    │
   └─────────────────────────────────┘
```

---

## 🔌 API Integration

### **Step 1: Login to Get Session Token**

```bash
curl -X POST http://192.168.1.100:8000/auth/login \
  -d "username=rpi_device&password=password123"

Response:
{
  "success": true,
  "session_token": "abc123xyz..."
}
```

### **Step 2: Use Token in App**

```python
# In raspberry_face_app.py
AUTH_TOKEN = "abc123xyz..."

# Automatic inclusion in all API calls
headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
```

### **Step 3: Send Frame for Recognition**

```bash
curl -X POST http://192.168.1.100:8000/query \
  -H "Authorization: Bearer abc123xyz..." \
  -F "file=@frame.jpg"

Response:
{
  "image_id": 1001,
  "class_id": "123",
  "score": 0.95,
  "emotion": {
    "emotion": "Happy",
    "prob": 0.92
  },
  "nguoi": {
    "id": 123,
    "full_name": "Nguyễn Văn A",
    "role": "staff",
    "shift": "day"
  }
}
```

---

## 🐛 Troubleshooting

### **Issue: Camera Not Detected**

```
Error: Cannot find camera device
Solution:
1. Check camera is enabled: raspi-config > Camera > Enable
2. Verify camera is connected (CSI ribbon)
3. Test camera: raspistill -o test.jpg
4. Change CAMERA_SOURCE to 0, 1, 2... until found
```

---

### **Issue: API Connection Timeout**

```
Error: requests.exceptions.ConnectionError
Solution:
1. Check server is running: curl http://SERVER:8000/health
2. Verify network connectivity: ping 192.168.1.100
3. Check firewall: sudo ufw allow 8000/tcp
4. Increase timeout in config (default 10s)
```

---

### **Issue: Low Frame Rate / Lag**

```
Performance: <10 FPS
Solution:
1. Reduce resolution: FRAME_WIDTH=320, FRAME_HEIGHT=240
2. Skip frames: FRAME_SKIP=3
3. Disable display: cv2.imshow(...) commented
4. Use GPU acceleration: mediapipe GPU
5. Compress JPEG more: cv2.IMWRITE_JPEG_QUALITY=80
```

---

### **Issue: Out of Memory**

```
Error: MemoryError or process killed
Solution:
1. Check RAM: free -h (should be >2GB available)
2. Stop other services: sudo systemctl stop service_name
3. Reduce frame buffer: remove frame caching
4. Compress images more
5. Run on Pi 5 (8GB RAM)
```

---

## 📊 Performance Metrics

### **Typical Performance on Raspberry Pi 4B**

| Metric | Value | Notes |
|--------|-------|-------|
| Frame Capture | 30 FPS | Full HD capable |
| Face Detection | 20ms | MediaPipe LITE |
| API Call (round trip) | 200-500ms | Depends on network |
| Display | 30 FPS | Real-time |
| Overall | 2-5 FPS effective | Limited by API latency |

### **Performance on Raspberry Pi 5**

| Metric | Value | Improvement |
|--------|-------|------------|
| Face Detection | 10ms | 2x faster |
| Overall | 5-10 FPS | Better throughput |

---

## 🚀 Advanced Features

### **Option 1: Offline Fallback**
```python
# Cache recognized faces locally
# If API fails, use cached embedding
cached_faces = {}  # {embedding: person_info}
```

### **Option 2: Cloud Storage**
```python
# Upload interesting frames to cloud
# (negative emotions, new persons)
import boto3
s3 = boto3.client('s3')
s3.upload_file('frame.jpg', 'bucket', 'faces/frame.jpg')
```

### **Option 3: Alert System**
```python
# Send notification when negative emotion detected
import smtplib
send_email("Alert: Angry employee detected")
```

---

## 📚 Additional Resources

- **OpenCV Documentation:** https://docs.opencv.org/
- **MediaPipe Docs:** https://developers.google.com/mediapipe
- **Raspberry Pi GPIO:** https://www.raspberrypi.com/documentation/computers/os.html

---

**Last Updated:** December 20, 2025  
**Maintainer:** IoT Team
