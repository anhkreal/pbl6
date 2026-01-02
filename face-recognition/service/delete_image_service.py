from fastapi import APIRouter, Form, Depends
from fastapi.responses import JSONResponse

from service.shared_instances import get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation
from db.nguoi_repository import NguoiRepository
from Depend.depend import DeleteImageInput

delete_image_router = APIRouter()

# ✅ Sử dụng shared instances
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()
nguoi_repo = NguoiRepository()

@track_operation("delete_image")
def delete_image_service(
    # image_id: int = Form(...)
    input: DeleteImageInput = Depends(DeleteImageInput.as_form)
    ):
    # ✅ Kiểm tra kết nối FAISS - không load lại (accessing property is thread-safe)
    try:
        _ = faiss_manager.image_ids
    except Exception as e:
        return {"message": f"Không thể kết nối FAISS: {e}", "status_code": 500}
    # Kiểm tra kết nối MySQL
    try:
        _ = nguoi_repo
        nguoi_repo.get_total_and_examples(limit=1)
    except Exception as e:
        return {"message": f"Không thể kết nối MySQL: {e}", "status_code": 500}
    
    try:
        # Lấy class_id trước khi xóa - Protected by lock to prevent race condition
        with faiss_manager._lock:
            idxs = [i for i, img_id in enumerate(faiss_manager.image_ids) if str(img_id) == str(input.image_id)]
            class_id = None
            if idxs:
                class_id = int(faiss_manager.class_ids[idxs[0]])
        
        # ✅ Thread-safe delete operation (delete_by_image_id has internal lock)
        result = faiss_manager.delete_by_image_id(input.image_id)
        if result:
            faiss_manager.save()  # save also has internal lock
        
        if result:
            # Kiểm tra còn ảnh nào thuộc class_id không
            if class_id is not None:
                ids_left = faiss_manager.get_image_ids_by_class(class_id)
                if not ids_left:
                    affected_rows = nguoi_repo.delete_by_class_id(class_id)
                    return {"message": f"Đã xóa embedding cho image_id={input.image_id} và xóa luôn người class_id={class_id} vì không còn ảnh nào."}
            return {"message": f"Đã xóa embedding cho image_id={input.image_id}"}
        else:
            return {"message": f"image_id {input.image_id} không tồn tại!", "status_code": 404}
    except Exception as e:
        return {"message": f"Lỗi xóa embedding: {e}", "status_code": 500}
