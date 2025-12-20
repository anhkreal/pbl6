"""
Cấu hình toàn hệ thống
"""

# ========== BACKEND CONFIG ==========
BACKEND_URL = "https://51f06c3fbb4f.ngrok-free.app"
HEADERS = {"ngrok-skip-browser-warning": "true"}

# ========== WEBCAM CONFIG (Nhân viên) ==========
EMPLOYEE_CAMERA_INDEX = 0
EMPLOYEE_CAMERA_WIDTH = 640
EMPLOYEE_CAMERA_HEIGHT = 480

# ========== PI CAMERA CONFIG (Khách hàng) ==========
# ===== THAY ĐỔI CAMERA CONFIG =====
# Thay vì dùng Pi Camera (index 1), dùng Webcam USB thứ 2
CUSTOMER_CAMERA_INDEX = 1  # Webcam USB thứ 2 (không phải Pi Camera)
CUSTOMER_CAMERA_WIDTH = 640
CUSTOMER_CAMERA_HEIGHT = 480
CUSTOMER_DETECTION_INTERVAL = 0.5  # seconds

# ========== MOTION DETECTION CONFIG ==========
MOTION_THRESHOLD = 1000  # pixels
MOTION_MIN_AREA = 500    # pixels²
NO_MOTION_TIMEOUT = 5.0  # seconds

# ========== TRACKING CONFIG ==========
DIST_THRESHOLD = 150            # pixels
AUTO_SEND_INTERVAL = 10         # seconds
RECOGNITION_EXPIRE_TIME = 30    # seconds
TRACKING_STABLE_TIME = 2        # seconds

# ========== GPIO CONFIG ==========
CHECKIN_BUTTON_PIN = 17   # BCM
CHECKOUT_BUTTON_PIN = 27  # BCM

# ========== HAAR CASCADE CONFIG ==========
CASCADE_CANDIDATES = [
    "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
    "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
    "/usr/share/opencv-data/haarcascades/haarcascade_frontalface_default.xml",
    "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
]
