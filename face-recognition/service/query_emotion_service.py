from db.nguoi_repository import NguoiRepository
from utils.timezone import parse_to_utc_naive

nguoi_repo = NguoiRepository()


def query_emotion_service(user_id: int = None, emotion_type: str = None, start_ts: str = None, end_ts: str = None, limit: int = 100, offset: int = 0, include_image_base64: bool = False):
    try:
        # Convert empty strings to None
        if user_id == "":
            user_id = None

        # Parse timestamp filters: assume input timestamps are local (Asia/Ho_Chi_Minh) when naive
        start_dt = parse_to_utc_naive(start_ts)
        end_dt = parse_to_utc_naive(end_ts)

        faces = nguoi_repo.query_emotion_logs(user_id=user_id, emotion_type=emotion_type, start_ts=start_dt, end_ts=end_dt, limit=limit, offset=offset)
        total_all = nguoi_repo.count_emotion_logs(user_id=user_id, emotion_type=emotion_type, start_ts=start_dt, end_ts=end_dt)
        result = []
        for f in faces:
            d = f.to_dict(include_image_base64=include_image_base64)
            try:
                nguoi = nguoi_repo.get_by_id(f.user_id)
                d['user_name'] = getattr(nguoi, 'username', None) if nguoi else None
            except Exception:
                d['user_name'] = None
            result.append(d)
        return {"success": True, "total": len(result), "total_all": int(total_all), "logs": result}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi truy vấn emotion logs: {e}", "status_code": 500}
