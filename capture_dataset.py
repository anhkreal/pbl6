import cv2
import os
import numpy as np
from datetime import datetime
import time

# ========== CẤU HÌNH ==========
CAMERA_WIDTH = 640   # GIỐNG RASPBERRY (hoặc 1280 nếu muốn chất lượng cao hơn)
CAMERA_HEIGHT = 480  # GIỐNG RASPBERRY (hoặc 720 nếu muốn chất lượng cao hơn)
OUTPUT_DIR = "dataset"  # Thư mục lưu ảnh
IMAGE_SIZE = 512  # Kích thước ảnh output (512x512 chuẩn ArcFace)
MIN_FACE_SIZE = 100  # Giảm xuống 100 để phù hợp với 640x480

# ========== TÌM HAAR CASCADE ==========
def find_haar_cascade():
    """Tìm file haarcascade_frontalface_default.xml"""
    try:
        base = cv2.data.haarcascades
        candidate = os.path.join(base, "haarcascade_frontalface_default.xml")
        if os.path.isfile(candidate):
            return candidate
    except AttributeError:
        pass
    
    # Các vị trí thường gặp
    candidates = [
        "C:/opencv/data/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

CASCADE_PATH = find_haar_cascade()
if not CASCADE_PATH:
    print("❌ Không tìm thấy haarcascade_frontalface_default.xml")
    print("Tải về từ: https://github.com/opencv/opencv/tree/master/data/haarcascades")
    exit(1)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
print(f"✓ Đã load Haar Cascade từ: {CASCADE_PATH}")

# ========== LIỆT KÊ CAMERA ==========
def list_available_cameras(max_cameras=10):
    """
    Tìm tất cả camera có sẵn trên hệ thống
    
    Returns:
        List các camera index có thể dùng
    """
    available_cameras = []
    
    print("\n🔍 Đang tìm kiếm camera...")
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Thử đọc 1 frame để chắc chắn camera hoạt động
            ret, frame = cap.read()
            if ret:
                # Lấy thông tin camera
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                available_cameras.append({
                    'index': i,
                    'width': width,
                    'height': height,
                    'fps': fps
                })
                
                print(f"  ✓ Camera {i}: {width}x{height} @ {fps}fps")
            cap.release()
    
    return available_cameras

def select_camera():
    """
    Cho phép user chọn camera
    
    Returns:
        Camera index được chọn
    """
    cameras = list_available_cameras()
    
    if len(cameras) == 0:
        print("❌ Không tìm thấy camera nào!")
        return None
    
    print("\n" + "="*70)
    print("📹 DANH SÁCH CAMERA:")
    print("="*70)
    for i, cam in enumerate(cameras):
        is_fullhd = (cam['width'] >= 1280 and cam['height'] >= 720)
        tag = " [FullHD+]" if is_fullhd else " [Laptop]" if i == 0 else ""
        print(f"  [{cam['index']}] Camera {cam['index']}: {cam['width']}x{cam['height']} @ {cam['fps']}fps{tag}")
    print("="*70)
    
    # Nếu chỉ có 1 camera
    if len(cameras) == 1:
        print(f"\nℹ Chỉ có 1 camera, tự động chọn Camera {cameras[0]['index']}")
        return cameras[0]['index']
    
    # Cho phép chọn
    while True:
        try:
            choice = input(f"\n👉 Chọn camera [0-{cameras[-1]['index']}] (mặc định: 0): ").strip()
            
            if choice == "":
                choice = 0
            else:
                choice = int(choice)
            
            # Kiểm tra xem camera index có hợp lệ không
            if any(cam['index'] == choice for cam in cameras):
                selected_cam = next(cam for cam in cameras if cam['index'] == choice)
                print(f"✓ Đã chọn Camera {choice}: {selected_cam['width']}x{selected_cam['height']}")
                return choice
            else:
                print(f"❌ Camera {choice} không tồn tại, vui lòng chọn lại!")
        except ValueError:
            print("❌ Vui lòng nhập số!")

# ========== CHUẨN HÓA ẢNH ==========
def prepare_face_image(face_img, target_size=512, margin_percent=0.5):
    """
    Chuẩn hóa ảnh khuôn mặt giống như raspberry_face_app.py
    """
    try:
        h, w = face_img.shape[:2]
        
        # Tính margin
        margin_w = int(w * margin_percent)
        margin_h = int(h * margin_percent)
        
        # Tạo canvas vuông với margin
        canvas_size = max(w, h) + max(margin_w, margin_h) * 2
        canvas = np.zeros((canvas_size, canvas_size, 3), dtype=np.uint8)
        canvas.fill(114)
        
        # Đặt ảnh vào giữa canvas
        start_x = (canvas_size - w) // 2
        start_y = (canvas_size - h) // 2
        canvas[start_y:start_y+h, start_x:start_x+w] = face_img
        
        # Resize về kích thước chuẩn
        if canvas_size > target_size:
            interpolation = cv2.INTER_AREA
        else:
            interpolation = cv2.INTER_CUBIC
            
        resized = cv2.resize(canvas, (target_size, target_size), interpolation=interpolation)
        
        return resized
        
    except Exception as e:
        print(f"❌ Lỗi chuẩn hóa ảnh: {e}")
        return cv2.resize(face_img, (target_size, target_size), interpolation=cv2.INTER_CUBIC)

# ========== MAIN PROGRAM ==========
def main():
    """Chương trình chính"""
    print("\n" + "="*70)
    print("📸 CHƯƠNG TRÌNH CHỤP ẢNH DATASET - FACE RECOGNITION")
    print("="*70)
    
    # ===== CHỌN CAMERA =====
    camera_index = select_camera()
    if camera_index is None:
        return
    
    # Nhập tên người dùng
    person_name = input("\n👤 Nhập tên người (VD: Nguyen Van A): ").strip()
    if not person_name:
        print("❌ Tên không được để trống!")
        return
    
    # Tạo thư mục lưu ảnh
    person_dir = os.path.join(OUTPUT_DIR, person_name.replace(" ", "_"))
    os.makedirs(person_dir, exist_ok=True)
    
    # ===== HIỂN THỊ ĐƯỜNG DẪN TUYẾT ĐỐI =====
    abs_person_dir = os.path.abspath(person_dir)
    print(f"✓ Thư mục lưu ảnh: {abs_person_dir}")
    print(f"ℹ Mở File Explorer tại: {abs_person_dir}")
    
    # Đếm số ảnh hiện có
    existing_images = [f for f in os.listdir(person_dir) if f.endswith('.jpg')]
    image_count = len(existing_images)
    print(f"ℹ Đã có {image_count} ảnh trong thư mục")
    
    # ===== MỞ CAMERA ĐÃ CHỌN =====
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    
    if not cap.isOpened():
        print(f"❌ Không mở được camera {camera_index}!")
        return
    
    # Lấy độ phân giải thực tế
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✓ Đã mở Camera {camera_index}: {actual_width}x{actual_height}")
    
    print("\n" + "="*70)
    print("💡 HƯỚNG DẪN SỬ DỤNG:")
    print("="*70)
    print("  📷 SPACE       - Chụp ảnh khuôn mặt được phát hiện")
    print("  🔄 'c'         - Chụp liên tục (mỗi 0.5s)")
    print("  ⏸️  's'         - Dừng chụp liên tục")
    print("  🗑️  'd'         - Xóa ảnh cuối cùng")
    print("  ❌ ESC/q       - Thoát chương trình")
    print("="*70)
    print("\n📸 Bắt đầu! Nhìn vào camera và nhấn SPACE để chụp...\n")
    
    continuous_mode = False
    last_capture_time = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Không đọc được frame từ camera")
            break
        
        # Lật ảnh ngang (mirror) để dễ nhìn
        frame = cv2.flip(frame, 1)
        
        # Chuyển sang grayscale để detect
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Phát hiện khuôn mặt
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE)
        )
        
        # Vẽ khung xanh cho khuôn mặt
        display_frame = frame.copy()
        face_detected = False
        largest_face = None
        
        for (x, y, w, h) in faces:
            face_detected = True
            
            # Chọn khuôn mặt lớn nhất
            if largest_face is None or (w * h) > (largest_face[2] * largest_face[3]):
                largest_face = (x, y, w, h)
        
        # Vẽ khung cho khuôn mặt lớn nhất
        if largest_face is not None:
            x, y, w, h = largest_face
            
            # Đánh giá chất lượng
            if w >= MIN_FACE_SIZE and h >= MIN_FACE_SIZE:
                color = (0, 255, 0)  # Xanh lá - OK
                quality = "GOOD"
            else:
                color = (0, 165, 255)  # Cam - Nhỏ
                quality = "TOO SMALL"
            
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 3)
            cv2.putText(display_frame, f"{quality} ({w}x{h})", 
                       (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Hiển thị thông tin
        info_y = 30
        cv2.putText(display_frame, f"Camera: {camera_index} | {actual_width}x{actual_height}", 
                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(display_frame, f"Person: {person_name}", 
                   (10, info_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(display_frame, f"Images: {image_count}", 
                   (10, info_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        if continuous_mode:
            cv2.putText(display_frame, "CONTINUOUS MODE", 
                       (10, info_y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Hiển thị trạng thái
        if face_detected:
            status = "FACE DETECTED - Press SPACE to capture"
            status_color = (0, 255, 0)
        else:
            status = "NO FACE DETECTED - Please look at camera"
            status_color = (0, 0, 255)
        
        cv2.putText(display_frame, status, 
                   (10, display_frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Hiển thị frame
        cv2.imshow("Dataset Capture", display_frame)
        
        # Xử lý phím
        key = cv2.waitKey(1) & 0xFF
        
        # Chụp ảnh (SPACE hoặc continuous mode)
        should_capture = False
        
        if key == ord(' '):  # SPACE - chụp thủ công
            should_capture = True
        elif continuous_mode and (time.time() - last_capture_time) >= 0.5:
            should_capture = True
        
        if should_capture and largest_face is not None:
            x, y, w, h = largest_face
            
            # Chỉ chụp nếu khuôn mặt đủ lớn
            if w >= MIN_FACE_SIZE and h >= MIN_FACE_SIZE:
                try:
                    # Crop khuôn mặt
                    face_img = frame[y:y+h, x:x+w].copy()
                    
                    # Chuẩn hóa ảnh
                    prepared_img = prepare_face_image(face_img, target_size=IMAGE_SIZE, margin_percent=0.5)
                    
                    # Lưu ảnh
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    filename = f"{person_name.replace(' ', '_')}_{timestamp}.jpg"
                    filepath = os.path.join(person_dir, filename)
                    
                    # ===== LOGGING CHI TIẾT =====
                    print(f"\n🔍 DEBUG:")
                    print(f"   Đường dẫn: {filepath}")
                    print(f"   Kích thước ảnh: {prepared_img.shape}")
                    
                    # Lưu ảnh
                    success = cv2.imwrite(filepath, prepared_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    if success:
                        # Kiểm tra file có tồn tại không
                        if os.path.exists(filepath):
                            file_size = os.path.getsize(filepath)
                            print(f"   ✅ ĐÃ LƯU THÀNH CÔNG!")
                            print(f"   📦 Kích thước file: {file_size / 1024:.1f} KB")
                            
                            image_count += 1
                            last_capture_time = time.time()
                            
                            print(f"\n✓ [{image_count}] {filename} ({w}x{h} -> {IMAGE_SIZE}x{IMAGE_SIZE})")
                        else:
                            print(f"   ❌ LỖI: File KHÔNG TỒN TẠI sau khi lưu!")
                            print(f"   💡 Có thể bị antivirus chặn hoặc lỗi quyền ghi")
                    else:
                        print(f"   ❌ LỖI: cv2.imwrite() trả về False!")
                        print(f"   💡 Kiểm tra quyền ghi file hoặc đường dẫn")
                        
                except Exception as e:
                    print(f"\n❌ LỖI KHI LƯU ẢNH:")
                    print(f"   {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠ Khuôn mặt quá nhỏ ({w}x{h}), đứng GẦN camera hơn!")
        
        # Chế độ chụp liên tục
        if key == ord('c'):
            continuous_mode = True
            print("🔄 BẬT chế độ chụp liên tục (mỗi 0.5s)")
        elif key == ord('s'):
            continuous_mode = False
            print("⏸️ TẮT chế độ chụp liên tục")
        
        # Xóa ảnh cuối
        elif key == ord('d') and image_count > 0:
            images = sorted([f for f in os.listdir(person_dir) if f.endswith('.jpg')])
            if images:
                last_image = images[-1]
                os.remove(os.path.join(person_dir, last_image))
                image_count -= 1
                print(f"🗑️ Đã xóa: {last_image} (còn {image_count} ảnh)")
        
        # Thoát
        elif key == 27 or key == ord('q'):  # ESC hoặc 'q'
            print(f"\n👋 Đã chụp {image_count} ảnh!")
            break
    
    # Dọn dẹp
    cap.release()
    cv2.destroyAllWindows()
    
    # Thống kê
    print("\n" + "="*70)
    print("📊 THỐNG KÊ:")
    print("="*70)
    print(f"  👤 Người: {person_name}")
    print(f"  📁 Thư mục: {person_dir}")
    print(f"  📸 Tổng số ảnh: {image_count}")
    print(f"  📐 Kích thước: {IMAGE_SIZE}x{IMAGE_SIZE} pixels")
    print(f"  🎥 Camera: {camera_index} ({actual_width}x{actual_height})")
    print(f"  💾 Chất lượng: 95%")
    print("="*70)
    
    if image_count > 0:
        print("\n💡 HƯỚNG DẪN TIẾP THEO:")
        print("  1. Upload thư mục dataset lên backend")
        print("  2. Chạy script training trên backend")
        print("  3. Test nhận diện trên Raspberry Pi")
        print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Đã dừng bởi Ctrl+C")
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
