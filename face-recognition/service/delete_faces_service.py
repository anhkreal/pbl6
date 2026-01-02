from db.nguoi_repository import NguoiRepository
from service.shared_instances import get_faiss_manager, get_faiss_lock

nguoi_repo = NguoiRepository()
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()


def delete_faces_for_user(user_id: int):
    """Delete all faces for a user both from FAISS and from the khuonmat table.
    - First remove all FAISS entries with class_id == user_id
    - Then delete all khuonmat rows for that user
    If DB deletion fails after FAISS deletion, attempt to reload FAISS from saved files (best-effort rollback not possible)
    Returns dict with success and counts.
    """
    try:
        print(f"[delete_faces_for_user] Starting deletion for user_id={user_id}")
        
        # Remove from FAISS (delete_by_class_id is already thread-safe with internal lock)
        print(f"[delete_faces_for_user] Deleting from FAISS index...")
        removed = faiss_manager.delete_by_class_id(user_id)
        print(f"[delete_faces_for_user] FAISS removed: {removed}")
        
        # Save after removal (save() is also thread-safe)
        print(f"[delete_faces_for_user] Saving FAISS index...")
        faiss_manager.save()
        print(f"[delete_faces_for_user] FAISS index saved")

        # Remove from DB
        print(f"[delete_faces_for_user] Deleting from database...")
        deleted_rows = nguoi_repo.delete_khuonmats_by_user(int(user_id))
        print(f"[delete_faces_for_user] DB deleted rows: {deleted_rows}")

        return {"success": True, "message": "Xóa mặt khỏi FAISS và DB hoàn tất", "faiss_removed": bool(removed), "db_deleted": deleted_rows}
    except Exception as e:
        print(f"[delete_faces_for_user] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Lỗi khi xóa faces cho user {user_id}: {e}", "status_code": 500}
