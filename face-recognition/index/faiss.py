import numpy as np
import faiss
import os
import pandas as pd
import threading
import logging
import shutil
import tempfile
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FaissIndexManager:
    def query_embeddings_by_string(self, query, page=1, page_size=15, sort_by="image_id_asc"):
        """
        Thread-safe: Truy vấn embedding chỉ theo class_id (không phân biệt hoa thường), hỗ trợ phân trang và sắp xếp.
        - query: chuỗi class_id cần tìm
        - page: số trang (bắt đầu từ 1)
        - page_size: số ảnh mỗi trang
        - sort_by: sắp xếp theo (image_id_asc, image_id_desc, class_id_asc, class_id_desc, image_path_asc, image_path_desc)
        Trả về dict: { 'total': ..., 'total_pages': ..., 'page': ..., 'results': [...] }
        """
        with self._lock:
            query = str(query).strip().lower()
            results = []
            if not query:
                # Trả về tất cả embedding nếu query rỗng
                for idx, (img_id, img_path, cls_id) in enumerate(zip(self.image_ids, self.image_paths, self.class_ids)):
                    results.append({
                        'image_id': img_id,
                        'image_path': img_path,
                        'class_id': cls_id,
                        'faiss_index': idx
                    })
            else:
                for idx, (img_id, img_path, cls_id) in enumerate(zip(self.image_ids, self.image_paths, self.class_ids)):
                    if query == str(cls_id).strip().lower():
                        results.append({
                            'image_id': img_id,
                            'image_path': img_path,
                            'class_id': cls_id,
                            'faiss_index': idx
                        })
            
            # Sorting
            if sort_by == "image_id_desc":
                results.sort(key=lambda x: int(str(x['image_id']).split('_')[0]) if '_' in str(x['image_id']) else int(x['image_id']), reverse=True)
            elif sort_by == "class_id_asc":
                results.sort(key=lambda x: int(x['class_id']) if str(x['class_id']).isdigit() else 0)
            elif sort_by == "class_id_desc":
                results.sort(key=lambda x: int(x['class_id']) if str(x['class_id']).isdigit() else 0, reverse=True)
            elif sort_by == "image_path_asc":
                results.sort(key=lambda x: str(x['image_path']))
            elif sort_by == "image_path_desc":
                results.sort(key=lambda x: str(x['image_path']), reverse=True)
            else:  # default image_id_asc
                results.sort(key=lambda x: int(str(x['image_id']).split('_')[0]) if '_' in str(x['image_id']) else int(x['image_id']))
            
            total = len(results)
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
            page = max(1, min(page, total_pages))
            start = (page - 1) * page_size
            end = start + page_size
            paged_results = results[start:end]
            return {
                'total': total,
                'total_pages': total_pages,
                'page': page,
                'page_size': page_size,
                'results': paged_results
            }
    def reset_index(self):
        """
        Thread-safe: Xóa toàn bộ dữ liệu FAISS index và metadata
        """
        with self._lock:
            self.index = faiss.IndexFlatIP(self.embedding_size)
            self.image_ids = []
            self.image_paths = []
            self.class_ids = []
            self.embeddings = []
            # Làm trống file index và metadata, giữ cấu trúc file
            if self.index_path:
                faiss.write_index(self.index, self.index_path)
                self._last_index_mtime = os.path.getmtime(self.index_path)
            if self.meta_path:
                np.savez(self.meta_path,
                         image_ids=np.array([]),
                         image_paths=np.array([]),
                         class_ids=np.array([]),
                         embeddings=np.array([], dtype=np.float32))
                self._last_meta_mtime = os.path.getmtime(self.meta_path)
            # Index and metadata cleared, structure preserved
        
    def __init__(self, embedding_size, index_path=None, meta_path=None):
        self.embedding_size = embedding_size
        self.index = faiss.IndexFlatIP(embedding_size)
        self.image_ids = []
        self.image_paths = []
        self.class_ids = []
        self.embeddings = []
        self.index_path = index_path
        self.meta_path = meta_path
        
        # Thread-safety: RLock allows same thread to acquire multiple times
        self._lock = threading.RLock()
        
        # Track file modification times for intelligent reloading
        self._last_index_mtime = None
        self._last_meta_mtime = None

    def add_embeddings(self, embeddings, image_ids, image_paths, class_ids):
        """Thread-safe: Add embeddings to index."""
        with self._lock:
            embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            self.index.add(embeddings_norm.astype(np.float32))
            self.image_ids.extend(image_ids)
            self.image_paths.extend(image_paths)
            self.class_ids.extend(class_ids)
            if len(self.embeddings) == 0:
                self.embeddings = embeddings_norm.tolist()
            else:
                self.embeddings.extend(embeddings_norm.tolist())

    def save(self):
        """Thread-safe: Atomic save to prevent corruption."""
        with self._lock:
            try:
                # Create temporary files for atomic write
                temp_index = None
                temp_meta = None
                
                if self.index_path:
                    # Write to temp file first
                    temp_index = self.index_path + '.tmp'
                    faiss.write_index(self.index, temp_index)
                    
                    # Backup old file if exists
                    if os.path.exists(self.index_path):
                        backup_path = self.index_path + '.backup'
                        shutil.copy2(self.index_path, backup_path)
                    
                    # Atomic rename
                    shutil.move(temp_index, self.index_path)
                    
                    # Update mtime tracking
                    self._last_index_mtime = os.path.getmtime(self.index_path)
                
                if self.meta_path:
                    # Write to temp file first
                    temp_meta = self.meta_path + '.tmp'
                    np.savez(temp_meta,
                             image_ids=np.array(self.image_ids),
                             image_paths=np.array(self.image_paths),
                             class_ids=np.array(self.class_ids),
                             embeddings=np.array(self.embeddings, dtype=np.float32))
                    
                    # Backup old file if exists
                    if os.path.exists(self.meta_path):
                        backup_path = self.meta_path + '.backup'
                        shutil.copy2(self.meta_path, backup_path)
                    
                    # Atomic rename
                    shutil.move(temp_meta, self.meta_path)
                    
                    # Update mtime tracking
                    self._last_meta_mtime = os.path.getmtime(self.meta_path)
                
                logger.info(f"Successfully saved index with {len(self.image_ids)} embeddings")
                
            except Exception as e:
                # Cleanup temp files on error
                if temp_index and os.path.exists(temp_index):
                    try:
                        os.remove(temp_index)
                    except Exception:
                        pass
                if temp_meta and os.path.exists(temp_meta):
                    try:
                        os.remove(temp_meta)
                    except Exception:
                        pass
                logger.error(f"Failed to save index: {e}")
                raise

    def load(self):
        """
        Thread-safe: Load lại FAISS index và metadata từ file nếu file thực sự thay đổi.
        - Sử dụng timestamp (mtime) của file index và metadata để kiểm tra thay đổi.
        - Nếu file không thay đổi kể từ lần load trước, bỏ qua việc load lại để tối ưu hiệu năng.
        - Nếu file thay đổi, đọc lại index và metadata, đồng bộ các thuộc tính image_ids, image_paths, class_ids, embeddings.
        - Nếu embeddings trong metadata bị thiếu hoặc không khớp số lượng với image_ids, sẽ reconstruct lại embeddings từ FAISS index.
        """
        with self._lock:
            # 1. Lấy thời gian sửa đổi cuối cùng (mtime) của file index và metadata
            index_mtime = os.path.getmtime(self.index_path) if self.index_path and os.path.exists(self.index_path) else None
            meta_mtime = os.path.getmtime(self.meta_path) if self.meta_path and os.path.exists(self.meta_path) else None

            # 2. Nếu đã từng load và mtime không đổi, bỏ qua việc load lại
            if self._last_index_mtime == index_mtime and self._last_meta_mtime == meta_mtime:
                # Index and metadata unchanged, no need to reload
                return

            # 3. Đọc lại FAISS index từ file
            idx = faiss.read_index(self.index_path)
            self.index = idx

            # 4. Đọc lại metadata từ file (image_ids, image_paths, class_ids, embeddings)
            meta = np.load(self.meta_path, allow_pickle=True)
            self.image_ids = list(meta['image_ids']) if 'image_ids' in meta else []
            self.image_paths = list(meta['image_paths']) if 'image_paths' in meta else []
            self.class_ids = list(meta['class_ids']) if 'class_ids' in meta else []

            # 5. Kiểm tra embeddings: nếu tồn tại và đủ số lượng thì dùng luôn, ngược lại reconstruct lại từ index
            if 'embeddings' in meta and meta['embeddings'].shape[0] == len(self.image_ids):
                self.embeddings = meta['embeddings'].tolist()
            else:
                # Embeddings missing or mismatched, reconstruct from FAISS index
                self.embeddings = []
                for i in range(len(self.image_ids)):
                    self.embeddings.append(self.index.reconstruct(i).tolist())

            # 6. Lưu lại mtime để lần sau kiểm tra
            self._last_index_mtime = index_mtime
            self._last_meta_mtime = meta_mtime
            
            logger.info(f"Loaded index with {len(self.image_ids)} embeddings")
        
    def delete_by_image_id(self, image_id):
        """Thread-safe: Delete embedding by image_id."""
        with self._lock:
            image_id = str(image_id)
            if image_id not in [str(i) for i in self.image_ids]:
                return False
            idx = [str(i) for i in self.image_ids].index(str(image_id))
            del self.image_ids[idx]
            del self.image_paths[idx]
            del self.class_ids[idx]
            del self.embeddings[idx]
            self.index = faiss.IndexFlatIP(self.embedding_size)
            if len(self.embeddings) > 0:
                self.index.add(np.array(self.embeddings, dtype=np.float32))
            return True

    def delete_by_class_id(self, class_id):
        """
        Thread-safe: Xóa toàn bộ ảnh có class_id chỉ định và rebuild lại FAISS index
        """
        with self._lock:
            class_id = str(class_id)
            # Lấy các chỉ số cần xóa
            idxs_to_delete = [i for i, cls in enumerate(self.class_ids) if str(cls) == class_id]
            if not idxs_to_delete:
                return False
            # Xóa các phần tử metadata tại các vị trí index
            self.image_ids = [img_id for i, img_id in enumerate(self.image_ids) if i not in idxs_to_delete]
            self.image_paths = [img_path for i, img_path in enumerate(self.image_paths) if i not in idxs_to_delete]
            self.class_ids = [cls for i, cls in enumerate(self.class_ids) if i not in idxs_to_delete]
            self.embeddings = [emb for i, emb in enumerate(self.embeddings) if i not in idxs_to_delete]
            # Rebuild lại FAISS index từ embeddings còn lại
            self.index = faiss.IndexFlatIP(self.embedding_size)
            if len(self.embeddings) > 0:
                self.index.add(np.array(self.embeddings, dtype=np.float32))
            return True
        
    def query(self, query_emb, topk=5):
        """Thread-safe: Query similar embeddings (read operation)."""
        import time
        print(f'--- FAISS query ---')
        with self._lock:
            print(f'Số lượng vector trong index: {self.index.ntotal}')
            start = time.time()
            query_emb_norm = query_emb / np.linalg.norm(query_emb)
            D, I = self.index.search(query_emb_norm.reshape(1, -1).astype(np.float32), topk)
            print(f'Thời gian search FAISS: {time.time() - start:.3f}s')
            results = []
            for idx, dist in zip(I[0], D[0]):
                if idx >= 0 and idx < len(self.image_ids):
                    results.append({
                        'image_id': self.image_ids[idx],
                        'image_path': self.image_paths[idx],
                        'class_id': self.class_ids[idx],
                        'score': dist,
                        'faiss_index': idx
                    })
            print(f'Kết quả truy vấn: {results}')
            return results

    def print_example_vectors(self, n=5):
        """Thread-safe: Print example vectors."""
        with self._lock:
            print('Ví dụ một số vector trong FAISS index:')
            for i in range(min(n, len(self.image_paths))):
                vec = self.index.reconstruct(i)
                image_id = self.image_ids[i] if i < len(self.image_ids) else None
                image_path = self.image_paths[i]
                class_id = self.class_ids[i]
                norm = np.linalg.norm(vec)
                print(f'Vector {i}:')
                print(f'  image_id: {image_id}')
                print(f'  image_path: {image_path}')
                print(f'  class_id: {class_id}')
                # print(f'  norm: {norm:.4f}')
                print(f'  values[:10]: {vec[:10]} ...')
                
    def check_index_data(self):
        """Thread-safe: Check index data consistency."""
        with self._lock:
            result = {
                'num_vectors': self.index.ntotal,
                'num_image_ids': len(self.image_ids),
                'num_image_paths': len(self.image_paths),
                'num_class_ids': len(self.class_ids),
                'num_embeddings': len(self.embeddings),
                'num_unique_image_ids': len(set(self.image_ids)),
                'num_unique_image_paths': len(set(self.image_paths)),
                'num_unique_class_ids': len(set(self.class_ids)),
            }
            # Kiểm tra vector NaN và min/max
            if self.index.ntotal > 0:
                vecs = np.zeros((self.index.ntotal, self.embedding_size), dtype=np.float32)
                for i in range(self.index.ntotal):
                    vecs[i] = self.index.reconstruct(i)
                result['num_nan_vectors'] = int(np.isnan(vecs).any(axis=1).sum())
                result['min_vector_value'] = float(vecs.min())
                result['max_vector_value'] = float(vecs.max())
            else:
                result['num_nan_vectors'] = 0
                result['min_vector_value'] = None
                result['max_vector_value'] = None
            return result
            
    def get_image_ids_by_class(self, class_id):
        """
        Thread-safe: Trả về danh sách image_id có class trùng với class_id được truy vấn
        """
        with self._lock:
            class_id = str(class_id)
            result = [str(img_id) for img_id, cls in zip(self.image_ids, self.class_ids) if str(cls) == class_id]
            return result
## Module only: import and use FaissIndexManager from another file


