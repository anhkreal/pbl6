from db.mysql_conn import get_connection, return_connection
import pymysql
import logging

logger = logging.getLogger(__name__)

class ConnectionHelper:
    """Context manager for MySQL connections with connection pooling support."""
    
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
            logger.warning(f"Connection error during commit/rollback: {e}")
        finally:
            try:
                self.cursor.close()
            except Exception as e:
                logger.debug(f"Error closing cursor: {e}")
            
            # Return connection to pool instead of closing
            try:
                return_connection(self.conn)
            except Exception as e:
                logger.warning(f"Error returning connection to pool: {e}")
                # If return fails, try to close connection
                try:
                    self.conn.close()
                except Exception:
                    pass
