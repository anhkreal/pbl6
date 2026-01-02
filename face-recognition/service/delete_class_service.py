from fastapi import APIRouter, Query, Form, Depends
from fastapi.responses import JSONResponse
import numpy as np

from service.shared_instances import get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation
from db.nguoi_repository import NguoiRepository
from Depend.depend import DeleteClassInput

delete_class_router = APIRouter()

# ✅ Sử dụng shared instances
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()
nguoi_repo = NguoiRepository()

@track_operation("delete_class")
def delete_class_service(
    # class_id: int = Form(...)
    input: DeleteClassInput = Depends(DeleteClassInput.as_form)
                 ):
    # ✅ Kiểm tra kết nối FAISS - không load lại (accessing property is thread-safe)
    try:
        _ = faiss_manager.class_ids
    except Exception as e:
        return {"message": f"Không thể kết nối FAISS: {e}", "status_code": 500}
    # Kiểm tra kết nối MySQL
    try:
        _ = nguoi_repo
        # Thử truy vấn đơn giản để kiểm tra kết nối
        nguoi_repo.get_total_and_examples(limit=1)
    except Exception as e:
        return {"message": f"Không thể kết nối MySQL: {e}", "status_code": 500}
    
    # Kiểm tra embedding của image-id 289 trước khi xóa
    # image_id_check = 289
    # try:
    #     emb_before = faiss_manager.index.reconstruct(image_id_check)
    #     print(f'Embedding của image-id={image_id_check} trước khi xóa: {emb_before[:10]} ...')
    # except Exception as e:
    #     print(f'Không reconstruct được embedding image-id={image_id_check} trước khi xóa: {e}')

    # Kiểm tra class_id có tồn tại và lấy image_ids - Protected by lock to prevent race condition
    with faiss_manager._lock:
        class_ids_set = set([int(cid) for cid in faiss_manager.class_ids])
        if int(input.class_id) not in class_ids_set:
            print(f'class_id={input.class_id} không tồn tại trong không gian embedding.')
            return {"message": f"class_id={input.class_id} không tồn tại trong không gian embedding.", "status_code": 404}
        # Lấy các image_id cần xóa
        idx_to_delete = [int(faiss_manager.image_ids[i]) for i, cid in enumerate(faiss_manager.class_ids) if int(cid) == int(input.class_id)]
        if not idx_to_delete:
            print(f'Không tìm thấy vector với class_id={input.class_id}')
    
    # ✅ Thread-safe delete operation (delete_by_class_id has internal lock)
    success = faiss_manager.delete_by_class_id(input.class_id)
    if success:
        faiss_manager.save()  # save also has internal lock
    
    if success:
        # Xóa người tương ứng trong bảng nhanvien (giả định class_id == id)
        try:
            affected_rows = nguoi_repo.delete_by_id(int(input.class_id))
        except Exception:
            affected_rows = 0
        return {
            'success': True,
            'class_id': input.class_id,
            'status': 'deleted',
            'message': f'Đã xóa toàn bộ ảnh với class_id={input.class_id} và rebuild index. Đã xóa luôn người trong bảng nguoi.'
        }
    else:
        return {
            'success': False,
            'class_id': input.class_id,
            'status': 'not_found',
            'message': f'class_id {input.class_id} không tồn tại!',
            "status_code": 404
        }
    