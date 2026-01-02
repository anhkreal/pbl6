from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import time

from service.shared_instances import get_extractor, get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation
from db.nguoi_repository import NguoiRepository
from service.emonet_service import predict_emotion_from_bytes

# ✅ Sử dụng shared instances
extractor = get_extractor()
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()
nguoi_repo = NguoiRepository()

face_query_top5_router = APIRouter()

@track_operation("face_query_top5")
async def query_face_top5_service(file: UploadFile = File(...)):
    # ✅ Thread-safe FAISS access
    start_total = time.time()
    image_bytes = await file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return {"error": "Lỗi: Không decode được ảnh!", "status_code": 400}
    # predict emotion from query image
    try:
        emo_query = predict_emotion_from_bytes(image_bytes)
    except Exception:
        emo_query = None
    
    emb = extractor.extract(image)
    
    # query method is already thread-safe with internal lock
    results = faiss_manager.query(emb, topk=5)
    resp = []
    mysql_error = False
    for r in results:
        if r['score'] > 0:
            class_id = int(r['class_id'])
            nguoi = None
            if not mysql_error:
                try:
                    nguoi = nguoi_repo.get_by_id(class_id)
                except Exception:
                    mysql_error = True
            item = {
                'image_id': int(r['image_id']),
                'image_path': str(r['image_path']),
                'class_id': class_id,
                'score': float(r['score'])
            }
            # attach query emotion once per response
            if emo_query and 'emotion' not in item:
                item['emotion'] = emo_query
            if nguoi:
                item['nguoi'] = nguoi.to_dict(include_avatar_base64=True)
            resp.append(item)
    return {"results": resp, "total_time": round(time.time() - start_total, 3)}
