from dataclasses import dataclass
from typing import Optional, Any, Dict
from datetime import datetime, date, timezone
import base64
def _iso_utc(dt: Optional[datetime]):
    """Return ISO-8601 string in UTC for datetime values.
    - If dt is None: return None
    - If dt is naive (assumed UTC in our DB), append 'Z'
    - If dt is aware: convert to UTC and return ISO string with offset
    """
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.isoformat() + 'Z'
        return dt.astimezone(timezone.utc).isoformat()
    return dt


def _bytes_to_b64(b: Optional[bytes]) -> Optional[str]:
    if b is None:
        return None
    try:
        return base64.b64encode(b).decode('utf-8')
    except Exception:
        return None


@dataclass
class TaiKhoan:
    """Bảng TaiKhoan: username, passwrd (lưu dưới VARCHAR theo DB)."""
    username: str
    passwrd: str

    @staticmethod
    def from_row(row: Dict[str, Any]) -> 'TaiKhoan':
        return TaiKhoan(username=row.get('username'), passwrd=row.get('passwrd'))


@dataclass
class Nguoi:
    """Mô tả bảng Nguoi (nhân viên / user profile).

    Trường chính:
    - id: INT PK
    - username, pin, full_name, age, address, phone
    - role, shift, status
    - avatar_url: BLOB (bytes)
    - created_at, updated_at: datetime
    """
    id: int
    username: str
    pin: Optional[str]
    full_name: str
    age: Optional[int]
    address: Optional[str]
    phone: Optional[str]
    gender: Optional[str]
    role: str
    shift: str
    status: str
    avatar_url: Optional[bytes]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @staticmethod
    def from_row(row: Dict[str, Any]) -> 'Nguoi':
        return Nguoi(
            id=row.get('id'),
            username=row.get('username'),
            pin=row.get('pin'),
            full_name=row.get('full_name') or row.get('ten'),
            age=row.get('age'),
            address=row.get('address') or row.get('noio'),
            phone=row.get('phone'),
            gender=row.get('gender') or row.get('gioitinh') or row.get('gioi_tinh'),
            role=row.get('role'),
            shift=row.get('shift') or 'day',
            status=row.get('status') or 'working',
            avatar_url=row.get('avatar_url') or row.get('avatar'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )

    def to_dict(self, include_avatar_base64: bool = False) -> Dict[str, Any]:
        d = {
            'id': self.id,
            'username': self.username,
            'pin': self.pin,
            'full_name': self.full_name,
            'age': self.age,
            'address': self.address,
            'phone': self.phone,
            'gender': self.gender,
            'role': self.role,
            'shift': self.shift,
            'status': self.status,
            'created_at': _iso_utc(self.created_at),
            'updated_at': _iso_utc(self.updated_at),
        }
        if include_avatar_base64:
            d['avatar_base64'] = _bytes_to_b64(self.avatar_url)
        return d


@dataclass
class KhuonMat:
    id: int
    user_id: int
    image_url: Optional[bytes]
    added_at: Optional[datetime]
    updated_at: Optional[datetime]

    @staticmethod
    def from_row(row: Dict[str, Any]) -> 'KhuonMat':
        return KhuonMat(
            id=row.get('id'),
            user_id=row.get('user_id') or row.get('nguoi_id'),
            image_url=row.get('image_url') or row.get('image'),
            added_at=row.get('added_at'),
            updated_at=row.get('updated_at')
        )

    def to_dict(self, include_image_base64: bool = False) -> Dict[str, Any]:
        d = {
            'id': self.id,
            'user_id': self.user_id,
            'added_at': _iso_utc(self.added_at),
            'updated_at': _iso_utc(self.updated_at),
            # NOTE: image_url is a BLOB storing raw image bytes in DB schema.
            # It is intentionally exposed as base64 only when include_image_base64=True.
        }
        if include_image_base64:
            d['image_base64'] = _bytes_to_b64(self.image_url)
        return d


@dataclass
class EmotionLog:
    id: int
    user_id: int
    camera_id: Optional[int]
    emotion_type: str
    confidence: float
    captured_at: Optional[datetime]
    image: Optional[bytes]
    note: Optional[str]

    @staticmethod
    def from_row(row: Dict[str, Any]) -> 'EmotionLog':
        return EmotionLog(
            id=row.get('id'),
            user_id=row.get('user_id'),
            camera_id=row.get('camera_id'),
            emotion_type=row.get('emotion_type'),
            confidence=row.get('confidence'),
            captured_at=row.get('captured_at'),
            image=row.get('image'),
            note=row.get('note')
        )

    def to_dict(self, include_image_base64: bool = False) -> Dict[str, Any]:
        d = {
            'id': self.id,
            'user_id': self.user_id,
            'camera_id': self.camera_id,
            'emotion_type': self.emotion_type,
            'confidence': self.confidence,
            'captured_at': _iso_utc(self.captured_at),
            'note': self.note
        }
        if include_image_base64:
            d['image_base64'] = _bytes_to_b64(self.image)
        return d


@dataclass
class Camera:
    id: int
    name: str
    ip_address: Optional[str]
    port: Optional[int]
    protocol: str
    username: Optional[str]
    password: Optional[str]
    stream_name: Optional[str]
    location: Optional[str]
    status: str
    last_connected: Optional[datetime]

    @staticmethod
    def from_row(row: Dict[str, Any]) -> 'Camera':
        return Camera(
            id=row.get('id'),
            name=row.get('name'),
            ip_address=row.get('ip_address'),
            port=row.get('port'),
            protocol=row.get('protocol'),
            username=row.get('username'),
            password=row.get('password'),
            stream_name=row.get('stream_name'),
            location=row.get('location'),
            status=row.get('status') or 'active',
            last_connected=row.get('last_connected')
        )


@dataclass
class CheckLog:
    id: int
    user_id: int
    date: Optional[date]
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    total_hours: Optional[float]
    shift: Optional[str]
    status: Optional[str]
    edited_by: Optional[int]
    note: Optional[str]

    @staticmethod
    def from_row(row: Dict[str, Any]) -> 'CheckLog':
        return CheckLog(
            id=row.get('id'),
            user_id=row.get('user_id'),
            date=row.get('date'),
            check_in=row.get('check_in'),
            check_out=row.get('check_out'),
            total_hours=row.get('total_hours'),
            shift=row.get('shift'),
            status=row.get('status'),
            edited_by=row.get('edited_by'),
            note=row.get('note')
        )


@dataclass
class KPI:
    id: int
    user_id: int
    date: Optional[date]
    emotion_score: Optional[float]
    attendance_score: Optional[float]
    total_score: Optional[float]
    remark: Optional[str]

    @staticmethod
    def from_row(row: Dict[str, Any]) -> 'KPI':
        return KPI(
            id=row.get('id'),
            user_id=row.get('user_id'),
            date=row.get('date'),
            emotion_score=row.get('emotion_score'),
            attendance_score=row.get('attendance_score'),
            total_score=row.get('total_score'),
            remark=row.get('remark')
        )

