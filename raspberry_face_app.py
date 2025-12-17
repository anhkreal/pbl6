import cv2
import numpy as np
import math
import time
import os
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import logging
import traceback
from typing import Optional, Dict, Any
import threading
from gtts import gTTS
from playsound import playsound
import tempfile
import warnings

# ========== IMPORT GPIO (NẾU CÓ) ==========
GPIO_AVAILABLE = True
PIGPIO_AVAILABLE = False
try:
    from gpiozero import Button, DistanceSensor
    from gpiozero.pins.pigpio import PiGPIOFactory
    PIGPIO_AVAILABLE = True
except Exception:
    try:
        from gpiozero import Button, DistanceSensor
    except Exception:
        GPIO_AVAILABLE = False

# Tắt cảnh báo DistanceSensorNoEcho để log sạch hơn
warnings.filterwarnings('ignore', message='.*no echo received.*')

# ========== SETUP LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== KHỞI TẠO TEXT-TO-SPEECH ENGINE ==========
def speak_text(text: str, is_async=True, lang='vi'):
    """
    Đọc text thông qua speaker sử dụng gTTS (Google Text-to-Speech)
    
    Args:
        text: Chuỗi cần đọc
        is_async: Nếu True, chạy trong thread riêng (không block)
        lang: Ngôn ngữ ('vi' = Tiếng Việt, 'en' = Tiếng Anh)
    """
    def _speak():
        try:
            logger.info(f"🔊 Đọc ({lang}): {text}")
            
            # Tạo gTTS object
            tts = gTTS(text, lang=lang, slow=False)
            
            # Lưu vào file tạm
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_file = fp.name
                tts.save(temp_file)
            
            # Phát âm thanh
            playsound(temp_file)
            
            # Xóa file tạm
            os.remove(temp_file)
            
        except Exception as e:
            logger.error(f"Lỗi khi đọc text: {e}")
    
    if is_async:
        # Chạy trong thread riêng để không block UI
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
    else:
        _speak()

# ========== CẤU HÌNH HỆ THỐNG ==========
BACKEND_URL = "https://51f06c3fbb4f.ngrok-free.app"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
DIST_THRESHOLD = 150  # Tăng từ 100 lên 150 để tracking ổn định hơn
CHECKIN_BUTTON_PIN = 17
CHECKOUT_BUTTON_PIN = 27
MAX_RETRY = 2
AUTO_SEND_INTERVAL = 10  # Gửi ảnh về backend mỗi 10 giây
RECOGNITION_EXPIRE_TIME = 30  # Xóa kết quả nhận diện sau 30 giây
TRACKING_STABLE_TIME = 2  # Tracking phải tồn tại ít nhất 2 giây trước khi gửi

# --- Ultrasonic sensor config (customer detector) ---
ULTRASONIC_TRIG_PIN = 5   # BCM, chân vật lý 29
ULTRASONIC_ECHO_PIN = 6   # BCM, chân vật lý 31 (qua cầu chia áp về ~3.3V)
CUSTOMER_DISTANCE_MIN_CM = 5    # Khoảng cách tối thiểu (cm)
CUSTOMER_DISTANCE_MAX_CM = 100  # Khoảng cách tối đa (cm)
CUSTOMER_DEBOUNCE_TIME = 2.0    # Delay giữa các lần thông báo (giây)
REQUIRE_CUSTOMER_FOR_AUTO_SEND = False  # TẮT để tránh lỗi sensor blocking
USE_PIGPIO_FOR_ULTRASONIC = True  # bật để ưu tiên pigpio nếu có
ULTRASONIC_MAX_DISTANCE = 1.5  # Giảm từ 2.0 xuống 1.5m
ULTRASONIC_RETRY_COUNT = 3  # Số lần thử lại khi đọc sensor

headers = {"ngrok-skip-browser-warning": "true"}

