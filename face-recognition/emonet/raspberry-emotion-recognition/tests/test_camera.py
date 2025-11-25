import cv2

def test_camera(camera_id=0):
    print(f"Đang test camera {camera_id}...")
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"❌ Không thể mở camera {camera_id}")
        return False
    
    print("✓ Camera hoạt động!")
    print("Nhấn 'q' để thoát test")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Camera Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    test_camera()