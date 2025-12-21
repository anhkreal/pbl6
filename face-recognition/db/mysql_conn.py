import pymysql
from pymysql.cursors import DictCursor
import time
import threading
from queue import Queue, Empty
import logging

# Thông tin kết nối MySQL (XAMPP mặc định)
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''  # Mặc định XAMPP không có mật khẩu cho root
MYSQL_DB = 'testtest2'  # Đặt tên database bạn muốn sử dụng

# Connection pool configuration
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds
POOL_SIZE = 10  # Số lượng connection tối đa trong pool
POOL_TIMEOUT = 30  # Timeout khi lấy connection từ pool (seconds)
CONNECTION_MAX_AGE = 300  # Connection sống tối đa 5 phút (seconds)

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Thread-safe MySQL connection pool."""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._pool = Queue(maxsize=POOL_SIZE)
        self._active_connections = 0
        self._pool_lock = threading.Lock()
        self._connection_times = {}  # Track connection creation time
        self._initialized = True
        
        # Pre-fill pool with initial connections
        for _ in range(min(3, POOL_SIZE)):
            try:
                conn = self._create_new_connection()
                if conn:
                    self._pool.put(conn, block=False)
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")
    
    def _create_new_connection(self, retry_count=0):
        """Create a new MySQL connection with retry mechanism."""
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
            self._connection_times[id(conn)] = time.time()
            return conn
        except (pymysql.err.OperationalError, pymysql.err.InterfaceError) as e:
            if retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (retry_count + 1))
                return self._create_new_connection(retry_count + 1)
            else:
                raise e
    
    def _is_connection_valid(self, conn):
        """Check if connection is still valid and not too old."""
        if conn is None:
            return False
        
        # Check age
        conn_id = id(conn)
        if conn_id in self._connection_times:
            age = time.time() - self._connection_times[conn_id]
            if age > CONNECTION_MAX_AGE:
                return False
        
        # Check if connection is alive
        try:
            conn.ping(reconnect=False)
            return True
        except Exception:
            return False
    
    def get_connection(self, timeout=POOL_TIMEOUT):
        """Get a connection from the pool (blocking with timeout)."""
        start_time = time.time()
        
        while True:
            # Try to get from pool first
            try:
                conn = self._pool.get(block=False)
                
                # Validate connection
                if self._is_connection_valid(conn):
                    with self._pool_lock:
                        self._active_connections += 1
                    return conn
                else:
                    # Connection invalid, close it and try to create new one
                    try:
                        conn.close()
                    except Exception:
                        pass
                    
                    conn_id = id(conn)
                    if conn_id in self._connection_times:
                        del self._connection_times[conn_id]
            
            except Empty:
                pass
            
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Could not get connection from pool within {timeout} seconds")
            
            # Try to create new connection if under limit
            with self._pool_lock:
                total_connections = self._pool.qsize() + self._active_connections
                if total_connections < POOL_SIZE:
                    try:
                        conn = self._create_new_connection()
                        self._active_connections += 1
                        return conn
                    except Exception as e:
                        logger.error(f"Failed to create new connection: {e}")
            
            # Wait a bit before retry
            time.sleep(0.1)
    
    def return_connection(self, conn):
        """Return a connection to the pool."""
        if conn is None:
            return
        
        with self._pool_lock:
            self._active_connections = max(0, self._active_connections - 1)
        
        # Check if connection is still valid
        if self._is_connection_valid(conn):
            try:
                # Rollback any pending transaction before returning
                conn.rollback()
                self._pool.put(conn, block=False)
                return
            except Exception as e:
                logger.warning(f"Failed to return connection to pool: {e}")
        
        # Connection invalid, close it
        try:
            conn.close()
        except Exception:
            pass
        
        conn_id = id(conn)
        if conn_id in self._connection_times:
            del self._connection_times[conn_id]
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get(block=False)
                conn.close()
                conn_id = id(conn)
                if conn_id in self._connection_times:
                    del self._connection_times[conn_id]
            except Exception:
                pass


# Global connection pool instance
_connection_pool = None
_pool_init_lock = threading.Lock()


def get_pool():
    """Get the global connection pool instance (singleton)."""
    global _connection_pool
    if _connection_pool is None:
        with _pool_init_lock:
            if _connection_pool is None:
                _connection_pool = ConnectionPool()
    return _connection_pool


def get_connection(retry_count=0):
    """Get MySQL connection from pool. Backward compatible interface."""
    pool = get_pool()
    return pool.get_connection()


def return_connection(conn):
    """Return connection to pool."""
    pool = get_pool()
    pool.return_connection(conn)

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