# ========== TÌM HAAR CASCADE ==========
def find_haar_cascade():
    """Tìm file haarcascade_frontalface_default.xml trong hệ thống"""
    # Thử tìm trong OpenCV data
    try:
        base = cv2.data.haarcascades
        candidate = os.path.join(base, "haarcascade_frontalface_default.xml")
        if os.path.isfile(candidate):
            return candidate
    except AttributeError:
        pass
    
    # Các vị trí thường gặp trên Linux/Raspberry Pi
    candidates = [
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv-data/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

CASCADE_PATH = find_haar_cascade()
if not CASCADE_PATH:
    print("❌ Không tìm thấy haarcascade_frontalface_default.xml")
    print("Cài đặt bằng lệnh:")
    print("  sudo apt-get install -y libopencv-dev python3-opencv")
    raise SystemExit(1)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if face_cascade.empty():
    print(f"❌ Không load được cascade tại: {CASCADE_PATH}")
    raise SystemExit(1)

logger.info(f"✓ Đã load Haar Cascade từ: {CASCADE_PATH}")

# ========== BIẾN TOÀN CỤC ==========
face_id = 0
faces = {}  # {tracking_id: (cx, cy, face_image, last_recognized_name, first_seen_time)}
current_frame_for_save = None
last_auto_send_time = 0  # Thời gian gửi ảnh tự động lần cuối
recognized_names = {}  # {tracking_id: (name, score, timestamp)}
distance_sensor: Optional[DistanceSensor] = None

# ========== HIỂN THỊ TEXT TIẾNG VIỆT ==========
def put_vn_text(img, text, pos, font_size=22, color=(255, 255, 0)):
    """
    Hiển thị text tiếng Việt trên ảnh OpenCV
    Args:
        img: Ảnh OpenCV (BGR)
        text: Chuỗi cần hiển thị
        pos: Vị trí (x, y)
        font_size: Kích thước font
        color: Màu BGR
    Returns:
        Ảnh đã vẽ text
    """
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # Thử load font tiếng Việt
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font = None
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except:
            pass
    
    if font is None:
        font = ImageFont.load_default()
    
    # Chuyển màu BGR -> RGB
    draw.text(pos, text, font=font, fill=color[::-1])
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ========== GỬI ẢNH TỰ ĐỘNG ĐỂ NHẬN DIỆN (KHÔNG LƯU DB) ==========
def auto_send_face_to_backend(face_image, tracking_id) -> Optional[Dict[str, Any]]:
    """
    Gửi ảnh khuôn mặt về backend để nhận diện (KHÔNG lưu check-in/check-out)
    
    API: /query
    - Nhận diện khuôn mặt
    - Phân tích cảm xúc
    - Log cảm xúc không tốt (Anger, Fear, Sad, Disgust, Surprise)
    - Cập nhật KPI tự động
    - KHÔNG TỰ ĐỘNG THÊM MỚI (phải thêm thủ công qua web)
    
    Args:
        face_image: Ảnh khuôn mặt đã crop
        tracking_id: ID tracking của khuôn mặt
    
    Returns:
        Dict chứa kết quả nhận diện hoặc None nếu lỗi
    """
    try:
        logger.info(f"📤 Gửi ảnh tự động về backend (Tracking ID: {tracking_id})...")
        
        # Encode ảnh thành JPEG
        _, img_encoded = cv2.imencode('.jpg', face_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        img_bytes = img_encoded.tobytes()
        
        files = {'image': ('face.jpg', img_bytes, 'image/jpeg')}
        data = {'isServing': 'false'}  # Thêm parameter isServing
        
        # ===== GỌI API /query (NHẬN DIỆN + CẢM XÚC + KPI) =====
        response = requests.post(
            f"{BACKEND_URL}/query",
            files=files,
            data=data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Kiểm tra action để xác định kết quả
            action = result.get('action', '')
            
            if action == 'face_recognized':
                # ===== ĐÃ NHẬN DIỆN ĐƯỢC =====
                full_name = result.get('full_name', 'Unknown')
                score = result.get('score', 0)
                class_id = result.get('class_id', 'N/A')
                
                # Thông tin cảm xúc (nếu có)
                emotion_data = result.get('emotion', {})
                emotion_type = emotion_data.get('emotion_type', 'unknown') if emotion_data else 'unknown'
                emotion_conf = emotion_data.get('confidence', 0) if emotion_data else 0
                
                # Lưu kết quả nhận diện vào tracking
                recognized_names[tracking_id] = (full_name, score, time.time())
                
                # Log kết quả
                logger.info(f"✓ Nhận diện: {full_name} (ID: {class_id}, Score: {score:.2f})")
                print(f"👤 ID {tracking_id}: {full_name} | Độ tin cậy: {score:.2f}")
                
                # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
                # speak_text(f"Xin chào {full_name}", is_async=True, lang='vi')
                
                if emotion_type != 'unknown':
                    print(f"😊 Cảm xúc: {emotion_type} (Độ tin cậy: {emotion_conf:.2f})")
                    # Cảnh báo nếu cảm xúc không tốt
                    not_good_emotions = ['Anger', 'Fear', 'Sad', 'Disgust', 'Surprise']
                    if emotion_type in not_good_emotions:
                        print(f"⚠️ Đã ghi log cảm xúc không tốt và cập nhật KPI")
                
                return result
                
            else:
                # Backend PBL6 không auto-add
                logger.warning(f"⚠ Không nhận diện được: {result.get('error', 'Unknown error')}")
                print(f"⚠ ID {tracking_id}: Chưa có trong hệ thống")
                # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
                # speak_text("Không nhận diện được người này, vui lòng thêm vào hệ thống", is_async=True, lang='vi')
                return None
                
        elif response.status_code == 404:
            # Không tìm thấy trong database
            logger.warning(f"⚠ Không tìm thấy khuôn mặt trong database")
            print(f"⚠ ID {tracking_id}: Không tìm thấy trong hệ thống")
            return None
        else:
            logger.warning(f"⚠ API /query trả về: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("⏱ Timeout khi gửi backend")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Không kết nối được backend")
        # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
        # speak_text("Lỗi kết nối tới hệ thống", is_async=True, lang='vi')
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi gửi ảnh: {str(e)}")
        traceback.print_exc()
        return None

# ========== GỌI API CHECK-IN ==========
def recognize_and_checkin(face_image, tracking_id) -> Optional[Dict[str, Any]]:
    """
    Gửi ảnh để CHECK-IN với đọc tên + thời gian (TIẾNG VIỆT)
    ✓ ĐỌC TEXT Ở ĐÂY
    """
    try:
        logger.info(f"📤 Gửi ảnh CHECK-IN (Tracking ID: {tracking_id})...")
        current_time = datetime.now()
        time_str = current_time.strftime("%H:%M:%S")
        
        _, img_encoded = cv2.imencode('.jpg', face_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        img_bytes = img_encoded.tobytes()
        
        files = {'image': ('face.jpg', img_bytes, 'image/jpeg')}
        
        response = requests.post(
            f"{BACKEND_URL}/query/checkin",
            files=files,
            headers=headers,
            timeout=10
        )
        
        # In kết quả đơn giản
        print(f"\n{'='*50}")
        if response.status_code == 200:
            result = response.json()
            full_name = result.get('full_name', 'Unknown')
            
            print(f"✓ CHECK-IN THÀNH CÔNG")
            print(f"  Người: {full_name}")
            print(f"  Thời gian: {time_str}")
            print(f"  Kết quả: {result.get('message', 'OK')}")
            
            # ===== ĐỌC TÊN + THỜI GIAN CHECK-IN (TIẾNG VIỆT) =====
            speak_text(f"Check in thành công. Người dùng {full_name}, lúc {time_str}", is_async=True, lang='vi')
            
        elif response.status_code == 404:
            print(f"⚠ KHÔNG NHẬN DIỆN ĐƯỢC")
            print(f"  Vui lòng thử lại")
            # ===== ĐỌC THÔNG BÁO LỖI =====
            speak_text("Không nhận diện được, vui lòng thử lại", is_async=True, lang='vi')
        else:
            print(f"✗ CHECK-IN THẤT BẠI")
            print(f"  Status: {response.status_code}")
            # ===== ĐỌC THÔNG BÁO LỖI =====
            speak_text("Check in thất bại, vui lòng thử lại", is_async=True, lang='vi')
        print(f"{'='*50}\n")
        
        return response.json() if response.status_code == 200 else None
            
    except Exception as e:
        logger.error(f"❌ Lỗi check-in: {str(e)}")
        print(f"\n❌ Lỗi khi check-in\n")
        # ===== ĐỌC THÔNG BÁO LỖI =====
        speak_text("Lỗi khi thực hiện check in", is_async=True, lang='vi')
        return None

# ========== GỌI API CHECK-OUT ==========
def recognize_and_checkout(face_image, tracking_id) -> Optional[Dict[str, Any]]:
    """
    Gửi ảnh để CHECK-OUT với đọc tên + thời gian (TIẾNG VIỆT)
    ✓ ĐỌC TEXT Ở ĐÂY
    """
    try:
        logger.info(f"📤 Gửi ảnh CHECK-OUT (Tracking ID: {tracking_id})...")
        current_time = datetime.now()
        time_str = current_time.strftime("%H:%M:%S")
        
        _, img_encoded = cv2.imencode('.jpg', face_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        img_bytes = img_encoded.tobytes()
        
        files = {'image': ('face.jpg', img_bytes, 'image/jpeg')}
        
        response = requests.post(
            f"{BACKEND_URL}/query/checkout",
            files=files,
            headers=headers,
            timeout=10
        )
        
        # In kết quả đơn giản
        print(f"\n{'='*50}")
        if response.status_code == 200:
            result = response.json()
            full_name = result.get('full_name', 'Unknown')
            
            print(f"✓ CHECK-OUT THÀNH CÔNG")
            print(f"  Người: {full_name}")
            print(f"  Thời gian: {time_str}")
            print(f"  Kết quả: {result.get('message', 'OK')}")
            
            # ===== ĐỌC TÊN + THỜI GIAN CHECK-OUT (TIẾNG VIỆT) =====
            speak_text(f"Check out thành công. Người dùng {full_name}, lúc {time_str}", is_async=True, lang='vi')
            
        elif response.status_code == 404:
            print(f"⚠ KHÔNG NHẬN DIỆN ĐƯỢC")
            print(f"  Vui lòng thử lại")
            # ===== ĐỌC THÔNG BÁO LỖI =====
            speak_text("Không nhận diện được, vui lòng thử lại", is_async=True, lang='vi')
        else:
            print(f"✗ CHECK-OUT THẤT BẠI")
            print(f"  Status: {response.status_code}")
            # ===== ĐỌC THÔNG BÁO LỖI =====
            speak_text("Check out thất bại, vui lòng thử lại", is_async=True, lang='vi')
        print(f"{'='*50}\n")
        
        return response.json() if response.status_code == 200 else None
            
    except Exception as e:
        logger.error(f"❌ Lỗi check-out: {str(e)}")
        print(f"\n❌ Lỗi khi check-out\n")
        # ===== ĐỌC THÔNG BÁO LỖI =====
        speak_text("Lỗi khi thực hiện check out", is_async=True, lang='vi')
        return None

# ========== XỬ LÝ NÚT CHECK-IN ==========
def on_checkin_pressed():
    """Callback khi nhấn nút/phím CHECK-IN"""
    try:
        logger.info("=== CHECK-IN PRESSED ===")
        print("\n🔵 Đang xử lý CHECK-IN...")
        # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
        # speak_text("Đang xử lý check in", is_async=True, lang='vi')
        
        # Tìm khuôn mặt có ảnh lớn nhất
        faces_with_images = [(fid, f) for fid, f in faces.items() 
                             if len(f) > 2 and f[2] is not None]
        
        if faces_with_images:
            faces_with_images.sort(key=lambda x: x[1][2].size, reverse=True)
            best_face_id, best_face = faces_with_images[0]
            face_img = best_face[2]
            
            # Gửi ảnh đến backend (backend tự xử lý tất cả)
            recognize_and_checkin(face_img, best_face_id)
        else:
            print("⚠ Không có khuôn mặt nào!")
            print("Vui lòng đứng trước camera\n")
            # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
            # speak_text("Không phát hiện khuôn mặt, vui lòng đứng trước camera", is_async=True, lang='vi')
    except Exception as e:
        logger.error(f"❌ Lỗi: {str(e)}")
        print("\n❌ Lỗi khi check-in\n")
        # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
        # speak_text("Lỗi xảy ra, vui lòng thử lại", is_async=True, lang='vi')

# ========== XỬ LÝ NÚT CHECK-OUT ==========
def on_checkout_pressed():
    """Callback khi nhấn nút/phím CHECK-OUT"""
    try:
        logger.info("=== CHECK-OUT PRESSED ===")
        print("\n🔴 Đang xử lý CHECK-OUT...")
        # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
        # speak_text("Đang xử lý check out", is_async=True, lang='vi')
        
        # Tìm khuôn mặt có ảnh lớn nhất
        faces_with_images = [(fid, f) for fid, f in faces.items() 
                             if len(f) > 2 and f[2] is not None]
        
        if faces_with_images:
            faces_with_images.sort(key=lambda x: x[1][2].size, reverse=True)
            best_face_id, best_face = faces_with_images[0]
            face_img = best_face[2]
            
            # Gửi ảnh đến backend (backend tự xử lý tất cả)
            recognize_and_checkout(face_img, best_face_id)
        else:
            print("⚠ Không có khuôn mặt nào!")
            print("Vui lòng đứng trước camera\n")
            # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
            # speak_text("Không phát hiện khuôn mặt, vui lòng đứng trước camera", is_async=True, lang='vi')
    except Exception as e:
        logger.error(f"❌ Lỗi: {str(e)}")
        print("\n❌ Lỗi khi check-out\n")
        # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
        # speak_text("Lỗi xảy ra, vui lòng thử lại", is_async=True, lang='vi')

# ========== KHỞI TẠO NÚT GPIO ==========
checkin_button = None
checkout_button = None

if GPIO_AVAILABLE:
    try:
        checkin_button = Button(CHECKIN_BUTTON_PIN, pull_up=True, bounce_time=0.2)
        checkout_button = Button(CHECKOUT_BUTTON_PIN, pull_up=True, bounce_time=0.2)
        checkin_button.when_pressed = on_checkin_pressed
        checkout_button.when_pressed = on_checkout_pressed
        logger.info(f"✓ GPIO nút CHECK-IN: Pin {CHECKIN_BUTTON_PIN}")
        logger.info(f"✓ GPIO nút CHECK-OUT: Pin {CHECKOUT_BUTTON_PIN}")
        print(f"✓ GPIO nút CHECK-IN: Pin {CHECKIN_BUTTON_PIN}")
        print(f"✓ GPIO nút CHECK-OUT: Pin {CHECKOUT_BUTTON_PIN}")
    except Exception as e:
        logger.error(f"✗ Lỗi khởi tạo GPIO: {e}")
        print(f"✗ Lỗi GPIO: {e}")
        checkin_button = None
        checkout_button = None
else:
    logger.info("ℹ Không có gpiozero. Dùng phím i/o thay thế.")
    print("ℹ Không có gpiozero. Dùng phím i/o thay thế.")

# ========== KIỂM TRA SỰ HIỆN DIỆN CỦA KHÁCH HÀNG (CẢI TIẾN) ==========
def is_customer_present() -> bool:
    """
    Trả về True khi cảm biến phát hiện khách trong khoảng cách 5cm - 100cm.
    Cải tiến: Retry nhiều lần để tránh lỗi NoEcho ngẫu nhiên
    """
    if distance_sensor is None:
        return not REQUIRE_CUSTOMER_FOR_AUTO_SEND
    
    # Thử đọc nhiều lần để tránh lỗi NoEcho ngẫu nhiên
    for attempt in range(ULTRASONIC_RETRY_COUNT):
        try:
            dist_cm = distance_sensor.distance * 100
            # Kiểm tra trong vùng 5cm - 100cm
            present = (CUSTOMER_DISTANCE_MIN_CM <= dist_cm <= CUSTOMER_DISTANCE_MAX_CM)
            return present
        except Exception as e:
            if attempt < ULTRASONIC_RETRY_COUNT - 1:
                # Retry với delay nhỏ
                time.sleep(0.05)
                continue
            else:
                # Lần cuối vẫn lỗi -> cho phép tiếp tục
                return not REQUIRE_CUSTOMER_FOR_AUTO_SEND

# ========== KHỞI TẠO CẢM BIẾN SIÊU ÂM (CẢI TIẾN) ==========
def init_distance_sensor():
    """
    Khởi tạo cảm biến siêu âm với các cải tiến:
    - Giảm max_distance xuống 1.5m
    - Thêm threshold_distance và partial
    - Ưu tiên dùng pigpio nếu có
    """
    global distance_sensor
    if not GPIO_AVAILABLE:
        logger.info("Không có gpiozero -> bỏ qua cảm biến siêu âm.")
        print("❌ Không có gpiozero, cảm biến siêu âm KHÔNG hoạt động.")
        return
    
    try:
        pin_factory = None
        if USE_PIGPIO_FOR_ULTRASONIC and PIGPIO_AVAILABLE:
            try:
                pin_factory = PiGPIOFactory()
                logger.info("Dùng PiGPIOFactory cho cảm biến siêu âm.")
            except Exception as e:
                logger.warning(f"Không khởi tạo được PiGPIOFactory, fallback GPIO mặc định: {e}")
                pin_factory = None
        
        # Khởi tạo với các tham số cải tiến
        distance_sensor = DistanceSensor(
            echo=ULTRASONIC_ECHO_PIN,
            trigger=ULTRASONIC_TRIG_PIN,
            max_distance=ULTRASONIC_MAX_DISTANCE,  # Giảm từ 2.0 xuống 1.5m
            queue_len=5,  # Tăng từ 3 lên 5 để lọc nhiễu tốt hơn
            threshold_distance=0.3,  # Thêm threshold để lọc giá trị
            partial=True,  # Cho phép đọc không hoàn chỉnh
            pin_factory=pin_factory
        )
        logger.info(f"✓ Cảm biến siêu âm sẵn sàng (Trig {ULTRASONIC_TRIG_PIN}, Echo {ULTRASONIC_ECHO_PIN})")
        print(f"✓ Cảm biến siêu âm HOẠT ĐỘNG: Trig {ULTRASONIC_TRIG_PIN}, Echo {ULTRASONIC_ECHO_PIN}, vùng {CUSTOMER_DISTANCE_MIN_CM}-{CUSTOMER_DISTANCE_MAX_CM}cm")
        if pin_factory:
            print("↪ Đang dùng pigpio để đo Echo (ổn định hơn).")
        else:
            print("↪ Đang dùng GPIO mặc định (nếu lỗi NoEcho, hãy bật pigpio).")
    except Exception as e:
        distance_sensor = None
        logger.error(f"✗ Lỗi khởi tạo cảm biến siêu âm: {e}")
        print(f"❌ Cảm biến siêu âm KHÔNG hoạt động: {e}")

# ========== ĐẢM BẢO XDG_RUNTIME_DIR ==========
def ensure_runtime_dir():
    """Đảm bảo XDG_RUNTIME_DIR tồn tại và có quyền 0700 để tránh cảnh báo QStandardPaths."""
    path = os.environ.get("XDG_RUNTIME_DIR") or "/tmp/xdg-runtime"
    try:
        os.makedirs(path, exist_ok=True)
        os.chmod(path, 0o700)
        os.environ["XDG_RUNTIME_DIR"] = path
    except Exception as e:
        logger.warning(f"Không thiết lập được XDG_RUNTIME_DIR: {e}")

# ========== MAIN LOOP ==========
def main():
    """Chương trình chính"""
    global face_id, faces, current_frame_for_save, last_auto_send_time, recognized_names

    ensure_runtime_dir()
    logger.info("Khởi động hệ thống nhận diện khuôn mặt...")

    # Mở camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    if not cap.isOpened():
        logger.error("Không mở được camera")
        print("✗ Không mở được camera")
        print("Kiểm tra:")
        print("  - Camera đã kết nối chưa?")
        print("  - Đã enable camera trong raspi-config chưa?")
        print("  - Thử lệnh: raspistill -o test.jpg")
        speak_text("Lỗi, không thể mở camera", is_async=True)
        return

    # Khởi tạo cảm biến siêu âm (khách hàng)
    init_distance_sensor()

    # In thông tin hệ thống
    print("\n" + "="*60)
    print("🎥 RASPBERRY FACE RECOGNITION - KPI MODE WITH TEXT-TO-SPEECH")
    print("="*60)
    print(f"Backend: {BACKEND_URL}")
    print(f"Camera: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    print(f"Auto send interval: {AUTO_SEND_INTERVAL}s (gửi ảnh tự động)")
    print(f"Tracking threshold: {DIST_THRESHOLD}px (khoảng cách tối đa)")
    print(f"Phím: i (Check-in) | o (Check-out) | ESC (Thoát)")
    if GPIO_AVAILABLE and checkin_button and checkout_button:
        print(f"GPIO: Pin {CHECKIN_BUTTON_PIN} (Check-in) | Pin {CHECKOUT_BUTTON_PIN} (Check-out)")
    if distance_sensor:
        print(f"Cảm biến khách: BẬT (vùng {CUSTOMER_DISTANCE_MIN_CM}-{CUSTOMER_DISTANCE_MAX_CM}cm)")
    else:
        print("Cảm biến khách: TẮT (auto-send sẽ không bị chặn)")
    print("="*60)
    print("\n💡 Tính năng:")
    print("  ✓ Nhận diện khuôn mặt tự động")
    print("  ✓ Phân tích cảm xúc real-time")
    print("  ✓ Đọc tên + thời gian khi check-in/check-out")
    print("="*60 + "\n")

    # Vòng lặp chính
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Không đọc được frame từ camera")
            print("✗ Không đọc được frame từ camera")
            break

        current_frame_for_save = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Lấy timestamp hiện tại (dùng chung cho toàn bộ frame)
        current_time_sec = time.time()

        # ===== PHÁT HIỆN KHUÔN MẶT BẰNG HAAR CASCADE =====
        rects = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        face_count = len(rects)
        new_faces = {}
        current_time = time.time()

        # ===== TRACKING KHUÔN MẶT (CẢI TIẾN) =====
        for (x, y, w, h) in rects:
            cx = x + w // 2
            cy = y + h // 2

            # Crop ảnh khuôn mặt
            face_img = frame[y:y+h, x:x+w].copy()

            # Tìm khuôn mặt gần nhất trong tracking
            matched_id = None
            min_dist = DIST_THRESHOLD

            for fid, face_data in faces.items():
                old_cx, old_cy = face_data[0], face_data[1]
                dist = math.sqrt((cx - old_cx)**2 + (cy - old_cy)**2)
                if dist < min_dist:
                    min_dist = dist
                    matched_id = fid

            if matched_id is None:
                # Khuôn mặt mới - tạo ID mới
                face_id += 1
                matched_id = face_id
                first_seen_time = current_time
                logger.info(f"✨ Phát hiện khuôn mặt mới: ID {matched_id}")
            else:
                # Khuôn mặt đã tồn tại - giữ nguyên first_seen_time
                first_seen_time = faces[matched_id][4] if len(faces[matched_id]) > 4 else current_time

            # Lấy tên đã nhận diện (nếu có)
            recognized_name = None
            if matched_id in recognized_names:
                recognized_name, score, timestamp = recognized_names[matched_id]
                # Xóa nếu quá cũ
                if current_time - timestamp > RECOGNITION_EXPIRE_TIME:
                    del recognized_names[matched_id]
                    recognized_name = None

            # Lưu tracking (thêm first_seen_time)
            new_faces[matched_id] = (cx, cy, face_img, recognized_name, first_seen_time)

            # Vẽ khung và thông tin lên frame
            tracking_age = current_time - first_seen_time
            
            if recognized_name:
                color = (0, 255, 0)  # Xanh lá = đã nhận diện
                label = f"ID {matched_id}: {recognized_name}"
            else:
                if tracking_age < TRACKING_STABLE_TIME:
                    color = (255, 165, 0)  # Cam = đang tracking
                    label = f"ID {matched_id}: Tracking... ({tracking_age:.1f}s)"
                else:
                    color = (0, 0, 255)  # Đỏ = chưa nhận diện
                    label = f"ID {matched_id}: Ready"

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            frame = put_vn_text(frame, label, (x, y - 10), 18, color)

        faces = new_faces

        # ===== LOGIC GỬI ẢNH TỰ ĐỘNG MỖI 10 GIÂY =====
        if (current_time_sec - last_auto_send_time) >= AUTO_SEND_INTERVAL:
            if faces:
                # Lọc khuôn mặt đã tracking ổn định (>2 giây)
                stable_faces = [(fid, f) for fid, f in faces.items() 
                               if len(f) > 4 and (current_time_sec - f[4]) >= TRACKING_STABLE_TIME
                               and f[2] is not None]
                
                if stable_faces:
                    # Sắp xếp theo kích thước ảnh (lớn nhất = gần nhất)
                    stable_faces.sort(key=lambda x: x[1][2].size, reverse=True)
                    best_face_id, best_face_data = stable_faces[0]
                    best_face_img = best_face_data[2]
                    tracking_age = current_time_sec - best_face_data[4]
                    
                    # Gửi ảnh về backend để nhận diện (không lưu check-in/out)
                    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Gửi ảnh tự động...")
                    print(f"   Tracking ID {best_face_id} (đã tracking {tracking_age:.1f}s)")
                    auto_send_face_to_backend(best_face_img, best_face_id)
                else:
                    logger.debug("Không có khuôn mặt nào đủ ổn định để gửi")
            else:
                logger.debug("Không có khuôn mặt để gửi")
            
            last_auto_send_time = current_time_sec

        # ===== HIỂN THỊ THÔNG TIN TRÊN FRAME =====
        # Số lượng khuôn mặt
        frame = put_vn_text(frame, f"Khuôn mặt: {face_count}", (10, 30), 22, (0, 255, 255))
        
        # Thời gian đến lần gửi tiếp theo
        time_until_next_send = AUTO_SEND_INTERVAL - (current_time_sec - last_auto_send_time)
        if time_until_next_send > 0:
            frame = put_vn_text(
                frame, 
                f"Gửi sau: {int(time_until_next_send)}s", 
                (10, 60), 
                18, 
                (200, 200, 200)
            )
        
        # Hiển thị hướng dẫn
        frame = put_vn_text(
            frame,
            "i: Check-in | o: Check-out | ESC: Thoát",
            (10, frame.shape[0] - 20),
            16,
            (255, 255, 255)
        )

        cv2.imshow("Raspberry Face Recognition", frame)

        # ===== XỬ LÝ PHÍM BẤM =====
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            logger.info("Nhận phím ESC - Thoát chương trình")
            print("\n👋 Đang thoát chương trình...")
            # ===== KHÔNG ĐỌC TEXT (TẮT TÍNH NĂNG NÀY) =====
            # speak_text("Đang thoát chương trình", is_async=True, lang='vi')
            break
        elif key == ord('i') or key == ord('I'):  # Check-in
            on_checkin_pressed()
        elif key == ord('o') or key == ord('O'):  # Check-out
            on_checkout_pressed()

    # Dọn dẹp
    cap.release()
    cv2.destroyAllWindows()
    logger.info("Hệ thống đã dừng")
    print("\n✓ Hệ thống đã dừng")

# ========== ENTRY POINT ==========
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Nhận Ctrl+C - Đang dừng...")
        logger.info("Dừng bởi Ctrl+C")
    except Exception as e:
        logger.error(f"Lỗi không mong đợi: {str(e)}")
        print(f"\n❌ Lỗi: {str(e)}")
        traceback.print_exc()