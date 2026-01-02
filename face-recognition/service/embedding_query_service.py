from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from service.shared_instances import get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation

# ✅ Sử dụng shared instances
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()

router = APIRouter()

@track_operation("embedding_query")
@router.get('/search_embeddings')
def search_embeddings_api(
    query: str = Query('', description='Chuỗi tìm kiếm (image_id, image_path, class_id)'),
    page: int = Query(1, ge=1, description='Số trang (bắt đầu từ 1)'),
    page_size: int = Query(15, ge=1, le=15, description='Số kết quả mỗi trang'),
    sort_by: str = Query('image_id_asc', description='Sắp xếp theo')
):
    # ✅ Thread-safe query operation - không load lại (method has internal lock)
    result = faiss_manager.query_embeddings_by_string(query, page, page_size, sort_by)
    return result
