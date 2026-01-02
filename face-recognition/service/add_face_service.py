import numpy as np
import cv2
from db.nguoi_repository import NguoiRepository
from service.shared_instances import get_extractor, get_faiss_manager, get_faiss_lock

nguoi_repo = NguoiRepository()
extractor = get_extractor()
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()


def add_face_service(user_id: int, image_bytes: bytes):
    """Add a face image (bytes from UploadFile) for an existing user:
    - inserts a `khuonmat` record (image blob)
    - adds the embedding to FAISS with image_id = khuonmat.id and class_id = user_id
    Returns dict with result or error and status_code on failure.
    """
    try:
        # ensure user exists
        try:
            user = nguoi_repo.get_by_id(int(user_id))
        except Exception as e:
            return {"success": False, "message": f"Không thể kết nối MySQL: {e}", "status_code": 500}

        if not user:
            return {"success": False, "message": f"Không tìm thấy user id={user_id}", "status_code": 404}

        # image_bytes is provided by the API layer
        try:
            np_img = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if img is None:
                return {"success": False, "message": "Không thể đọc ảnh (cv2.imdecode trả về None)", "status_code": 400}
        except Exception as e:
            return {"success": False, "message": f"Lỗi đọc ảnh: {e}", "status_code": 400}

        # extract embedding
        try:
            embedding = extractor.extract(img)
        except Exception as e:
            return {"success": False, "message": f"Lỗi trích xuất embedding: {e}", "status_code": 500}

        # insert khuonmat
        try:
            khuonmat_id = nguoi_repo.add_khuonmat(user_id=int(user_id), image_bytes=image_bytes)
        except Exception as e:
            khuonmat_id = None

        image_id_to_use = khuonmat_id if khuonmat_id else None

        # add embedding to FAISS with rollback semantics
        faiss_added = False
        try:
            # add_embeddings and save are already thread-safe with internal locks
            faiss_manager.add_embeddings([embedding], [image_id_to_use], [None], [int(user_id)])
            faiss_manager.save()
            faiss_added = True
        except Exception as e:
            # If FAISS add fails, rollback DB insert if we created one
            if image_id_to_use is not None:
                try:
                    nguoi_repo.delete_khuonmat_by_id(image_id_to_use)
                except Exception:
                    pass
            return {"success": False, "message": f"Lỗi khi thêm vào FAISS: {e}", "image_id": image_id_to_use, "class_id": int(user_id), "status_code": 500}

        return {"success": True, "message": "Đã thêm khuôn mặt và embedding vào FAISS", "image_id": image_id_to_use, "class_id": int(user_id)}

    except Exception as e:
        return {"success": False, "message": f"Lỗi khi thêm khuôn mặt: {e}", "status_code": 500}
