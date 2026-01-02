import numpy as np
import cv2
import faiss
from service.shared_instances import get_extractor, get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation
from db.nguoi_repository import NguoiRepository
from db.models import Nguoi
from index.faiss import FaissIndexManager
from config import FAISS_INDEX_PATH, FAISS_META_PATH

@track_operation("edit_embedding")
def edit_embedding_service(input, file):
    # ✅ Sử dụng shared instances
    faiss_manager = get_faiss_manager()
    faiss_lock = get_faiss_lock()
    extractor = get_extractor()
    nguoi_repo = NguoiRepository()
    
    # ✅ Thread-safe check existence (property access is thread-safe)
    if str(input.image_id) not in [str(id) for id in faiss_manager.image_ids]:
        return {"message": f"image_id {input.image_id} không tồn tại!", "status_code": 404}
    
    try:
        # Find index - Protected by lock to prevent race condition during enumeration
        with faiss_manager._lock:
            idxs = [i for i, img_id in enumerate(faiss_manager.image_ids) if str(img_id) == str(input.image_id)]
            if not idxs:
                return {"message": f"Không tìm thấy index cho image_id {input.image_id}", "status_code": 404}
            idx = idxs[0]
        
        updated_fields = []
        
        # Cập nhật embedding nếu file ảnh được gửi lên
        if file is not None and hasattr(file, 'file'):
            try:
                image_bytes = file.file.read()
                np_img = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                
                if img is None:
                    return {"message": "Không thể decode ảnh!", "status_code": 400}
                
                # ✅ Sử dụng shared extractor
                new_embedding = extractor.extract(img)
                
                # L2 normalization (quan trọng!)
                new_embedding_norm = new_embedding / np.linalg.norm(new_embedding)
                
                # CRITICAL SECTION: Directly modifying internal state requires manual lock
                # Since FAISS manager doesn't have update_embedding method, we need to protect this
                with faiss_manager._lock:
                    # Cập nhật embedding trong memory
                    faiss_manager.embeddings[idx] = new_embedding_norm.tolist()
                    
                    # QUAN TRỌNG: Rebuild FAISS index với embeddings mới
                    faiss_manager.index = faiss_manager.index.__class__(faiss_manager.embedding_size)
                    if len(faiss_manager.embeddings) > 0:
                        embeddings_array = np.array(faiss_manager.embeddings, dtype=np.float32)
                        faiss_manager.index.add(embeddings_array)
                
                updated_fields.append('embedding')
                
            except Exception as e:
                return {"message": f"Lỗi trích xuất embedding: {e}", "status_code": 500}
        
        # Cập nhật image_path nếu truyền lên và không rỗng
        if hasattr(input, 'image_path') and input.image_path:
            # Thread-safe: direct property modification needs lock
            with faiss_manager._lock:
                faiss_manager.image_paths[idx] = input.image_path
            updated_fields.append('image_path')
        
        # Lưu thay đổi
        faiss_manager.save()
        
        if updated_fields:
            return {"message": f"Đã cập nhật: {', '.join(updated_fields)} cho image_id={input.image_id}"}
        else:
            return {"message": f"Không có trường nào được cập nhật cho image_id={input.image_id}"}
            
    except Exception as e:
        return {"message": f"Lỗi cập nhật embedding: {e}", "status_code": 500}
