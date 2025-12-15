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


