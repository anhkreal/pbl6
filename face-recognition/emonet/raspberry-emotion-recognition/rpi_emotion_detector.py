
import torch
from torch import nn
import cv2
import numpy as np
import face_alignment
from emonet.models import EmoNet
from config import Config
import time

class RPiEmotionDetector:
    def __init__(self):
        print("Khởi tạo Emotion Detector cho Raspberry Pi...")
        print(f"Device: {Config.DEVICE}")
        
        self._load_model()
        self._load_face_detector()
        self.frame_count = 0
        
    def _load_model(self):
        """Load mô hình EmoNet"""
        print(f"Đang load model từ {Config.MODEL_PATH}...")
        
        state_dict = torch.load(
            Config.MODEL_PATH, 
            map_location='cpu'
        )
        state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
        
        self.net = EmoNet(n_expression=Config.N_EXPRESSION).to(Config.DEVICE)
        self.net.load_state_dict(state_dict, strict=False)
        self.net.eval()
        
        print("✓ Model đã load thành công")
    
    def _load_face_detector(self):
        """Load face alignment detector"""
        print("Đang load face detector...")
        try:
            self.fa = face_alignment.FaceAlignment(
                face_alignment.LandmarksType.TWO_D, 
                flip_input=False, 
                device='cpu'
            )
        except AttributeError:
            self.fa = face_alignment.FaceAlignment(
                '2D', 
                flip_input=False, 
                device='cpu'
            )
        print("✓ Face detector đã load thành công")
    
    def detect_faces(self, frame_rgb):
        """Phát hiện khuôn mặt trong frame"""
        return self.fa.face_detector.detect_from_image(frame_rgb)
    
    def predict_emotion(self, face_img):
        """Dự đoán cảm xúc từ ảnh khuôn mặt"""
        face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        face_resized = cv2.resize(face_rgb, (Config.IMAGE_SIZE, Config.IMAGE_SIZE))
        
        image_tensor = torch.Tensor(face_resized).permute(2, 0, 1).to(Config.DEVICE) / 255.0
        
        with torch.no_grad():
            output = self.net(image_tensor.unsqueeze(0))
            
            emotion_class = torch.argmax(
                nn.functional.softmax(output["expression"], dim=1)
            ).cpu().item()
            
            valence = output['valence'].clamp(-1.0, 1.0).cpu().item()
            arousal = output['arousal'].clamp(-1.0, 1.0).cpu().item()
        
        return {
            'emotion': Config.EMOTION_CLASSES[emotion_class],
            'emotion_id': emotion_class,
            'valence': valence,
            'arousal': arousal
        }
    
    def should_process_frame(self):
        """Kiểm tra có nên xử lý frame hiện tại không"""
        self.frame_count += 1
        return self.frame_count % Config.PROCESS_EVERY_N_FRAMES == 0