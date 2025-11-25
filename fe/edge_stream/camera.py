import cv2, time, base64, requests, os
from identity_client import query_identity
from emotion_infer import infer_emotion

class Camera:
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        self._last_meta = {}

    def frames(self):
        while True:
            ok, frame = self.cap.read()
            if not ok:
                # create blank frame fallback
                frame = (255 * (1 - (cv2.getGaussianKernel(480, 64) @ cv2.getGaussianKernel(640,64).T))).astype('uint8')
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            # fake detection: full frame box
            h, w = frame.shape[:2]
            bbox = [0,0,w,h]
            embedding = [0.0]*512  # placeholder
            identity = query_identity(embedding) or {'id': None, 'name': 'Unknown'}
            emotion_label, emotion_type, emotion_score = infer_emotion(frame)
            # draw overlay
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0,255,0), 2)
            cv2.putText(frame, f"{identity['name']}|{emotion_label}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,255,0),2)
            ret, buf = cv2.imencode('.jpg', frame)
            jpeg = buf.tobytes()
            ts = time.time()
            meta = {
                'timestamp': ts,
                'staffId': identity['id'],
                'staffName': identity['name'],
                'emotion': emotion_label,
                'emotion_type': emotion_type,
                'emotion_score': emotion_score,
                'frameImage': base64.b64encode(jpeg[:8000]).decode('utf-8')  # truncate to limit size
            }
            self._last_meta = meta
            yield jpeg, meta

    def last_meta(self):
        return self._last_meta

    def release(self):
        if self.cap:
            self.cap.release()
