def get_kpi_by_user_and_date_service(user_id: int, date: str):
    """Lấy KPI theo user_id và ngày (YYYY-MM-DD)."""
    try:
        sql = "SELECT * FROM kpi WHERE user_id = %s AND DATE(date) = %s LIMIT 1"
        with nguoi_repo as cursor:
            cursor.execute(sql, (user_id, date))
            row = cursor.fetchone()
            if row:
                kpi = KPI.from_row(row)
                return {"success": True, "kpi": kpi.__dict__}
            return {"success": False, "message": "Không tìm thấy KPI với user_id và ngày này"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi truy vấn KPI: {e}"}
"""
KPI Service Layer
-----------------
Các hàm thao tác với cơ sở dữ liệu thật cho KPI: thêm, cập nhật, truy vấn, tìm kiếm theo user/date.
"""

from db.nguoi_repository import NguoiRepository
from db.models import KPI

nguoi_repo = NguoiRepository()

def add_kpi_service(user_id: int, date: str, emotion_score: float, attendance_score: float, total_score: float, remark: str = None):
    """Thêm KPI vào cơ sở dữ liệu."""
    try:
        sql = (
            "INSERT INTO kpi (user_id, date, emotion_score, attendance_score, total_score, remark) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        with nguoi_repo as cursor:
            cursor.execute(sql, (user_id, date, emotion_score, attendance_score, total_score, remark))
            kpi_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
            return {"success": True, "kpi_id": kpi_id}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi thêm KPI: {e}"}
def get_kpi_by_id_service(kpi_id: int):
    """Lấy KPI theo id."""
    try:
        sql = "SELECT * FROM kpi WHERE id = %s LIMIT 1"
        with nguoi_repo as cursor:
            cursor.execute(sql, (kpi_id,))
            row = cursor.fetchone()
            if row:
                kpi = KPI.from_row(row)
                return {"success": True, "kpi": kpi.__dict__}
            return {"success": False, "message": "Không tìm thấy KPI với id này"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi truy vấn KPI theo id: {e}"}

def update_kpi_service(kpi_id: int, user_id: int, date: str, emotion_score: float, attendance_score: float, total_score: float, remark: str = None):
    """Cập nhật KPI theo id."""
    try:
        sql = (
            "UPDATE kpi SET user_id=%s, date=%s, emotion_score=%s, attendance_score=%s, total_score=%s, remark=%s "
            "WHERE id=%s"
        )
        with nguoi_repo as cursor:
            cursor.execute(sql, (user_id, date, emotion_score, attendance_score, total_score, remark, kpi_id))
            if cursor.rowcount > 0:
                return {"success": True}
            return {"success": False, "message": "Không tìm thấy KPI để cập nhật"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi cập nhật KPI: {e}"}
def query_kpis_service(date: str = None, month: str = None, full_name: str = None, limit: int = 100, offset: int = 0):
    """Truy vấn danh sách KPI, có thể lọc theo ngày, tháng, tên nhân viên."""
    try:
        kpis = nguoi_repo.query_kpis(date=date, month=month, full_name=full_name, limit=limit, offset=offset)
        result = []
        for k in kpis:
            item = k.to_dict() if hasattr(k, 'to_dict') else k.__dict__.copy()
            if 'date' in item and item['date'] is not None:
                try:
                    item['date'] = item['date'].isoformat()
                except Exception:
                    item['date'] = str(item['date'])
            try:
                nguoi = nguoi_repo.get_by_id(item.get('user_id'))
                item['user_name'] = getattr(nguoi, 'username', None) if nguoi else None
            except Exception:
                item['user_name'] = None
            result.append(item)
        return {"success": True, "kpis": result}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi truy vấn KPI: {e}", "status_code": 500}


def query_kpis_for_user_service(user_id: int, date: str = None, month: str = None, limit: int = 100, offset: int = 0):
    """Truy vấn KPI cho một user, có thể lọc theo ngày/tháng."""
    try:
        kpis = nguoi_repo.query_kpis(date=date, month=month, user_id=user_id, limit=limit, offset=offset)
        result = []
        user_name = None
        if user_id is not None:
            try:
                nguoi = nguoi_repo.get_by_id(user_id)
                user_name = getattr(nguoi, 'username', None) if nguoi else None
            except Exception:
                user_name = None
        for k in kpis:
            item = k.to_dict() if hasattr(k, 'to_dict') else k.__dict__.copy()
            if 'date' in item and item['date'] is not None:
                try:
                    item['date'] = item['date'].isoformat()
                except Exception:
                    item['date'] = str(item['date'])
            if user_name is not None:
                item['user_name'] = user_name
            else:
                try:
                    nguoi = nguoi_repo.get_by_id(item.get('user_id'))
                    item['user_name'] = getattr(nguoi, 'username', None) if nguoi else None
                except Exception:
                    item['user_name'] = None
            result.append(item)
        return {"success": True, "kpis": result}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi truy vấn KPI cho user {user_id}: {e}", "status_code": 500}
