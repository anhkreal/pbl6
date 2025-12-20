import pymysql
from pymysql.cursors import DictCursor
import time

# Thông tin kết nối MySQL (XAMPP mặc định)
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''  # Mặc định XAMPP không có mật khẩu cho root
MYSQL_DB = 'testtest2'  # Đặt tên database bạn muốn sử dụng

# Connection pool configuration
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds

# Hàm tạo kết nối MySQL

def get_connection(retry_count=0):
    """Get MySQL connection with automatic retry on failure."""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30,
            autocommit=False
        )
        return conn
    except (pymysql.err.OperationalError, pymysql.err.InterfaceError) as e:
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))  # Exponential backoff
            return get_connection(retry_count + 1)
        else:
            raise e

# Ví dụ sử dụng:
if __name__ == '__main__':
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT VERSION()')
            version = cursor.fetchone()
            print('MySQL version:', version)
        conn.close()
    except Exception as e:
        print('Kết nối MySQL thất bại:', e)
