from fastapi import APIRouter
from fastapi.responses import JSONResponse

from service.shared_instances import get_faiss_manager, get_faiss_lock
from service.performance_monitor import track_operation
from db.nguoi_repository import NguoiRepository
from db import mysql_conn
from db.init_db import create_database_and_tables
import os
import shutil
import traceback
import pymysql

reset_router = APIRouter()

# ✅ Sử dụng shared instances
faiss_manager = get_faiss_manager()
faiss_lock = get_faiss_lock()
nguoi_repo = NguoiRepository()

@track_operation("reset_index")
def reset_index_api_service():
    # ✅ Thread-safe reset operation (accessing property is thread-safe)
    try:
        _ = faiss_manager.image_ids
    except Exception as e:
        return {"message": f"Không thể kết nối FAISS: {e}", "status_code": 500}
    # Kiểm tra kết nối MySQL
    try:
        nguoi_repo.get_total_and_examples(limit=1)
    except Exception as e:
        return {"message": f"Không thể kết nối MySQL: {e}", "status_code": 500}
    
    # ✅ Thread-safe reset operation for FAISS (clear in-memory and persistent files)
    faiss_index_path = getattr(faiss_manager, 'index_path', None)
    faiss_meta_path = getattr(faiss_manager, 'meta_path', None)

    try:
        # reset_index may have internal lock, but file operations should be outside
        faiss_manager.reset_index()
        # remove files if they exist to fully wipe persisted state
        if faiss_index_path and os.path.exists(faiss_index_path):
            try:
                os.remove(faiss_index_path)
            except Exception:
                # fallback: try moving to a temp backup
                try:
                    shutil.move(faiss_index_path, faiss_index_path + '.bak')
                except Exception:
                    pass
        if faiss_meta_path and os.path.exists(faiss_meta_path):
            try:
                os.remove(faiss_meta_path)
            except Exception:
                try:
                    shutil.move(faiss_meta_path, faiss_meta_path + '.bak')
                except Exception:
                    pass
    except Exception as e:
        return {"message": f"Lỗi khi reset FAISS: {e}", "status_code": 500}

    # Now drop and recreate the MySQL database
    db_name = mysql_conn.MYSQL_DB
    try:
        conn = pymysql.connect(host=mysql_conn.MYSQL_HOST, port=mysql_conn.MYSQL_PORT,
                               user=mysql_conn.MYSQL_USER, password=mysql_conn.MYSQL_PASSWORD,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor, autocommit=True)
        with conn.cursor() as cursor:
            # Drop the database entirely (NUCLEAR)
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`;")
        conn.close()
    except Exception as e:
        traceback.print_exc()
        return {"message": f"Lỗi khi xóa database {db_name}: {e}", "status_code": 500}

    # Recreate database and tables (idempotent)
    try:
        create_database_and_tables()
    except Exception as e:
        traceback.print_exc()
        return {"message": f"Lỗi khi tạo lại database/tables: {e}", "status_code": 500}

    # Reinitialize FAISS files to an empty index (if the manager knows paths)
    try:
        # reset_index and save have internal locks
        faiss_manager.reset_index()
        # ensure persisted empty files exist
        faiss_manager.save()
    except Exception as e:
        traceback.print_exc()
        return {"message": f"Lỗi khi lưu FAISS rỗng: {e}", "status_code": 500}

    return {"message": "Đã xóa FAISS và MySQL và khởi tạo lại thành công", "success": True}
