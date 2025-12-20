from db.mysql_conn import get_connection
import pymysql

class ConnectionHelper:
    def __enter__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        except (pymysql.err.InterfaceError, pymysql.err.OperationalError) as e:
            # Connection already closed or lost, log but don't raise
            print(f"Warning: Connection error during commit/rollback: {e}")
        finally:
            try:
                self.cursor.close()
            except Exception:
                pass
            try:
                self.conn.close()
            except Exception:
                pass
