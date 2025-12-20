"""
Hệ thống nhận diện khuôn mặt Raspberry Pi - DUAL CAMERA
- Webcam: Nhận diện nhân viên
- Pi Camera: Phát hiện khách hàng (motion detection)
"""
import cv2
import math
import time
import logging
import warnings
from datetime import datetime

# Import modules
from modules.config import *
from modules.utils import put_vn_text, find_haar_cascade, ensure_runtime_dir
from modules.checkin_checkout import recognize_and_checkin, recognize_and_checkout
from modules.customer_detector import CustomerDetector
from modules.face_recognition import auto_send_face_to_backend

# Import GPIO (nếu có)
GPIO_AVAILABLE = True
try:
    from gpiozero import Button
except Exception:
    GPIO_AVAILABLE = False

warnings.filterwarnings('ignore')

# ========== SETUP LOGGING ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== LOAD HAAR CASCADE ==========
CASCADE_PATH = find_haar_cascade(CASCADE_CANDIDATES)
if not CASCADE_PATH:
    print("❌ Không tìm thấy haarcascade_frontalface_default.xml")
    raise SystemExit(1)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if face_cascade.empty():
    print(f"❌ Không load được cascade")
    raise SystemExit(1)

logger.info(f"✓ Đã load Haar Cascade từ: {CASCADE_PATH}")

# ========== BIẾN TOÀN CỤC ==========
face_id = 0
faces = {}
recognized_names = {}
last_auto_send_time = 0

# Khởi tạo customer detector
customer_detector = CustomerDetector()

# ========== XỬ LÝ NÚT ==========
def on_checkin_pressed():
    """Callback check-in"""
    try:
        logger.info("=== CHECK-IN PRESSED ===")
        print("\n🔵 Đang xử lý CHECK-IN...")
        time.sleep(0.5)
        
        faces_with_images = [(fid, f) for fid, f in faces.items() if len(f) > 2 and f[2] is not None]
        
        if faces_with_images:
            faces_with_images.sort(key=lambda x: x[1][2].size, reverse=True)
            best_face_id, best_face = faces_with_images[0]
            face_img = best_face[2]
            
            h, w = face_img.shape[:2]
            logger.info(f"   📸 Khuôn mặt ID {best_face_id}: {w}x{h} pixels")
            
            recognize_and_checkin(face_img, best_face_id, recognized_names)
        else:
            print("⚠ Không có khuôn mặt!")
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")

def on_checkout_pressed():
    """Callback check-out"""
    try:
        logger.info("=== CHECK-OUT PRESSED ===")
        print("\n🔴 Đang xử lý CHECK-OUT...")
        time.sleep(0.5)
        
        faces_with_images = [(fid, f) for fid, f in faces.items() if len(f) > 2 and f[2] is not None]
        
        if faces_with_images:
            faces_with_images.sort(key=lambda x: x[1][2].size, reverse=True)
            best_face_id, best_face = faces_with_images[0]
            face_img = best_face[2]
            
            recognize_and_checkout(face_img, best_face_id, recognized_names)
        else:
            print("⚠ Không có khuôn mặt!")
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")

# ========== KHỞI TẠO GPIO ==========
checkin_button = None
checkout_button = None

if GPIO_AVAILABLE:
    try:
        checkin_button = Button(CHECKIN_BUTTON_PIN, pull_up=True, bounce_time=0.2)
        checkout_button = Button(CHECKOUT_BUTTON_PIN, pull_up=True, bounce_time=0.2)
        checkin_button.when_pressed = on_checkin_pressed
        checkout_button.when_pressed = on_checkout_pressed
        logger.info(f"✓ GPIO: Pin {CHECKIN_BUTTON_PIN} (Check-in) | Pin {CHECKOUT_BUTTON_PIN} (Check-out)")
    except Exception as e:
        logger.error(f"✗ Lỗi GPIO: {e}")
else:
    logger.info("ℹ Dùng phím i/o thay thế GPIO")

