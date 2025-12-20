"""
Nhận diện khuôn mặt và gửi về backend
"""
import cv2
import time
import logging
import requests
from typing import Optional, Dict, Any
from .utils import prepare_face_image
from .config import BACKEND_URL, HEADERS

logger = logging.getLogger(__name__)

def auto_send_face_to_backend(face_image, tracking_id, recognized_names, is_serving=False):
    """
    Gửi ảnh về backend mỗi 10 giây để:
    - Nhận diện khuôn mặt
    - Phân tích cảm xúc
    - Cập nhật KPI (nếu cảm xúc không tốt)
    
    Args:
        face_image: Ảnh khuôn mặt đã crop
        tracking_id: ID tracking của khuôn mặt
        recognized_names: Cache tên đã nhận diện
        is_serving: True = đang phục vụ khách (trừ 5 điểm)
                    False = không phục vụ (trừ 2 điểm)
    """
    try:
        logger.info(f"📤 AUTO-SEND (ID: {tracking_id}, isServing: {is_serving})...")
        print(f"\n{'='*60}")
        print(f"📤 AUTO-SEND - Tracking ID: {tracking_id}")
        print(f"   🎯 Chế độ: {'ĐANG PHỤC VỤ KHÁCH' if is_serving else 'KHÔNG PHỤC VỤ KHÁCH'}")
        
        # Chuẩn hóa ảnh
        prepared_img = prepare_face_image(face_image, target_size=512, margin_percent=0.5)
        _, img_encoded = cv2.imencode('.jpg', prepared_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        img_bytes = img_encoded.tobytes()
        
        logger.info(f"📦 File size: {len(img_bytes) / 1024:.1f} KB")
        print(f"{'='*60}\n")
        
        files = {'image': ('face.jpg', img_bytes, 'image/jpeg')}
        data = {'isServing': 'true' if is_serving else 'false'}  # ← THAY ĐỔI ĐƠN GIẢN
        
        response = requests.post(f"{BACKEND_URL}/query", files=files, data=data, headers=HEADERS, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            action = result.get('action', '')
            
            if action == 'face_recognized':
                full_name = result.get('full_name', 'Unknown')
                score = result.get('score', 0)
                class_id = result.get('class_id', 'N/A')
                
                # Lưu cache
                recognized_names[tracking_id] = (full_name, score, time.time())
                
                logger.info(f"✓ Nhận diện: {full_name} (ID: {class_id}, Score: {score:.2f})")
                print(f"👤 ID {tracking_id}: {full_name} | Độ tin cậy: {score:.2f}")
                
                # Kiểm tra cảm xúc
                emotion_data = result.get('emotion', {})
                emotion_type = emotion_data.get('emotion_type', 'unknown') if emotion_data else 'unknown'
                
                if emotion_type != 'unknown':
                    emotion_conf = emotion_data.get('confidence', 0)
                    print(f"😊 Cảm xúc: {emotion_type} (Độ tin cậy: {emotion_conf:.2f})")
                    
                    not_good_emotions = ['Anger', 'Fear', 'Sad', 'Disgust', 'Surprise']
                    if emotion_type in not_good_emotions:
                        penalty = 5 if is_serving else 2
                        print(f"⚠️ Cảm xúc không tốt → Backend trừ {penalty} điểm KPI")
                
                return result
            else:
                logger.warning(f"⚠ Không nhận diện được")
                print(f"⚠ ID {tracking_id}: Chưa có trong hệ thống")
                return None
        elif response.status_code == 404:
            logger.warning(f"⚠ Không tìm thấy trong database")
            return None
        else:
            logger.warning(f"⚠ API trả về: {response.status_code}")
            return None
    
    except requests.exceptions.Timeout:
        logger.error("⏱ Timeout")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Không kết nối được backend")
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        return None
