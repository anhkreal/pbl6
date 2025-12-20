"""
Phát hiện khách hàng bằng Motion Detection (Pi Camera)
"""
import cv2
import time
import logging
import traceback
import threading
from .config import (
    CUSTOMER_CAMERA_INDEX, CUSTOMER_CAMERA_WIDTH, CUSTOMER_CAMERA_HEIGHT,
    CUSTOMER_DETECTION_INTERVAL, MOTION_THRESHOLD, MOTION_MIN_AREA, NO_MOTION_TIMEOUT
)

logger = logging.getLogger(__name__)

class CustomerDetector:
    """Class phát hiện khách hàng bằng motion detection"""
    
    def __init__(self):
        self.customer_present = False
        self.customer_camera_running = True
        self.last_motion_time = 0
        self.lock = threading.Lock()
        self.thread = None
    
    def start(self):
        """Khởi động thread phát hiện khách"""
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        logger.info("✅ Đã khởi động thread phát hiện khách (Motion Detection)")
    
    def stop(self):
        """Dừng thread"""
        self.customer_camera_running = False
    
    def is_customer_present(self) -> bool:
        """Kiểm tra có khách hay không (thread-safe)"""
        with self.lock:
            return self.customer_present
    
    def _detection_loop(self):
        """Vòng lặp chính của thread"""
        logger.info("🎥 Khởi động Pi Camera...")
        
        # Mở camera
        cap = cv2.VideoCapture(CUSTOMER_CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CUSTOMER_CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CUSTOMER_CAMERA_HEIGHT)
        
        if not cap.isOpened():
            logger.error("❌ Không mở được Pi Camera (index=%d)", CUSTOMER_CAMERA_INDEX)
            return
        
        logger.info("✅ Pi Camera sẵn sàng - Motion Detection")
        print("💡 Phát hiện khách bằng CHUYỂN ĐỘNG")
        
        # Khởi tạo background subtractor
        back_sub = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False
        )
        
        # Học background 2 giây
        logger.info("⏳ Đang học background...")
        for _ in range(40):
            ret, frame = cap.read()
            if ret:
                back_sub.apply(frame)
            time.sleep(0.05)
        logger.info("✅ Background model sẵn sàng")
        
        # Vòng lặp phát hiện
        while self.customer_camera_running:
            try:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.5)
                    continue
                
                # Background subtraction
                fg_mask = back_sub.apply(frame)
                
                # Loại bỏ nhiễu
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
                fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
                
                # Tìm contours
                contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                motion_pixels = cv2.countNonZero(fg_mask)
                
                # Kiểm tra chuyển động
                significant_motion = any(cv2.contourArea(c) > MOTION_MIN_AREA for c in contours)
                current_time = time.time()
                
                if significant_motion or motion_pixels > MOTION_THRESHOLD:
                    self.last_motion_time = current_time
                    
                    with self.lock:
                        old_state = self.customer_present
                        self.customer_present = True
                        
                        if not old_state:
                            logger.info("👤 PHÁT HIỆN KHÁCH HÀNG")
                            print(f"\n{'='*60}")
                            print(f"👤 KHÁCH HÀNG XUẤT HIỆN - Motion: {motion_pixels} px")
                            print(f"{'='*60}\n")
                else:
                    time_since_last_motion = current_time - self.last_motion_time
                    
                    with self.lock:
                        old_state = self.customer_present
                        
                        if time_since_last_motion > NO_MOTION_TIMEOUT:
                            self.customer_present = False
                            
                            if old_state:
                                logger.info("👋 Khách rời đi")
                                print(f"\n{'='*60}")
                                print(f"👋 KHÔNG CÒN KHÁCH")
                                print(f"{'='*60}\n")
                
                time.sleep(CUSTOMER_DETECTION_INTERVAL)
            
            except Exception as e:
                logger.error(f"❌ Lỗi detection: {e}")
                traceback.print_exc()
                time.sleep(1)
        
        cap.release()
        logger.info("🛑 Thread phát hiện khách đã dừng")
