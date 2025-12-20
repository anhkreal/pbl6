from typing import Optional
from fastapi import Form
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import time
import httpx
from service.face_query_service import query_face_service as face_query_service
from service.add_embedding_simple_service import simple_add_embedding_service
from service.anti_spoofing_service import spoof_detection_service
from service.checkin_service import checkin_service as svc_checkin
from service.add_emotion_service import add_emotion_service
from service.add_emotion_service import add_emotion_service
from service.checkout_service import checkout as svc_checkout
from service.shift_attendance_service import mark_seen
from fastapi import Form
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import time
import httpx
from service.face_query_service import query_face_service as face_query_service
from service.add_embedding_simple_service import simple_add_embedding_service
from service.anti_spoofing_service import spoof_detection_service
from service.checkin_service import checkin_service as svc_checkin
from service.add_emotion_service import add_emotion_service
from service.add_emotion_service import add_emotion_service
from service.checkout_service import checkout as svc_checkout
from typing import Optional


router = APIRouter()

async def call_add_emotion_api(user_id: int, emotion: str):
    """Helper function to call the /add-emotion API."""
    try:
        async with httpx.AsyncClient() as client:
            payload = {"user_id": user_id, "emotion": emotion}
            # Assuming the app runs on localhost:8000. Adjust if needed.
            response = await client.post("http://127.0.0.1:8000/api/v1/emotions/add-emotion", json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            return response.json()
    except httpx.RequestError as e:
        print(f"[error] API call to /add-emotion failed: {e}")
        return {"success": False, "message": str(e)}
    except Exception as e:
        print(f"[error] An unexpected error occurred when calling /add-emotion: {e}")
        return {"success": False, "message": "Unexpected error during API call"}

@router.post(
    '/query',
    summary="Nhận diện khuôn mặt với Auto-Add",
    description="""
    **Nhận diện khuôn mặt từ ảnh tải lên với tính năng tự động thêm mới**
    
    API này sẽ:
    - Nhận ảnh chứa khuôn mặt từ người dùng
    - Trích xuất đặc trưng khuôn mặt từ ảnh
    - Tìm kiếm khuôn mặt tương tự trong cơ sở dữ liệu
    - **🚀 TỰ ĐỘNG THÊM MỚI**: Nếu không tìm thấy (score < 0.5), tự động gọi API `/add_embedding_simple` để thêm người mới
    - Trả về thông tin chi tiết của người được nhận diện hoặc thông tin người vừa được thêm
    
    **Tính năng mới:**
    - 🔍 **Tìm kiếm trước**: Kiểm tra xem có người phù hợp không
    - ➕ **Tự động thêm**: Nếu không tìm thấy, tự động tạo profile mới với AI prediction
    - 📊 **Thống kê**: Cho biết đây là kết quả tìm kiếm hay người mới được thêm
    
    **Lưu ý:**
    - Ảnh phải chứa ít nhất 1 khuôn mặt rõ ràng
    - Hỗ trợ các định dạng: JPG, PNG, WEBP
    - Kích thước file tối đa: 10MB
    - Threshold nhận diện: 0.5 (có thể điều chỉnh)
    """,
    response_description="Kết quả nhận diện khuôn mặt hoặc thông tin người mới được thêm tự động",
    tags=["👤 Nhận Diện Khuôn Mặt"]
)

async def query_face(
    image: UploadFile = File(
        ...,
        description="File ảnh chứa khuôn mặt cần nhận diện (JPG, PNG, WEBP)",
        media_type="image/*"
    ),
    isServing: Optional[bool] = Form(False)
):
    """
    🔍 Nhận diện khuôn mặt với tính năng auto-add
    
    1. Kiểm tra ảnh giả mạo
    2. Nếu là ảnh thật, tiến hành tìm kiếm
    3. Nếu không tìm thấy, tự động thêm mới
    4. Trả về kết quả tương ứng
    """
    # Bước 1: Kiểm tra chống giả mạo
    await image.seek(0)
    spoof_check = await spoof_detection_service.check_spoof(image)

    # Bước 2: Thực hiện query face bình thường
    # ensure file pointer is at beginning because spoof_detection_service may have read the file
    await image.seek(0)
    result = await face_query_service(image)

    # Bước 3: Kiểm tra kết quả
    if result and not result.get("error"):
        # Có kết quả tìm thấy - chỉ trả về thông tin cơ bản
        basic_result = {
            "action": "face_recognized",
            "message": f"Đã nhận diện thành công với score: {result.get('score', 'N/A')}",
            "class_id": result.get("class_id"),
            "image_id": result.get("image_id"),
            "score": result.get("score")
        }

        # Thêm thông tin người nếu có
        if result.get("nguoi"):
            nguoi_info = result["nguoi"]
            basic_result.update({
                "full_name": nguoi_info.get("full_name"),
                "age": nguoi_info.get("age"),
                "gender": nguoi_info.get("gender"),
                "avatar_base64": nguoi_info.get("avatar_base64")
            })


        # Thêm trường cảm xúc và log nếu cần
        if 'emotion' in result:
            emotion_data = result.get('emotion')
            basic_result['emotion'] = emotion_data
            print(f"[debug] Adding emotion to response: {emotion_data}")

            # Lấy emotion string một cách an toàn, xử lý cả dict và str
            emotion_str = emotion_data.get('emotion') if isinstance(emotion_data, dict) else emotion_data
            print(f"[debug] Parsed emotion string: '{emotion_str}'")

            # Log cảm xúc không tốt và cập nhật KPI
            not_good_emotions = ['Anger', 'Fear', 'Sad', 'Disgust', 'Surprise']
            if emotion_str in not_good_emotions:
                class_id = result.get("class_id")
                if class_id:
                    print(f"[debug] Phát hiện cảm xúc không tốt: '{emotion_str}'. Bắt đầu ghi log cho user_id {class_id}.")
                    await image.seek(0)  # Ensure file pointer is at the beginning
                    confidence = emotion_data.get('prob') if isinstance(emotion_data, dict) else result.get('emotion_confidence')
                    log_result = add_emotion_service(
                        user_id=int(class_id), 
                        emotion_type=emotion_str,
                        image_file=image,
                        confidence=confidence
                    )
                    print(f"[info] Logged not-good emotion '{emotion_str}' for user_id {class_id}. Result: {log_result}")

                    # --- Cập nhật KPI: CHỈ trừ điểm khi isServing=True VÀ serving_time=False ---
                    # Logic: Chỉ trừ điểm cho lần đầu tiên phát hiện khách hàng (serving_time=False)
                    # Sau đó chuyển serving_time=True để không trừ điểm lần nữa cho cùng khách
                    if isServing:  # Có khách hàng
                        from datetime import datetime
                        import pytz
                        from db.nguoi_repository import NguoiRepository
                        from service.kpi_service import get_kpi_by_user_and_date_service, update_kpi_service
                        from service.shift_attendance_service import current_shift
                        
                        tz = pytz.timezone('Asia/Ho_Chi_Minh')
                        now = datetime.now(tz)
                        today = now.date()
                        shift_name = current_shift(now)
                        
                        # Kiểm tra serving_time
                        repo = NguoiRepository()
                        shift_att = repo.get_shift_attendance(int(class_id), today, shift_name)
                        
                        if shift_att:
                            serving_time = shift_att.get('serving_time', False)
                            
                            # CHỈ trừ điểm khi serving_time=False (lần đầu gặp khách)
                            if not serving_time:
                                print(f"[info] Trừ điểm KPI cho user {class_id} - Lần đầu phát hiện khách hàng")
                                
                                kpi_res = get_kpi_by_user_and_date_service(int(class_id), str(today))
                                if kpi_res.get('success') and kpi_res.get('kpi'):
                                    from service.shift_attendance_service import EMOTION_PENALTIES
                                    
                                    kpi_id = kpi_res['kpi']['id']
                                    old_emotion_score = kpi_res['kpi'].get('emotion_score', 100.0) or 100.0
                                    attendance_score = kpi_res['kpi'].get('attendance_score', 100.0) or 100.0
                                    
                                    # Trừ điểm theo trọng số của từng cảm xúc
                                    penalty = EMOTION_PENALTIES.get(emotion_str, 5.0)
                                    new_emotion_score = max(0, old_emotion_score - penalty)
                                    total_score = new_emotion_score * 0.3 + attendance_score * 0.7
                                    remark = kpi_res['kpi'].get('remark', '')
                                    
                                    update_kpi_service(kpi_id, int(class_id), str(today), new_emotion_score, attendance_score, total_score, remark)
                                    print(f"[info] Đã trừ {penalty} điểm emotion_score cho {emotion_str}")
                            else:
                                print(f"[info] Bỏ qua trừ điểm - serving_time=True (đã trừ cho khách này rồi)")
                        else:
                            print(f"[warning] Không tìm thấy shift_attendance cho user {class_id}")

        if result.get('matched_image_emotion'):
            basic_result['matched_image_emotion'] = result.get('matched_image_emotion')

        # Cập nhật hiện diện: last_seen cho ca hiện tại
        try:
            if basic_result.get("class_id") is not None:
                # Pass isServing to mark_seen for tracking
                from service.shift_attendance_service import mark_seen
                mark_seen(int(basic_result.get("class_id")), is_serving=isServing)
        except Exception:
            pass

        result = basic_result
        status_code = 200
    else:
        # Không tìm thấy hoặc có lỗi, chỉ trả về thông báo không tìm thấy, không tự động thêm mới
        result = {
            "action": "not_found",
            "error": "Không nhận diện được người phù hợp trong hệ thống"
        }
        status_code = 404
        # --- CODE AUTO-ADD ĐÃ ĐƯỢC COMMENT LẠI ---
        # await image.seek(0)
        # add_result = await simple_add_embedding_service(image)
        # if add_result.get("status_code") and add_result["status_code"] != 200:
        #     # Có lỗi khi thêm mới
        #     result = {
        #         "action": "auto_add_failed",
        #         "error": f"Không tìm thấy kết quả và thêm mới thất bại: {add_result.get('message', 'Unknown error')}"
        #     }
        #     status_code = add_result.get("status_code", 500)
        # else:
        #     # Thêm mới thành công - chỉ trả về thông tin cơ bản
        #     nguoi_info = add_result.get("nguoi_info", {})
        #     result = {
        #         "action": "auto_added",
        #         "message": "Không tìm thấy kết quả phù hợp, đã tự động thêm người mới vào hệ thống",
        #         "class_id": add_result.get("class_id"),
        #         "image_id": add_result.get("image_id"),
        #         "full_name": nguoi_info.get("full_name"),
        #         "age": nguoi_info.get("age"),
        #         "gender": nguoi_info.get("gender"),
        #         "avatar_base64": nguoi_info.get("avatar_base64"),
        #         "predict_used": add_result.get("predict_used", False)
        #     }
        #     status_code = 200
    
    # Loại bỏ status_code khỏi response body
    if "status_code" in result:
        result = {k: v for k, v in result.items() if k != "status_code"}
    
    return JSONResponse(content=result, status_code=status_code)


@router.post('/query/checkin', summary='Nhận diện và tạo check-in nếu match')
async def query_and_checkin(
    image: UploadFile = File(..., description="File ảnh chứa khuôn mặt cần nhận diện", media_type="image/*")
):
    await image.seek(0)
    spoof_check = await spoof_detection_service.check_spoof(image)
    await image.seek(0)
    result = await face_query_service(image)
    if result and not result.get('error'):
        class_id = result.get('class_id')
        if class_id:
            try:
                from datetime import datetime
                import pytz
                from db.nguoi_repository import NguoiRepository
                from service.kpi_service import get_kpi_by_user_and_date_service
                tz = pytz.timezone('Asia/Ho_Chi_Minh')
                now = datetime.now(tz)
                today = now.date()
                nguoi_repo = NguoiRepository()
                # Kiểm tra đã có checklog chưa
                checklog = nguoi_repo.find_checklog_by_user_and_date(int(class_id), today)
                if checklog:
                    checkin_res = {"success": False, "message": "Đã tồn tại checklog cho user này trong ngày hiện tại."}
                else:
                    checkin_res = svc_checkin(user_id=int(class_id), edited_by=None, note=None)
                    # Kiểm tra đã có KPI cho user_id trong ngày hiện tại chưa
                    kpi_res = get_kpi_by_user_and_date_service(int(class_id), str(today))
                    if not (kpi_res.get('success') and kpi_res.get('kpi')):
                        # Chưa có KPI, mới tạo mới
                        from api.kpi import add_kpi
                        kpi_kwargs = {
                            "user_id": int(class_id),
                            "date": now.strftime("%Y-%m-%d"),
                            "emotion_score": 100,
                            "attendance_score": 100,
                            "total_score": 100 * 0.3 + 100 * 0.7,
                            "remark": str(100 * 0.3 + 100 * 0.7)
                        }
                        kpi_result = await add_kpi(**kpi_kwargs)
                        print(f"[debug] Gọi add_kpi trực tiếp với: {kpi_kwargs}, response: {kpi_result.body.decode()}")
                    else:
                        print(f"[debug] KPI đã tồn tại cho user_id {class_id} trong ngày {today}, không tạo mới.")
            except Exception as e:
                checkin_res = {"success": False, "message": f"Lỗi khi checkin: {e}"}
        else:
            checkin_res = {"success": False, "message": "Không xác định class_id"}
        merged = {**result, 'checkin': checkin_res}
        return JSONResponse(content=merged, status_code=200)
    else:
        return JSONResponse(content={"success": False, "message": "Không nhận diện được user"}, status_code=404)


@router.post('/query/checkout', summary='Nhận diện và tạo check-out nếu match')
async def query_and_checkout(
    image: UploadFile = File(..., description="File ảnh chứa khuôn mặt cần nhận diện", media_type="image/*")
):
    await image.seek(0)
    spoof_check = await spoof_detection_service.check_spoof(image)
    await image.seek(0)
    result = await face_query_service(image)
    if result and not result.get('error'):
        class_id = result.get('class_id')
        if class_id:
            try:
                from datetime import datetime, timedelta, time as dtime
                import pytz
                from service.kpi_service import update_kpi_service, get_kpi_by_user_and_date_service
                from db.nguoi_repository import NguoiRepository
                tz = pytz.timezone('Asia/Ho_Chi_Minh')
                now = datetime.now(tz)
                # Always treat checkout as success if update_checkin_checkout runs, even if no open check-in (overwrite allowed)
                checkout_db_res = svc_checkout(user_id=int(class_id), edited_by=None, note=None)
                # If DB update was successful or already checked out, always return success
                if checkout_db_res.get('success'):
                    checkout_res = {"success": True, "message": "Checkout thành công"}
                else:
                    # Only fail if truly not found or DB error
                    checkout_res = {"success": False, "message": checkout_db_res.get('message', 'Lỗi không xác định'), "status_code": checkout_db_res.get('status_code', 500)}

                # --- KPI Attendance Score Calculation ---
                nguoi_repo = NguoiRepository()
                today = now.date()
                checklog = nguoi_repo.find_checklog_by_user_and_date(int(class_id), today)
                attendance_score = 20
                remark = ""
                if checklog:
                    # Always use UTC+7 for all time fields
                    check_in = checklog.get('check_in')
                    check_out = checklog.get('check_out')
                    shift = checklog.get('shift') or 'day'
                    # Localize to UTC+7 if naive
                    if check_in and check_in.tzinfo is None:
                        check_in = tz.localize(check_in)
                    if check_out and check_out.tzinfo is None:
                        check_out = tz.localize(check_out)
                    # Always use now as the latest checkout (overwrite)
                    check_out = now
                    # Calculate working hours, subtract absence_time (absence_count * 10s)
                    total_seconds = (check_out - check_in).total_seconds() if (check_in and check_out) else 0
                    try:
                        absence_count = nguoi_repo.get_absence_count_for_shift(user_id=int(class_id), date_only=today, shift=shift)
                    except Exception:
                        absence_count = 0
                    absent_seconds = (absence_count or 0) * 10
                    if absent_seconds > 0:
                        total_seconds = max(0.0, total_seconds - absent_seconds)
                    total_hours = round(total_seconds / 3600.0, 2)
                    # Save new checkout and total_hours (overwrite)
                    nguoi_repo.update_checkin_checkout(row_id=checklog.get('id'), check_out=now.replace(tzinfo=None), total_hours=total_hours, status=checklog.get('status'), edited_by=None, note=None)
                    # Calculate late/early
                    # Use centralized shift config
                    from utils.shift_config import SHIFT_DAY_START, SHIFT_DAY_END, SHIFT_NIGHT_START, SHIFT_NIGHT_END
                    if shift == 'day':
                        work_start = SHIFT_DAY_START
                        work_end = SHIFT_DAY_END
                    else:
                        work_start = SHIFT_NIGHT_START
                        work_end = SHIFT_NIGHT_END
                    late_minutes = 0
                    if check_in and check_in.time() > work_start:
                        late_minutes = int((datetime.combine(today, check_in.time()) - datetime.combine(today, work_start)).total_seconds() // 60)
                        attendance_score -= min(late_minutes, 10)
                        remark += f"Đi trễ {late_minutes} phút. " if late_minutes > 0 else ""
                    early_minutes = 0
                    if check_out:
                        work_end_dt = datetime.combine(today, work_end)
                        check_out_dt = datetime.combine(today, check_out.time())
                        if check_out_dt < work_end_dt:
                            early_minutes = int((work_end_dt - check_out_dt).total_seconds() // 60)
                            attendance_score -= min(early_minutes, 10)
                            remark += f"Về sớm {early_minutes} phút. " if early_minutes > 0 else ""
                    work_score = 0
                    if total_hours >= 6:
                        work_score = 80
                    elif total_hours > 0:
                        work_score = int((total_hours / 6) * 80)
                    attendance_score = max(0, min(attendance_score, 100))
                    print(f"attendance_score = {attendance_score}, work_score = {work_score}")
                    attendance_score = attendance_score + work_score
                    remark += f"Giờ làm: {total_hours:.2f}h, điểm giờ làm: {attendance_score}."
                # --- Only update existing KPI ---
                kpi_res = get_kpi_by_user_and_date_service(int(class_id), str(today))
                if kpi_res.get('success') and kpi_res.get('kpi'):
                    kpi_id = kpi_res['kpi']['id']
                    emotion_score = kpi_res['kpi'].get('emotion_score', 100.0) or 100.0
                    total_score = emotion_score * 0.3 + attendance_score * 0.7
                    update_kpi_service(kpi_id, int(class_id), str(today), emotion_score, attendance_score, total_score, remark)
                # else: do nothing if no KPI exists
            except Exception as e:
                checkout_res = {"success": False, "message": f"Lỗi khi checkout/KPI: {e}"}
        else:
            checkout_res = {"success": False, "message": "Không xác định class_id"}
        merged = {**result, 'checkout': checkout_res}
        return JSONResponse(content=merged, status_code=200)
    else:
        return JSONResponse(content={"success": False, "message": "Không nhận diện được user"}, status_code=404)

