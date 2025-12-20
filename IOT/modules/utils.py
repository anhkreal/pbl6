"""
Các hàm tiện ích: TTS, chuẩn hóa ảnh, hiển thị text tiếng Việt
"""
import cv2
import numpy as np
import os
import logging
import traceback
import threading
import tempfile
from gtts import gTTS
from playsound import playsound
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ========== TEXT-TO-SPEECH ==========
def speak_text(text: str, is_async=True, lang='vi'):
    """Đọc text qua speaker (gTTS)"""
    def _speak():
        try:
            logger.info(f"🔊 Đọc ({lang}): {text}")
            tts = gTTS(text, lang=lang, slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_file = fp.name
                tts.save(temp_file)
            playsound(temp_file)
            os.remove(temp_file)
        except Exception as e:
            logger.error(f"Lỗi TTS: {e}")
    
    if is_async:
        threading.Thread(target=_speak, daemon=True).start()
    else:
        _speak()

# ========== HIỂN THỊ TEXT TIẾNG VIỆT ==========
def put_vn_text(img, text, pos, font_size=22, color=(255, 255, 0)):
    """Vẽ text tiếng Việt lên ảnh OpenCV"""
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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
    
    draw.text(pos, text, font=font, fill=color[::-1])
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ========== CHUẨN HÓA ẢNH ==========
def prepare_face_image(face_img, target_size=512, margin_percent=0.5):
    """Chuẩn hóa ảnh khuôn mặt về 512x512 với margin"""
    try:
        h, w = face_img.shape[:2]
        logger.info(f"📐 Ảnh gốc: {w}x{h} pixels")
        
        margin_w = int(w * margin_percent)
        margin_h = int(h * margin_percent)
        
        canvas_size = max(w, h) + max(margin_w, margin_h) * 2
        canvas = np.zeros((canvas_size, canvas_size, 3), dtype=np.uint8)
        canvas.fill(114)
        
        start_x = (canvas_size - w) // 2
        start_y = (canvas_size - h) // 2
        canvas[start_y:start_y+h, start_x:start_x+w] = face_img
        
        interpolation = cv2.INTER_AREA if canvas_size > target_size else cv2.INTER_CUBIC
        resized = cv2.resize(canvas, (target_size, target_size), interpolation=interpolation)
        
        logger.info(f"✅ Đã chuẩn hóa: {w}x{h} → {target_size}x{target_size}")
        return resized
    except Exception as e:
        logger.error(f"❌ Lỗi chuẩn hóa ảnh: {e}")
        return cv2.resize(face_img, (target_size, target_size), interpolation=cv2.INTER_CUBIC)

# ========== TÌM HAAR CASCADE ==========
def find_haar_cascade(candidates):
    """Tìm file haarcascade trong hệ thống"""
    try:
        base = cv2.data.haarcascades
        candidate = os.path.join(base, "haarcascade_frontalface_default.xml")
        if os.path.isfile(candidate):
            return candidate
    except AttributeError:
        pass
    
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

# ========== ENSURE XDG_RUNTIME_DIR ==========
def ensure_runtime_dir():
    """Tạo XDG_RUNTIME_DIR nếu chưa có"""
    path = os.environ.get("XDG_RUNTIME_DIR") or "/tmp/xdg-runtime"
    try:
        os.makedirs(path, exist_ok=True)
        os.chmod(path, 0o700)
        os.environ["XDG_RUNTIME_DIR"] = path
    except Exception as e:
        logger.warning(f"Không thiết lập được XDG_RUNTIME_DIR: {e}")
