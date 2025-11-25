import cv2
import time
from rpi_opencv_detector import RPiOpenCVDetector
from config import Config

def main():
    detector = RPiOpenCVDetector()
    
    print(f"Đang mở camera {Config.CAMERA_ID}...")
    cap = cv2.VideoCapture(Config.CAMERA_ID)
    
    if not cap.isOpened():
        print("❌ Lỗi: Không thể mở camera!")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
    
    print("✓ Camera đã sẵn sàng")
    print("=" * 50)
    print("Nhấn 'q' để thoát")
    print("=" * 50)
    
    fps_start_time = time.time()
    fps_counter = 0
    fps_display = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if detector.should_process_frame():
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = detector.detect_faces(frame_rgb)
            
            if faces is not None:
                for face_box in faces:
                    x_min, y_min, x_max, y_max, confidence = face_box
                    
                    x1 = max(0, int(x_min) - Config.FACE_MARGIN)
                    y1 = max(0, int(y_min) - Config.FACE_MARGIN)
                    x2 = min(frame.shape[1], int(x_max) + Config.FACE_MARGIN)
                    y2 = min(frame.shape[0], int(y_max) + Config.FACE_MARGIN)
                    
                    face_img = frame[y1:y2, x1:x2]
                    
                    if face_img.size == 0 or (x2 - x1) < Config.MIN_FACE_SIZE:
                        continue
                    
                    result = detector.predict_emotion(face_img)
                    
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    text = f"{result['emotion']}"
                    text2 = f"V:{result['valence']:.2f} A:{result['arousal']:.2f}"
                    
                    cv2.putText(frame, text, (x1, y1 - 25), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.putText(frame, text2, (x1, y1 - 5), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        fps_counter += 1
        if time.time() - fps_start_time > 1:
            fps_display = fps_counter
            fps_counter = 0
            fps_start_time = time.time()
        
        cv2.putText(frame, f"FPS: {fps_display}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow('Raspberry Pi - OpenCV DNN', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✓ Chương trình đã kết thúc")

if __name__ == "__main__":
    main()