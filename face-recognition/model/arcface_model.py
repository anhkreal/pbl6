import torch
import numpy as np
import cv2
# from albumentations.pytorch import ToTensorV2  # Temporarily disabled
# import albumentations as A  # Temporarily disabled
import torchvision.transforms as transforms
import sys
# sys.path.append('/home/intern1/lab/face_recognition/casia-webface/insightface/recognition/arcface_torch')
sys.path.append('E:/intern-bes/intern-2025-AI/face_api/insightface/recognition/arcface_torch')
from backbones import get_model

class ArcFaceFeatureExtractor:
    # def __init__(self, model_path='model/ms1mv3_arcface_r18_fp16.pth', model_version='r18', device=None, img_size=112):
    def __init__(self, model_path='model/ms1mv3_arcface_r18_fp16.pth', model_version='r18', device=None, img_size=112):
        self.model_path = model_path
        self.model_version = model_version
        self.img_size = img_size
        # Tự động chọn GPU nếu có, không thì dùng CPU
        if device is None:
            import torch
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        self.model = self._load_model()
        # Use torchvision transforms instead of albumentations
        self.val_aug = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((self.img_size, self.img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def _load_model(self):
        model = get_model(self.model_version, fp16=True)
        model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        model.eval()
        model.to(self.device)
        return model

    @torch.no_grad()
    def extract(self, img):
        # img: đường dẫn hoặc numpy array
        if isinstance(img, str):
            img = cv2.imread(img)
        if img is None or len(img.shape) != 3 or img.shape[2] != 3:
            img = np.zeros((self.img_size, self.img_size, 3), dtype=np.uint8)
        else:
            # Convert BGR to RGB for PIL transforms
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
        # Apply transforms (note: different from albumentations)
        img_tensor = self.val_aug(img).unsqueeze(0).to(self.device)
        emb = self.model(img_tensor).cpu().numpy()[0]
        return emb

# Example usage:
# extractor = ArcFaceFeatureExtractor('ms1mv3_arcface_r18_fp16.pth', model_version='r18')
# emb = extractor.extract('path/to/image.jpg')
