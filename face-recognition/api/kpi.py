
"""
KPI API endpoints
-----------------
Các endpoint quản lý KPI: thêm, cập nhật, tìm kiếm, truy vấn theo user/date.
"""

from fastapi import Path, APIRouter, Query, Form
from fastapi.responses import JSONResponse
from service.kpi_service import (
    update_kpi_service,
    get_kpi_by_id_service,
    add_kpi_service,
    query_kpis_service,
    query_kpis_for_user_service,
)

kpi_router = APIRouter()


@kpi_router.put('/kpi/{kpi_id}', summary='Cập nhật KPI theo id')
async def update_kpi(
    kpi_id: int = Path(...),
    user_id: int = Form(...),
    date: str = Form(...),
    emotion_score: float = Form(...),
    attendance_score: float = Form(...),
    total_score: float = Form(...),
    remark: str = Form(None)
):
    """Cập nhật KPI theo id."""
    result = update_kpi_service(kpi_id, user_id, date, emotion_score, attendance_score, total_score, remark)
    if result.get('success'):
        return JSONResponse(content={"success": True})
    return JSONResponse(content={"success": False, "error": result.get('message', 'Cập nhật KPI thất bại')}, status_code=404)


@kpi_router.get('/kpi/id/{kpi_id}', summary='Tìm kiếm KPI theo id')
async def get_kpi_by_id(kpi_id: int = Path(...)):
    """Tìm kiếm KPI theo id."""
    result = get_kpi_by_id_service(kpi_id)
    if result.get('success'):
        return JSONResponse(content={"success": True, "data": result['kpi']})
    return JSONResponse(content={"success": False, "error": result.get('message', 'Không tìm thấy KPI với id này')}, status_code=404)


@kpi_router.post('/add-kpi', summary='Thêm KPI cho user')
async def add_kpi(
    user_id: int = Form(...),
    date: str = Form(...),
    emotion_score: float = Form(...),
    attendance_score: float = Form(...),
    total_score: float = Form(...),
    remark: str = Form(None)
):
    """Thêm KPI cho user."""
    result = add_kpi_service(user_id, date, emotion_score, attendance_score, total_score, remark)
    if result.get('success'):
        return JSONResponse(content={"success": True, "kpi_id": result.get('kpi_id')})
    return JSONResponse(content={"success": False, "error": result.get('message', 'Thêm KPI thất bại')}, status_code=400)


@kpi_router.get('/kpi', summary='Xem danh sách KPI (lọc theo ngày hoặc tháng, theo tên nhân viên)')
def get_kpis(
    date: str = Query(None, description='YYYY-MM-DD'),
    month: str = Query(None, description='YYYY-MM'),
    full_name: str = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    """Lấy danh sách KPI, có thể lọc theo ngày, tháng, tên nhân viên."""
    result = query_kpis_service(date=date, month=month, full_name=full_name, limit=limit, offset=offset)
    status_code = result.get('status_code', 200)
    body = {k: v for k, v in result.items() if k != 'status_code'}
    return JSONResponse(content=body, status_code=status_code)


@kpi_router.get('/kpi/{user_id}', summary='Xem chi tiết KPI của nhân viên')
def get_kpis_for_user(
    user_id: int,
    date: str = Query(None, description='YYYY-MM-DD'),
    month: str = Query(None, description='YYYY-MM'),
    limit: int = Query(100),
    offset: int = Query(0),
):
    """Lấy chi tiết KPI của nhân viên theo user_id, có thể lọc theo ngày/tháng."""
    result = query_kpis_for_user_service(user_id=user_id, date=date, month=month, limit=limit, offset=offset)
    status_code = result.get('status_code', 200)
    body = {k: v for k, v in result.items() if k != 'status_code'}
    return JSONResponse(content=body, status_code=status_code)
