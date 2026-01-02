from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from service.shared_instances import get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation
from db.nguoi_repository import NguoiRepository

get_image_ids_by_class_router = APIRouter()

# ✅ Sử dụng shared instances
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()
nguoi_repo = NguoiRepository()

@track_operation("get_image_ids_by_class")
def get_image_ids_by_class_api_service(class_id: str = Query(..., description="Class ID cần truy vấn")):
    # ✅ Thread-safe query operation - không load lại (method has internal lock)
    image_ids = faiss_manager.get_image_ids_by_class(class_id)
    nguoi = None
    try:
        nguoi = nguoi_repo.get_by_id(int(class_id))
    except Exception:
        nguoi = None
    return {
        'class_id': class_id,
        'image_ids': image_ids,
        'count': len(image_ids),
        'nguoi': nguoi.to_dict(include_avatar_base64=True) if nguoi else None
    }
