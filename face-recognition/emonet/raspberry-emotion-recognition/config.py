import torch

class Config:
    # Device - Raspberry Pi chỉ dùng CPU
    DEVICE = torch.device("cpu")
    
    # Model
    N_EXPRESSION = 8
    IMAGE_SIZE = 256
    MODEL_PATH = "pretrained/emonet_8.pth"
    
    EMOTION_CLASSES = {
        0: "Neutral", 
        1: "Happy", 
        2: "Sad", 
        3: "Surprise", 
        4: "Fear", 
        5: "Disgust", 
        6: "Anger", 
        7: "Contempt"
    }
    
    # Camera - Tối ưu cho Raspberry Pi
    CAMERA_ID = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 15
    
    # Performance - Xử lý mỗi N frames để tăng tốc
    PROCESS_EVERY_N_FRAMES = 3
    
    # Face detection
    FACE_MARGIN = 30
    MIN_FACE_SIZE = 50