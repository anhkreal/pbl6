from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import time


from service.shared_instances import get_extractor, get_faiss_manager, get_faiss_lock
from db.nguoi_repository import NguoiRepository
from service.emonet_service import predict_emotion_from_bytes
from service.add_emotion_service import add_emotion_service
import io


# ✅ Sử dụng shared instances thay vì tạo mới
extractor = get_extractor()
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()
nguoi_repo = NguoiRepository()

router = APIRouter()

async def query_face_service(file: UploadFile = File(...)):
    # ✅ Không load lại FAISS mỗi request - sử dụng thread-safe access
    start_total = time.time()
    
    image_bytes = await file.read()
    if not image_bytes:
        return {"error": "Lỗi: file ảnh rỗng (không đọc được). Hãy đảm bảo file được upload đúng.", "status_code": 400}

    try:
        buf = np.frombuffer(image_bytes, np.uint8)
        if buf.size == 0:
            return {"error": "Lỗi: file ảnh rỗng (buffer 0).", "status_code": 400}
        image = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if image is None:
            return {"error": "Lỗi: Không decode được ảnh (imdecode trả None). Hãy kiểm tra định dạng file." , "status_code": 400}
    except cv2.error as e:
        # Return a clear error instead of letting OpenCV propagate a 500
        print(f"OpenCV imdecode error: {e}")
        return {"error": f"OpenCV decode error: {e}", "status_code": 400}
    except Exception as e:
        print(f"Unexpected error when decoding image: {e}")
        return {"error": f"Unexpected decode error: {e}", "status_code": 500}
    # Predict emotion from the uploaded/query image (if model available)
    try:
        emo_query = predict_emotion_from_bytes(image_bytes)
    except Exception:
        emo_query = None
    print(f"[debug] emo_query from emonet_service: {emo_query}")
    
    emb = extractor.extract(image)
    
    # ✅ Thread-safe FAISS query
    with faiss_lock:
        results = faiss_manager.query(emb, topk=1)
    
    # Threshold 0.42 chosen based on model validation: scores above 0.42 indicate a confident match.
    if results and results[0]['score'] > 0.27:
        class_id = str(results[0]['class_id'])
        try:
                nguoi = nguoi_repo.get_by_id(int(class_id))
        except Exception as e:
            print(f"Lỗi truy vấn MySQL: {e}")
            nguoi = None
        resp = {
            'image_id': int(results[0]['image_id']),
            'image_path': str(results[0]['image_path']),
            'class_id': class_id,
            'score': float(results[0]['score'])
        }
        # Attach emotion prediction from the query image (always include the field if available)
        if emo_query is not None:
            resp['emotion'] = emo_query
        else:
            print("[debug] emo_query is None, emotion not attached")
        
            # If we have a matched user and a detected negative emotion, log it via add_emotion_service
            try:
                # Ensure we have a valid emotion result
                if emo_query and isinstance(emo_query, dict):
                    emo_label = emo_query.get('emotion')
                    emo_prob = emo_query.get('prob')
                else:
                    emo_label = None
                    emo_prob = None
                negative_set = {"Sad", "Fear", "Disgust", "Anger", "Contempt"}
                # only proceed if the matched user exists and has a username
                if nguoi and getattr(nguoi, 'username', None) and emo_label and str(emo_label) in negative_set:
                    # create a simple file-like wrapper for image bytes
                    class FileLike:
                        def __init__(self, b):
                            self.file = io.BytesIO(b)
                    file_obj = FileLike(image_bytes)
                    # call service to add emotion log (camera_id left as None)
                    try:
                        add_emotion_service(user_id=int(class_id), camera_id=None, emotion_type=str(emo_label), confidence=float(emo_prob) if emo_prob is not None else None, image_file=file_obj, note=None)
                        print(f"[debug] Logged negative emotion for user {class_id}: {emo_label} ({emo_prob})")
                    except Exception as e:
                        print(f"[debug] Failed to log emotion: {e}")
            except Exception as e:
                print(f"[debug] Exception in emotion logging flow: {e}")
        if nguoi:
            resp['nguoi'] = nguoi.to_dict(include_avatar_base64=True)
        return resp
    else:
        # No matching result found
        return {}
