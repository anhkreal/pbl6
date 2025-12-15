# ===== SHARED INSTANCES SINGLETON =====
# File: face_api/service/shared_instances.py
# Mục đích: Tạo các instance duy nhất để tránh duplicate và memory leak

import threading
from model.arcface_model import ArcFaceFeatureExtractor
from index.faiss import FaissIndexManager
from config import *

class SharedInstances:
    """Singleton pattern để quản lý các instance dùng chung"""
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
        if not self._initialized:
            print("🔄 Initializing shared instances...")
            
            # Feature Extractor - chỉ tạo 1 lần
            self.extractor = ArcFaceFeatureExtractor(
                model_path=MODEL_PATH, 
                model_version=MODEL_VERSION,
                device=None
            )
            
            # FAISS Manager - chỉ tạo 1 lần
            self.faiss_manager = FaissIndexManager(
                embedding_size=512,
                index_path=FAISS_INDEX_PATH,
                meta_path=FAISS_META_PATH
            )
            
            # Load initial data
            self.faiss_manager.load()
            
            # Thread lock cho FAISS operations
            self.faiss_lock = threading.Lock()
            
            self._initialized = True
            print("✅ Shared instances initialized successfully!")
    
    def get_extractor(self):
        """Lấy feature extractor (thread-safe)"""
        return self.extractor
    
    def get_faiss_manager(self):
        """Lấy FAISS manager (thread-safe)"""
        return self.faiss_manager
    
    def get_faiss_lock(self):
        """Lấy lock cho FAISS operations"""
        return self.faiss_lock
    
    def reload_faiss_if_needed(self):
        """Reload FAISS chỉ khi cần thiết"""
        with self.faiss_lock:
            # Chỉ reload nếu có thay đổi
            if hasattr(self.faiss_manager, '_needs_reload') and self.faiss_manager._needs_reload:
                print("🔄 Reloading FAISS index...")
                self.faiss_manager.load()
                self.faiss_manager._needs_reload = False

# Global instance
shared = SharedInstances()

# Convenience functions
def get_extractor():
    return shared.get_extractor()

def get_faiss_manager():
    return shared.get_faiss_manager()

def get_faiss_lock():
    return shared.get_faiss_lock()

def reload_faiss_if_needed():
    return shared.reload_faiss_if_needed()
