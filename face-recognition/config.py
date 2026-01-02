# Face Recognition API - Configuration
# Version: 2.0.0 - MySQL Authentication System
# Updated: August 2025

# AI Model Configuration
MODEL_PATH = 'model/glint360k_cosface_r100_fp16_0.1.pth'  # Primary ArcFace model
MODEL_VERSION = 'r100'
# MODEL_PATH = 'model/glint360k_cosface_r18_fp16_0.1.pth'  # Primary ArcFace model
# MODEL_VERSION = 'r18'
AGE_MODEL=  'model/ModelAge.pth' # Age prediction model
GENDER_MODEL = 'model/ModelGender.pth' # Gender prediction model


# FAISS Vector Database Configuration
FAISS_INDEX_PATH = 'index/faiss_db_r18.index'
FAISS_META_PATH = 'index/faiss_db_r18_meta.npz'


# ============================================================
# WORK SHIFT CONFIGURATION - Cấu hình khung giờ làm việc
# ============================================================
from datetime import time

# Ca sáng (Day Shift)
SHIFT_DAY_START = time(8, 0, 0)      # Bắt đầu ca sáng: 08:00
SHIFT_DAY_END = time(14, 0, 0)        # Kết thúc ca sáng: 14:00

# Ca tối (Night Shift)
SHIFT_NIGHT_START = time(14, 0, 0)    # Bắt đầu ca tối: 14:00
SHIFT_NIGHT_END = time(20, 0, 0)      # Kết thúc ca tối: 20:00

# Grace Period - Thời gian gia hạn sau khi kết thúc ca
# Nhân viên có thể checkout trong khoảng thời gian này mà không bị trừ điểm
GRACE_PERIOD_MINUTES = 30              # 30 phút sau khi kết thúc ca

# Thời gian cập nhật absence tracking (giây)
ABSENCE_THRESHOLD_SECONDS = 30         # Ngưỡng tính vắng mặt
INCREMENT_INTERVAL_SECONDS = 10        # Chu kỳ kiểm tra và cập nhật absence


