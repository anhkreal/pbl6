
from db.models import Nguoi
from datetime import datetime
import pytz
import traceback
from db.connection_helper import ConnectionHelper


class NguoiRepository(ConnectionHelper):
    """Repository cho bảng `nhanvien` (tên bảng trong DB: nhanvien).

    Lưu ý: giữ tên class là `NguoiRepository` để tương thích với phần còn lại của code.
    """

    def _remove_accents(self, s: str) -> str:
        import unicodedata
        if not s:
            return ''
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

    def search_nguoi_paged(self, query: str = "", page: int = 1, page_size: int = 15, sort_by: str = "full_name_asc", status: str = None, shift: str = None):
        """Tìm kiếm nhân viên phân trang; tìm trên full_name, address, phone, username, gender."""
        sort_mapping = {
            'full_name_asc': 'full_name ASC',
            'full_name_desc': 'full_name DESC',
            'age_asc': 'age ASC',
            'age_desc': 'age DESC',
            'id_asc': 'id ASC',
            'id_desc': 'id DESC',
            'created_asc': 'created_at ASC',
            'created_desc': 'created_at DESC'
        }
        order_clause = sort_mapping.get(sort_by, 'full_name ASC')

        offset = (page - 1) * page_size
        sql = "SELECT * FROM nhanvien"
        params: list = []
        where_clauses: list = []
        if query:
            q = query.lower()
            where_clauses.append("(LOWER(full_name) LIKE %s OR LOWER(address) LIKE %s OR LOWER(phone) LIKE %s OR LOWER(username) LIKE %s OR CAST(age AS CHAR) LIKE %s OR LOWER(gender) LIKE %s)")
            params += [f"%{q}%"] * 6

        if status:
            where_clauses.append("LOWER(status) = %s")
            params.append(status.lower())

        if shift:
            where_clauses.append("LOWER(shift) = %s")
            params.append(shift.lower())

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += f" ORDER BY {order_clause} LIMIT %s OFFSET %s"
        params += [page_size, offset]

        with self as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            # count
            count_sql = "SELECT COUNT(*) as total FROM nhanvien"
            count_params: list = []
            if where_clauses:
                count_sql += " WHERE " + " AND ".join(where_clauses)
                count_params = params[:-2]
            cursor.execute(count_sql, tuple(count_params))
            total = cursor.fetchone()['total']

            if query:
                filtered = []
                q_no_acc = self._remove_accents(query.lower())
                for row in rows:
                    name = (row.get('full_name') or '')
                    addr = (row.get('address') or '')
                    phone = str(row.get('phone') or '')
                    username = (row.get('username') or '')
                    gender = (row.get('gender') or '')
                    if (
                        q_no_acc in self._remove_accents(name.lower())
                        or q_no_acc in self._remove_accents(addr.lower())
                        or q_no_acc in self._remove_accents(username.lower())
                        or q_no_acc in self._remove_accents(gender.lower())
                        or query.lower() in phone.lower()
                    ):
                        filtered.append(Nguoi.from_row(row))
                return {'nguoi_list': filtered, 'total': total}

            return {'nguoi_list': [Nguoi.from_row(row) for row in rows], 'total': total}

    def search_nguoi(self, query: str = ""):
        sql = "SELECT * FROM nhanvien"
        params: list = []
        if query:
            q = query.lower()
            sql += " WHERE LOWER(full_name) LIKE %s OR LOWER(address) LIKE %s OR LOWER(phone) LIKE %s OR LOWER(username) LIKE %s OR CAST(age AS CHAR) LIKE %s OR LOWER(gender) LIKE %s"
            params = [f"%{q}%"] * 6
        with self as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            if query:
                filtered = []
                q_no_acc = self._remove_accents(query.lower())
                for row in rows:
                    name = (row.get('full_name') or '')
                    addr = (row.get('address') or '')
                    phone = str(row.get('phone') or '')
                    username = (row.get('username') or '')
                    gender = (row.get('gender') or '')
                    if (
                        q_no_acc in self._remove_accents(name.lower())
                        or q_no_acc in self._remove_accents(addr.lower())
                        or q_no_acc in self._remove_accents(username.lower())
                        or q_no_acc in self._remove_accents(gender.lower())
                        or query.lower() in phone.lower()
                    ):
                        filtered.append(Nguoi.from_row(row))
                return filtered
            return [Nguoi.from_row(row) for row in rows]

    def get_total_and_examples(self, limit=5):
        with self as cursor:
            cursor.execute('SELECT COUNT(*) as total FROM nhanvien')
            total = cursor.fetchone()['total']
            cursor.execute('SELECT * FROM nhanvien LIMIT %s', (limit,))
            examples = [row for row in cursor.fetchall()]
        return total, examples

    def truncate_all(self):
        with self as cursor:
            cursor.execute('TRUNCATE TABLE nhanvien')

    def add(self, nguoi: Nguoi):
        sql = """
        REPLACE INTO nhanvien (id, username, pin, full_name, age, address, phone, gender, role, shift, status, avatar_url, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Ensure timestamps are set to now if not provided
        tz = pytz.timezone('Asia/Ho_Chi_Minh')
        created_at = getattr(nguoi, 'created_at', None) or datetime.now(tz)
        updated_at = getattr(nguoi, 'updated_at', None) or datetime.now(tz)
        with self as cursor:
            cursor.execute(sql, (
                getattr(nguoi, 'id', None), nguoi.username, nguoi.pin, nguoi.full_name, nguoi.age, nguoi.address,
                nguoi.phone, nguoi.gender, nguoi.role, nguoi.shift, nguoi.status, getattr(nguoi, 'avatar_url', None),
                created_at, updated_at
            ))
            # If inserted id is auto-generated (None passed), return lastrowid
            try:
                return cursor.lastrowid
            except Exception:
                return getattr(nguoi, 'id', None)

    def delete_by_id(self, id_):
        sql = "DELETE FROM nhanvien WHERE id = %s"
        with self as cursor:
            cursor.execute(sql, (id_,))
            return cursor.rowcount

    def add_khuonmat(self, user_id, image_bytes: bytes, image_id=None):
        """Insert a khuonmat (face image) record linked to a user.

        If the `khuonmat` table lacks an `image_id` column, attempt to add it.
        """
        # Try to ensure image_id column exists (best-effort)
        try:
            with self as cursor:
                try:
                    cursor.execute('ALTER TABLE khuonmat ADD COLUMN IF NOT EXISTS image_id BIGINT NULL')
                except Exception:
                    # Older MySQL may not support IF NOT EXISTS; try adding and ignore error
                    try:
                        cursor.execute('ALTER TABLE khuonmat ADD COLUMN image_id BIGINT NULL')
                    except Exception:
                        pass

                tz = pytz.timezone('Asia/Ho_Chi_Minh')
                added_at = datetime.now(tz)
                updated_at = datetime.now(tz)
                sql = "INSERT INTO khuonmat (user_id, image_id, image_url, added_at, updated_at) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (user_id, image_id, image_bytes, added_at, updated_at))
                return cursor.lastrowid
        except Exception:
            traceback.print_exc()
            return None

    def delete_by_class_id(self, class_id):
        """Compatibility shim: delete person(s) by class_id.

        Many service modules still call delete_by_class_id(class_id). In our
        schema class_id==id for nhanvien, so delegate to delete_by_id to
        avoid runtime AttributeError.
        """
        try:
            return self.delete_by_id(int(class_id))
        except Exception:
            return 0

    def get_by_id(self, id_):
        sql = "SELECT * FROM nhanvien WHERE id = %s"
        with self as cursor:
            cursor.execute(sql, (id_,))
            row = cursor.fetchone()
            if row:
                return Nguoi.from_row(row)
            return None

    def get_by_username(self, username: str):
        sql = "SELECT * FROM nhanvien WHERE username = %s"
        with self as cursor:
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
            if row:
                return Nguoi.from_row(row)
            return None

    def update_by_id(self, id_, nguoi: Nguoi):
        sql = """
        UPDATE nhanvien
        SET username = %s, pin = %s, full_name = %s, age = %s, address = %s, phone = %s, gender = %s, role = %s, shift = %s, status = %s, avatar_url = %s, updated_at = %s
        WHERE id = %s
        """
        # Ensure updated_at is set to now if not provided
        tz = pytz.timezone('Asia/Ho_Chi_Minh')
        updated_at = getattr(nguoi, 'updated_at', None) or datetime.now(tz)
        with self as cursor:
            cursor.execute(sql, (
                nguoi.username, nguoi.pin, nguoi.full_name, nguoi.age, nguoi.address, nguoi.phone, nguoi.gender,
                nguoi.role, nguoi.shift, nguoi.status, getattr(nguoi, 'avatar_url', None), updated_at, id_
            ))
            return cursor.rowcount

    def get_khuonmats_by_user(self, user_id: int):
        sql = "SELECT * FROM khuonmat WHERE user_id = %s ORDER BY added_at DESC"
        with self as cursor:
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            from db.models import KhuonMat
            return [KhuonMat.from_row(r) for r in rows]

    def delete_khuonmat_by_id(self, khuonmat_id: int):
        """Delete a khuonmat row by id. Returns number of affected rows."""
        try:
            with self as cursor:
                cursor.execute('DELETE FROM khuonmat WHERE id = %s', (khuonmat_id,))
                return cursor.rowcount
        except Exception:
            traceback.print_exc()
            return 0

    def delete_khuonmats_by_user(self, user_id: int):
        """Delete all khuonmat rows for a given user_id. Returns number of deleted rows."""
        try:
            with self as cursor:
                cursor.execute('DELETE FROM khuonmat WHERE user_id = %s', (user_id,))
                return cursor.rowcount
        except Exception:
            traceback.print_exc()
            return 0

    def add_emotion_log(self, user_id: int = None, camera_id: int = None, emotion_type: str = None, confidence: float = None, image_bytes: bytes = None, note: str = None):
        """Insert an emotion_log record. Returns lastrowid or None on failure."""
        try:
            with self as cursor:
                tz = pytz.timezone('Asia/Ho_Chi_Minh')
                captured_at = datetime.now(tz)
                sql = "INSERT INTO emotion_log (user_id, camera_id, emotion_type, confidence, image, captured_at, note) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (user_id, camera_id, emotion_type, confidence, image_bytes, captured_at, note))
                return cursor.lastrowid
        except Exception:
            traceback.print_exc()
            return None

    def query_emotion_logs(self, user_id: int = None, emotion_type: str = None, start_ts=None, end_ts=None, limit: int = 100, offset: int = 0):
        """Query emotion_log with optional filters and pagination."""
        sql = "SELECT * FROM emotion_log"
        where = []
        params = []
        if user_id is not None:
            where.append("user_id = %s")
            params.append(user_id)
        if emotion_type:
            where.append("LOWER(emotion_type) = %s")
            params.append(emotion_type.lower())
        if start_ts:
            where.append("captured_at >= %s")
            params.append(start_ts)
        if end_ts:
            where.append("captured_at <= %s")
            params.append(end_ts)

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY captured_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with self as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            from db.models import EmotionLog
            return [EmotionLog.from_row(r) for r in rows]

    def delete_emotion_by_id(self, emotion_id: int):
        try:
            with self as cursor:
                cursor.execute('DELETE FROM emotion_log WHERE id = %s', (emotion_id,))
                return cursor.rowcount
        except Exception:
            traceback.print_exc()
            return 0

    def find_open_checkin_by_date(self, user_id: int, date_only):
        """Return a checklog row for the given user and date where check_out is NULL, or None."""
        sql = "SELECT * FROM checklog WHERE user_id = %s AND DATE(date) = %s AND check_out IS NULL LIMIT 1"
        with self as cursor:
            cursor.execute(sql, (user_id, date_only))
            row = cursor.fetchone()
            return row

    def add_checkin(self, user_id: int, shift: str, status: str, edited_by: int = None, note: str = None):
        """Insert a check-in record and return lastrowid."""
        try:
            with self as cursor:
                tz = pytz.timezone('Asia/Ho_Chi_Minh')
                now = datetime.now(tz)
                sql = "INSERT INTO checklog (user_id, date, check_in, shift, status, edited_by, note) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (user_id, now.date(), now, shift, status, edited_by, note))
                return cursor.lastrowid
        except Exception:
            traceback.print_exc()
            return None

    def update_checkin_checkout(self, row_id: int, check_out, total_hours: float = None, status: str = None, edited_by: int = None, note: str = None):
        """Update a checklog row with checkout time, total_hours and optional status/note."""
        try:
            with self as cursor:
                sql = """
                UPDATE checklog
                SET check_out = %s, total_hours = %s, status = COALESCE(%s, status), edited_by = COALESCE(%s, edited_by), note = COALESCE(%s, note)
                WHERE id = %s
                """
                cursor.execute(sql, (check_out, total_hours, status, edited_by, note, row_id))
                return cursor.rowcount > 0
        except Exception:
            traceback.print_exc()
            return False

    def query_checklogs(self, date=None, date_from=None, date_to=None, full_name=None, user_id: int = None, status: str = None, limit: int = 100, offset: int = 0):
        """Query checklog entries with optional filters.

        - date: single date (date object or YYYY-MM-DD string) to match DATE(date)
        - date_from/date_to: range filter (inclusive)
        - full_name: partial match on nhanvien.full_name (joins nhanvien)
        - user_id: exact match on c.user_id
        - status: exact status match
        Returns list of rows (dicts) joined with nhanvien info.
        """
        sql = "SELECT c.*, n.full_name FROM checklog c LEFT JOIN nhanvien n ON c.user_id = n.id"
        where = []
        params = []

        if date:
            where.append("DATE(c.date) = %s")
            params.append(date)
        if date_from:
            where.append("DATE(c.date) >= %s")
            params.append(date_from)
        if date_to:
            where.append("DATE(c.date) <= %s")
            params.append(date_to)
        if user_id is not None:
            where.append("c.user_id = %s")
            params.append(int(user_id))
        if full_name:
            where.append("LOWER(n.full_name) LIKE %s")
            params.append(f"%{full_name.lower()}%")
        if status:
            where.append("LOWER(c.status) = %s")
            params.append(status.lower())

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY c.date DESC, c.check_in DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with self as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            from db.models import CheckLog
            return [CheckLog.from_row(r) for r in rows]

    def query_kpis(self, date=None, month=None, full_name=None, user_id: int = None, limit: int = 100, offset: int = 0):
        """Query KPI entries with optional filters.

        - date: YYYY-MM-DD to match DATE(k.date)
        - month: YYYY-MM to match YEAR_MONTH (i.e., DATE_FORMAT)
        - full_name: partial match on nhanvien.full_name (join nhanvien)
        Returns list of KPI.from_row objects.
        """
        sql = "SELECT k.*, n.full_name FROM kpi k LEFT JOIN nhanvien n ON k.user_id = n.id"
        where = []
        params = []

        if user_id is not None:
            where.append("k.user_id = %s")
            params.append(int(user_id))

        if date:
            where.append("DATE(k.date) = %s")
            params.append(date)
        if month:
            # month expected as YYYY-MM
            where.append("DATE_FORMAT(k.date, '%%Y-%%m') = %s")
            params.append(month)
        if full_name:
            where.append("LOWER(n.full_name) LIKE %s")
            params.append(f"%{full_name.lower()}%")

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY k.date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with self as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            from db.models import KPI
            return [KPI.from_row(r) for r in rows]

    def find_checklog_by_id(self, row_id: int):
        sql = "SELECT c.*, n.full_name FROM checklog c LEFT JOIN nhanvien n ON c.user_id = n.id WHERE c.id = %s LIMIT 1"
        with self as cursor:
            cursor.execute(sql, (row_id,))
            row = cursor.fetchone()
            return row

    def find_checklog_by_user_and_date(self, user_id: int, date_only):
        sql = "SELECT * FROM checklog WHERE user_id = %s AND DATE(date) = %s LIMIT 1"
        with self as cursor:
            cursor.execute(sql, (user_id, date_only))
            return cursor.fetchone()

    def update_checklog_status(self, row_id: int, status: str = None, edited_by: int = None, note: str = None):
        try:
            with self as cursor:
                sql = "UPDATE checklog SET status = COALESCE(%s, status), edited_by = COALESCE(%s, edited_by), note = COALESCE(%s, note) WHERE id = %s"
                cursor.execute(sql, (status, edited_by, note, row_id))
                return cursor.rowcount > 0
        except Exception:
            traceback.print_exc()
            return False
