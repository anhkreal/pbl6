from fastapi import APIRouter
from fastapi.responses import JSONResponse
from service.shared_instances import get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation

vector_info_router = APIRouter()

# ✅ Sử dụng shared instances
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()

@track_operation("vector_info")
def get_vector_info_service():
    # ✅ Thread-safe vector info query - không load lại
    n = 10
    
    def _safe_int(val):
        if val is None:
            return None
        try:
            return int(val)
        except Exception:
            try:
                # try converting from bytes
                if isinstance(val, (bytes, bytearray)):
                    return int(val.decode())
            except Exception:
                return None
    
    # Lấy 10 vector đầu và cuối - Protected by lock to prevent race condition during iteration
    with faiss_manager._lock:
        total = len(faiss_manager.image_ids)
        if total == 0:
            return {"message": "Không có vector nào trong FAISS index.", "status_code": 404}
        
        first_vectors = []
        for i in range(min(n, total)):
            # defensive extraction: allow None or non-numeric ids
            raw_image_id = faiss_manager.image_ids[i] if i < len(faiss_manager.image_ids) else None
            raw_image_path = faiss_manager.image_paths[i] if i < len(faiss_manager.image_paths) else None
            raw_class_id = faiss_manager.class_ids[i] if i < len(faiss_manager.class_ids) else None

            first_vectors.append({
                'faiss_index': int(i),
                'image_id': _safe_int(raw_image_id),
                'image_path': str(raw_image_path) if raw_image_path is not None else None,
                'class_id': _safe_int(raw_class_id),
                # 'embedding': faiss_manager.embeddings[i]
            })
        
        # Lấy 10 vector cuối
        last_vectors = []
        for i in range(max(0, total-n), total):
            raw_image_id = faiss_manager.image_ids[i] if i < len(faiss_manager.image_ids) else None
            raw_image_path = faiss_manager.image_paths[i] if i < len(faiss_manager.image_paths) else None
            raw_class_id = faiss_manager.class_ids[i] if i < len(faiss_manager.class_ids) else None

            last_vectors.append({
                'faiss_index': int(i),
                'image_id': _safe_int(raw_image_id),
                'image_path': str(raw_image_path) if raw_image_path is not None else None,
                'class_id': _safe_int(raw_class_id),
                # 'embedding': faiss_manager.embeddings[i]
            })
        
        faiss_manager.check_index_data()
    
    return {
        "first_vectors": first_vectors,
        "last_vectors": last_vectors,
        "total": total
    }
