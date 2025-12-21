from fastapi import APIRouter, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import random
from service.shared_instances import get_extractor, get_faiss_manager
from db.nguoi_repository import NguoiRepository
from db.models import Nguoi
from Depend.depend import AddEmbeddingInput

add_router = APIRouter() 

# ✅ Sử dụng shared instances (faiss_manager đã thread-safe)
extractor = get_extractor()
faiss_manager = get_faiss_manager()
nguoi_repo = NguoiRepository()

async def add_embedding_service(
    input: AddEmbeddingInput = Depends(AddEmbeddingInput.as_form),
    file: UploadFile = File(...)
):
    # ✅ Kiểm tra kết nối FAISS - thread-safe tự động
    try:
        _ = faiss_manager.image_ids
    except Exception as e:
        return {"message": f"Không thể kết nối FAISS: {e}", "status_code": 500}
    
    # Kiểm tra tồn tại image_id
    if str(input.image_id) in [str(id) for id in faiss_manager.image_ids]:
        return {"message": f"image_id {input.image_id} đã tồn tại!", "status_code": 400}
    # Đọc ảnh từ file upload
    try:
        image_bytes = file.file.read()
        np_img = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    except Exception as e:
        return {"message": f"Lỗi đọc ảnh: {e}", "status_code": 400}
    # Tiền xử lý và trích xuất embedding
    try:
        embedding = extractor.extract(img)
    except Exception as e:
        return {"message": f"Lỗi trích xuất embedding: {e}", "status_code": 500}
    # Kiểm tra kết nối MySQL trước khi thêm vào FAISS
    try:
        nguoi_exist = nguoi_repo.get_by_id(int(input.class_id)) if input.class_id is not None else None
    except Exception as e:
        return {"message": f"Không thể kết nối MySQL: {e}", "status_code": 500}

    try:
        # Determine class_id to use: use provided class_id or generate a random 6-digit unique id
        if input.class_id is not None:
            class_id_to_use = int(input.class_id)
        else:
            # Attempt to generate a unique 6-digit id
            class_id_to_use = None
            existing_faiss_class_ids = set([str(cid) for cid in faiss_manager.class_ids])
            attempts = 0
            while attempts < 1000:
                cand = random.randint(100000, 999999)
                # check DB and FAISS for collision
                try:
                    exists_in_db = nguoi_repo.get_by_id(cand) is not None
                except Exception:
                    # if DB check fails, conservatively treat as exists to avoid collisions
                    exists_in_db = True
                if (not exists_in_db) and (str(cand) not in existing_faiss_class_ids):
                    class_id_to_use = cand
                    break
                attempts += 1
            if class_id_to_use is None:
                return {"message": "Không thể sinh class_id mới (đã thử nhiều lần, bị trùng).", "status_code": 500}

        # If user doesn't exist, create Nguoi record
        if not nguoi_exist:
            gender_str = None
            if getattr(input, 'gender', None) is not None:
                gender_val = input.gender
                gender_str = "Male" if gender_val in (True, 'True', 'true', 'Nam', 'male', 'Male') else "Female"
            new_nguoi = Nguoi(
                id=class_id_to_use,
                username=None,
                pin=None,
                full_name=getattr(input, 'full_name', None) or f"Person {class_id_to_use}",
                age=getattr(input, 'age', None),
                address=getattr(input, 'address', None),
                phone=None,
                gender=gender_str,
                role='user',
                shift='day',
                status='working',
                avatar_url=image_bytes,
                created_at=None,
                updated_at=None
            )
            nguoi_repo.add(new_nguoi)

        # Insert a khuonmat record and get its id to use as image_id in FAISS
        try:
            khuonmat_id = nguoi_repo.add_khuonmat(user_id=class_id_to_use, image_bytes=image_bytes, image_id=input.image_id if input.image_id else None)
            if khuonmat_id:
                image_id_to_use = khuonmat_id
            else:
                image_id_to_use = input.image_id or None
        except Exception:
            image_id_to_use = input.image_id or None

        # Thread-safe FAISS operations: add embedding with image_id=image_id_to_use and class_id=class_id_to_use
        # No external lock needed - FaissIndexManager has internal RLock
        faiss_manager.add_embeddings([embedding], [image_id_to_use], [None], [class_id_to_use])
        faiss_manager.save()

        # If user existed, update their avatar_url (latest image) and updated_at
        if nguoi_exist:
            try:
                updated_nguoi = Nguoi(
                    id=int(input.class_id),
                    username=nguoi_exist.username if hasattr(nguoi_exist, 'username') else None,
                    pin=nguoi_exist.pin if hasattr(nguoi_exist, 'pin') else None,
                    full_name=nguoi_exist.full_name,
                    age=nguoi_exist.age,
                    address=nguoi_exist.address,
                    phone=nguoi_exist.phone if hasattr(nguoi_exist, 'phone') else None,
                    gender=nguoi_exist.gender,
                    role=nguoi_exist.role if hasattr(nguoi_exist, 'role') else 'user',
                    shift=nguoi_exist.shift if hasattr(nguoi_exist, 'shift') else 'day',
                    status=nguoi_exist.status if hasattr(nguoi_exist, 'status') else 'working',
                    avatar_url=image_bytes,
                    created_at=nguoi_exist.created_at if hasattr(nguoi_exist, 'created_at') else None,
                    updated_at=None
                )
                nguoi_repo.update_by_id(int(input.class_id), updated_nguoi)
            except Exception:
                # If updating avatar fails, we still consider embedding added to FAISS
                pass
            return {"message": f"Đã thêm embedding cho image_id={image_id_to_use}, class_id={class_id_to_use} (class_id đã tồn tại trong bảng nguoi). Cập nhật ảnh/updated_at.", "class_id": class_id_to_use}

        return {"message": f"Đã thêm embedding và thông tin người cho image_id={image_id_to_use}, class_id={class_id_to_use}", "class_id": class_id_to_use}
    except Exception as e:
        return {"message": f"Lỗi thêm embedding hoặc thông tin người: {e}", "status_code": 500}

# fe cần phải truyền về api toàn bộ trường, không được bỏ trống thông tin
# nếu như chỉ thêm ảnh (class_id đã tồn tại) --> điền dữ liệu rác