# ========== MAIN LOOP ==========
def main():
    """Vòng lặp chính"""
    global face_id, faces, last_auto_send_time, recognized_names
    
    ensure_runtime_dir()
    logger.info("Khởi động hệ thống...")
    
    # Khởi động customer detector
    customer_detector.start()
    
    # Mở webcam
    cap = cv2.VideoCapture(EMPLOYEE_CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, EMPLOYEE_CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, EMPLOYEE_CAMERA_HEIGHT)
    
    if not cap.isOpened():
        logger.error("Không mở được Webcam")
        customer_detector.stop()
        return
    
    # In thông tin
    print("\n" + "="*60)
    print("🎥 RASPBERRY DUAL-CAMERA FACE RECOGNITION")
    print("="*60)
    print(f"Backend: {BACKEND_URL}")
    print(f"📷 Employee Camera: {EMPLOYEE_CAMERA_WIDTH}x{EMPLOYEE_CAMERA_HEIGHT} (index {EMPLOYEE_CAMERA_INDEX})")
    print(f"📷 Customer Camera: {CUSTOMER_CAMERA_WIDTH}x{CUSTOMER_CAMERA_HEIGHT} (index {CUSTOMER_CAMERA_INDEX})")
    print(f"Auto send: {AUTO_SEND_INTERVAL}s")
    print(f"Phím: i (Check-in) | o (Check-out) | ESC (Thoát)")
    print("="*60 + "\n")
    
    # Vòng lặp
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_time = time.time()
        
        # Phát hiện khuôn mặt
        rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        new_faces = {}
        
        # Tracking
        for (x, y, w, h) in rects:
            cx, cy = x + w // 2, y + h // 2
            face_img = frame[y:y+h, x:x+w].copy()
            
            matched_id = None
            min_dist = DIST_THRESHOLD
            
            for fid, face_data in faces.items():
                old_cx, old_cy = face_data[0], face_data[1]
                dist = math.sqrt((cx - old_cx)**2 + (cy - old_cy)**2)
                if dist < min_dist:
                    min_dist = dist
                    matched_id = fid
            
            if matched_id is None:
                face_id += 1
                matched_id = face_id
                first_seen_time = current_time
            else:
                first_seen_time = faces[matched_id][4] if len(faces[matched_id]) > 4 else current_time
            
            recognized_name = None
            if matched_id in recognized_names:
                recognized_name, score, timestamp = recognized_names[matched_id]
                if current_time - timestamp > RECOGNITION_EXPIRE_TIME:
                    del recognized_names[matched_id]
                    recognized_name = None
            
            new_faces[matched_id] = (cx, cy, face_img, recognized_name, first_seen_time)
            
            tracking_age = current_time - first_seen_time
            
            if recognized_name:
                color = (0, 255, 0)
                label = f"ID {matched_id}: {recognized_name}"
            else:
                if tracking_age < TRACKING_STABLE_TIME:
                    color = (255, 165, 0)
                    label = f"ID {matched_id}: Tracking... ({tracking_age:.1f}s)"
                else:
                    color = (0, 0, 255)
                    label = f"ID {matched_id}: Ready"
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            frame = put_vn_text(frame, label, (x, y - 10), 18, color)
        
        faces = new_faces
        
        # ===== AUTO-SEND VỚI CHẾ ĐỘ isServing =====
        if (current_time - last_auto_send_time) >= AUTO_SEND_INTERVAL:
            # Kiểm tra có khách không
            has_customer = customer_detector.is_customer_present()
            
            # ===== LỰA CHỌN 1: CHỈ GỬI KHI CÓ KHÁCH (GIỮ NGUYÊN LOGIC CŨ) =====
            # if has_customer:
            #     if faces:
            #         stable_faces = [...]
            #         if stable_faces:
            #             auto_send_face_to_backend(..., is_serving=True)
            
            # ===== LỰA CHỌN 2: GỬI MỌI LÚC (CÓ VÀ KHÔNG CÓ KHÁCH) =====
            if faces:
                stable_faces = [(fid, f) for fid, f in faces.items()
                               if len(f) > 4 and (current_time - f[4]) >= TRACKING_STABLE_TIME and f[2] is not None]
                
                if stable_faces:
                    stable_faces.sort(key=lambda x: x[1][2].size, reverse=True)
                    best_face_id, best_face_data = stable_faces[0]
                    best_face_img = best_face_data[2]
                    
                    # Gửi với isServing tùy vào có khách hay không
                    status_msg = "CÓ KHÁCH" if has_customer else "KHÔNG CÓ KHÁCH"
                    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Gửi ảnh ({status_msg})...")
                    auto_send_face_to_backend(best_face_img, best_face_id, recognized_names, is_serving=has_customer)
            
            last_auto_send_time = current_time
        
        # Hiển thị thông tin
        frame = put_vn_text(frame, f"Nhân viên: {len(faces)}", (10, 30), 22, (0, 255, 255))
        
        customer_status = "CÓ KHÁCH ✓" if customer_detector.is_customer_present() else "KHÔNG CÓ KHÁCH"
        customer_color = (0, 255, 0) if customer_detector.is_customer_present() else (128, 128, 128)
        frame = put_vn_text(frame, f"Khách: {customer_status}", (10, 60), 22, customer_color)
        
        time_until_next = AUTO_SEND_INTERVAL - (current_time - last_auto_send_time)
        if time_until_next > 0:
            frame = put_vn_text(frame, f"Gửi sau: {int(time_until_next)}s", (10, 90), 18, (200, 200, 200))
        
        cv2.imshow("Employee Recognition (Webcam)", frame)
        
        # Xử lý phím
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord('i'):
            on_checkin_pressed()
        elif key == ord('o'):
            on_checkout_pressed()
    
    # Cleanup
    customer_detector.stop()
    cap.release()
    cv2.destroyAllWindows()
    logger.info("Hệ thống đã dừng")

# ========== ENTRY POINT ==========
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Đang dừng...")
        customer_detector.stop()
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        customer_detector.stop()