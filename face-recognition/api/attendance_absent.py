from fastapi import APIRouter, Path, Form, Query
from fastapi.responses import JSONResponse
from service.attendance_absence_service import mark_absent_service, generate_absent_report

attendance_absent_router = APIRouter()


@attendance_absent_router.post('/checklog/mark-absent/{id}', summary='Đánh dấu vắng cho user trong ngày hiện tại')
def mark_absent(id: int = Path(...), note: str = Form(None)):
    # No authentication required per device flow
    result = mark_absent_service(user_id=id, note=note, edited_by=None)
    status_code = result.get('status_code', 200)
    body = {k: v for k, v in result.items() if k != 'status_code'}
    return JSONResponse(content=body, status_code=status_code)


@attendance_absent_router.get('/attendance/absent-report', summary='Báo cáo nhân viên vắng theo ngày và ca')
def absent_report(date: str = Query(None), shift: str = Query('day'), write_log: bool = Query(True)):
    result = generate_absent_report(date=date, shift=shift, write_log=write_log)
    status_code = result.get('status_code', 200)
    body = {k: v for k, v in result.items() if k != 'status_code'}
    return JSONResponse(content=body, status_code=status_code)
