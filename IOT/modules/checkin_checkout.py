"""
Xử lý check-in/check-out với backend
"""
import cv2
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from .utils import prepare_face_image, speak_text
from .config import BACKEND_URL, HEADERS

logger = logging.getLogger(__name__)

# ========== CHECK-IN ==========
def recognize_and_checkin(face_image, tracking_id, recognized_names) -> Optional[Dict[str, Any]]:
    """Gửi ảnh để CHECK-IN"""
    try:
        logger.info(f"📤 CHECK-IN (Tracking ID: {tracking_id})...")
        print(f"\n{'='*60}")
        print(f"🔵 CHECK-IN - Tracking ID: {tracking_id}")
        
        # Múi giờ Việt Nam
        tz_vn = timezone(timedelta(hours=7))
        current_time = datetime.now(tz_vn)
        time_str = current_time.strftime("%H:%M:%S")
        
        # Lấy tên từ cache
        recognized_name = None
        if tracking_id in recognized_names:
            recognized_name, score, timestamp = recognized_names[tracking_id]
            logger.info(f"✓ Tên từ tracking: {recognized_name}")
        
        # Chuẩn hóa ảnh
        prepared_img = prepare_face_image(face_image, target_size=512, margin_percent=0.5)
        _, img_encoded = cv2.imencode('.jpg', prepared_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        img_bytes = img_encoded.tobytes()
        
        files = {'image': ('face.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(f"{BACKEND_URL}/query/checkin", files=files, headers=HEADERS, timeout=10)
        
        print(f"\n{'='*50}")
        if response.status_code == 200:
            result = response.json()
            final_name = recognized_name if recognized_name else result.get('full_name', 'Unknown')
            
            print(f"✓ CHECK-IN THÀNH CÔNG")
            print(f"  Người: {final_name}")
            print(f"  Thời gian: {time_str} (GMT+7)")
            
            speak_text(f"Check in thành công. Người dùng {final_name}, lúc {time_str}", lang='vi')
        elif response.status_code == 404:
            if recognized_name:
                speak_text(f"Check in thành công. Người dùng {recognized_name}, lúc {time_str}", lang='vi')
            else:
                print(f"⚠ KHÔNG NHẬN DIỆN ĐƯỢC")
                speak_text("Không nhận diện được, vui lòng thử lại", lang='vi')
        else:
            print(f"✗ CHECK-IN THẤT BẠI (Status: {response.status_code})")
            speak_text("Check in thất bại, vui lòng thử lại", lang='vi')
        print(f"{'='*50}\n")
        
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"❌ Lỗi check-in: {e}")
        speak_text("Lỗi khi thực hiện check in", lang='vi')
        return None

# ========== CHECK-OUT ==========
def recognize_and_checkout(face_image, tracking_id, recognized_names) -> Optional[Dict[str, Any]]:
    """Gửi ảnh để CHECK-OUT"""
    try:
        logger.info(f"📤 CHECK-OUT (Tracking ID: {tracking_id})...")
        print(f"\n{'='*60}")
        print(f"🔴 CHECK-OUT - Tracking ID: {tracking_id}")
        
        tz_vn = timezone(timedelta(hours=7))
        current_time = datetime.now(tz_vn)
        time_str = current_time.strftime("%H:%M:%S")
        
        recognized_name = None
        if tracking_id in recognized_names:
            recognized_name, score, timestamp = recognized_names[tracking_id]
        
        prepared_img = prepare_face_image(face_image, target_size=512, margin_percent=0.5)
        _, img_encoded = cv2.imencode('.jpg', prepared_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        img_bytes = img_encoded.tobytes()
        
        files = {'image': ('face.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(f"{BACKEND_URL}/query/checkout", files=files, headers=HEADERS, timeout=10)
        
        print(f"\n{'='*50}")
        if response.status_code == 200:
            result = response.json()
            final_name = recognized_name if recognized_name else result.get('full_name', 'Unknown')
            
            print(f"✓ CHECK-OUT THÀNH CÔNG")
            print(f"  Người: {final_name}")
            print(f"  Thời gian: {time_str} (GMT+7)")
            
            speak_text(f"Check out thành công. Người dùng {final_name}, lúc {time_str}", lang='vi')
        elif response.status_code == 404:
            if recognized_name:
                speak_text(f"Check out thành công. Người dùng {recognized_name}, lúc {time_str}", lang='vi')
            else:
                speak_text("Không nhận diện được, vui lòng thử lại", lang='vi')
        else:
            speak_text("Check out thất bại, vui lòng thử lại", lang='vi')
        print(f"{'='*50}\n")
        
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"❌ Lỗi check-out: {e}")
        speak_text("Lỗi khi thực hiện check out", lang='vi')
        return None
