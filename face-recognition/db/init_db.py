"""Database initializer.

Creates the MySQL database named in `mysql_conn.MYSQL_DB` and the tables
used by this project. Safe to run multiple times (uses IF NOT EXISTS).

Usage:
    python db/init_db.py

The script connects to the MySQL server using credentials from
`db/mysql_conn.py`. If your MySQL user does not have privilege to create
databases, run the CREATE DATABASE step manually or use a privileged user.
"""
from __future__ import annotations
import traceback
import os
import sys

# Ensure project root is on sys.path so `from db import mysql_conn` works
# regardless of current working directory or whether the script is executed
# directly (python db/init_db.py) or as a module (python -m db.init_db).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db import mysql_conn
import pymysql


TABLE_SQLS = [
    # accounts
    """
    CREATE TABLE IF NOT EXISTS taikhoan (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL UNIQUE,
        passwrd VARCHAR(255) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # people / employees
    """
    CREATE TABLE IF NOT EXISTS nhanvien (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100),
        pin VARCHAR(50),
        full_name VARCHAR(255),
        age INT,
        address TEXT,
        phone VARCHAR(50),
        gender VARCHAR(50),
        role VARCHAR(50),
        shift VARCHAR(50),
        status VARCHAR(50),
        avatar_url LONGBLOB,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # face images
    """
    CREATE TABLE IF NOT EXISTS khuonmat (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        image_url LONGBLOB,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_khuonmat_user FOREIGN KEY (user_id) REFERENCES nhanvien(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # emotion logs
    """
    CREATE TABLE IF NOT EXISTS emotion_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        camera_id INT,
        emotion_type VARCHAR(100),
        confidence DOUBLE,
        captured_at DATETIME,
        image LONGBLOB,
        note TEXT,
        CONSTRAINT fk_emotion_user FOREIGN KEY (user_id) REFERENCES nhanvien(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # cameras
    """
    CREATE TABLE IF NOT EXISTS camera (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        ip_address VARCHAR(100),
        port INT,
        protocol VARCHAR(50),
        username VARCHAR(100),
        password VARCHAR(255),
        stream_name VARCHAR(255),
        location VARCHAR(255),
        status VARCHAR(50),
        last_connected DATETIME
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # attendance / check logs
    """
    CREATE TABLE IF NOT EXISTS checklog (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        date DATE,
        check_in DATETIME,
        check_out DATETIME,
        total_hours DOUBLE,
        shift VARCHAR(50),
        status VARCHAR(50),
        edited_by INT,
        note TEXT,
        CONSTRAINT fk_checklog_user FOREIGN KEY (user_id) REFERENCES nhanvien(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # kpi
    """
    CREATE TABLE IF NOT EXISTS kpi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        date DATE,
        emotion_score DOUBLE,
        attendance_score DOUBLE,
        total_score DOUBLE,
        remark TEXT,
        CONSTRAINT fk_kpi_user FOREIGN KEY (user_id) REFERENCES nhanvien(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # per-shift attendance tracking (absence_count and last_seen per user per shift/day)
    """
    CREATE TABLE IF NOT EXISTS shift_attendance (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        date DATE NOT NULL,
        shift VARCHAR(50) NOT NULL, -- 'day' (08:00-14:00) or 'night' (14:00-20:00)
        absence_count INT DEFAULT 0,
        last_seen DATETIME NULL,
        serving_time TINYINT(1) DEFAULT 0, -- True khi đang phục vụ khách
        no_serving_count INT DEFAULT 0, -- Đếm lần liên tiếp không phục vụ
        updated_at DATETIME NULL,
        UNIQUE KEY uniq_shift_user_date (user_id, date, shift),
        CONSTRAINT fk_shift_att_user FOREIGN KEY (user_id) REFERENCES nhanvien(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]


def create_database_and_tables(host=None, port=None, user=None, password=None, db_name=None):
    host = host or mysql_conn.MYSQL_HOST
    port = port or mysql_conn.MYSQL_PORT
    user = user or mysql_conn.MYSQL_USER
    password = password if password is not None else mysql_conn.MYSQL_PASSWORD
    db_name = db_name or mysql_conn.MYSQL_DB

    # Connect without specifying database to allow CREATE DATABASE
    conn = None
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
                               autocommit=False)
        with conn.cursor() as cursor:
            print(f"Creating database {db_name} if not exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute(f"USE `{db_name}`;")
            for sql in TABLE_SQLS:
                print("Executing table DDL...")
                cursor.execute(sql)

            # Ensure new shift_attendance columns exist even on pre-existing DBs
            print("Ensuring shift_attendance columns exist...")
            cursor.execute("SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='shift_attendance' AND COLUMN_NAME='serving_time'", (db_name,))
            has_serving = cursor.fetchone().get('cnt', 0) > 0
            if not has_serving:
                cursor.execute("ALTER TABLE shift_attendance ADD COLUMN serving_time TINYINT(1) DEFAULT 0 COMMENT 'True khi nhân viên đang phục vụ khách hàng'")

            cursor.execute("SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='shift_attendance' AND COLUMN_NAME='no_serving_count'", (db_name,))
            has_no_serv = cursor.fetchone().get('cnt', 0) > 0
            if not has_no_serv:
                cursor.execute("ALTER TABLE shift_attendance ADD COLUMN no_serving_count INT DEFAULT 0 COMMENT 'Đếm số lần liên tiếp không phát hiện isServing (reset về 0 sau 2 lần)'")

            # Ensure index exists
            cursor.execute("SELECT COUNT(*) AS cnt FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='shift_attendance' AND INDEX_NAME='idx_shift_attendance_serving'", (db_name,))
            has_index = cursor.fetchone().get('cnt', 0) > 0
            if not has_index:
                cursor.execute("CREATE INDEX idx_shift_attendance_serving ON shift_attendance(user_id, date, shift, serving_time)")
        conn.commit()
        print("Database and tables created/verified successfully.")
    except Exception as e:
        if conn:
            conn.rollback()
        print("Error while creating database/tables:")
        traceback.print_exc()
        raise
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    print("Initializing MySQL database and tables...")
    create_database_and_tables()
    print("Done.")
