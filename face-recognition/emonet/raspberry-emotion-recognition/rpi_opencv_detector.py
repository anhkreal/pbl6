import cv2
import numpy as np
from config import Config

class RPiOpenCVDetector:
    def __init__(self):
        print("Khởi tạo OpenCV DNN Detector...")
        self._load_model()
        self._load_face_detector()
        self.frame_count = 0

    def _load_model(self):
        onnx_path = Config.MODEL_PATH.replace('.pth', '.onnx')
        print(f"Load ONNX: {onnx_path}")
        self.net = cv2.dnn.readNetFromONNX(onnx_path)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        print("✓ Model OK")

    def _load_face_detector(self):
        print("Load Haar Cascade...")
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError("Không load được haarcascade_frontalface_default.xml")
        print("✓ Haar OK")

    def detect_faces(self, frame_rgb):
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(Config.MIN_FACE_SIZE, Config.MIN_FACE_SIZE)
        )
        if len(faces) == 0:
            return None
        result = []
        for (x, y, w, h) in faces:
            result.append([x, y, x + w, y + h, 1.0])
        return np.array(result)

    def predict_emotion(self, face_img):
        face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        face_resized = cv2.resize(face_rgb, (Config.IMAGE_SIZE, Config.IMAGE_SIZE))
        blob = cv2.dnn.blobFromImage(
            face_resized,
            scalefactor=1.0/255.0,
            size=(Config.IMAGE_SIZE, Config.IMAGE_SIZE),
            mean=(0, 0, 0),
            swapRB=False,
            crop=False
        )
        self.net.setInput(blob)
        output_names = self.net.getUnconnectedOutLayersNames()
        outputs = self.net.forward(output_names)
        expression_logits = outputs[0][0]
        valence = float(outputs[1][0][0])
        arousal = float(outputs[2][0][0])
        exp_values = np.exp(expression_logits - np.max(expression_logits))
        probs = exp_values / exp_values.sum()
        emotion_id = int(np.argmax(probs))
        return {
            "emotion": Config.EMOTION_CLASSES[emotion_id],
            "emotion_id": emotion_id,
            "valence": float(np.clip(valence, -1.0, 1.0)),
            "arousal": float(np.clip(arousal, -1.0, 1.0))
        }

    def should_process_frame(self):
        self.frame_count += 1
        return self.frame_count % Config.PROCESS_EVERY_N_FRAMES == 0