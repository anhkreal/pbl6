import time, requests, os
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:8000')

class EmotionLogBatcher:
    def __init__(self, post_interval=5.0, max_batch=50):
        self.post_interval = post_interval
        self.max_batch = max_batch
        self.buffer = []
        self._last_post = time.time()

    def enqueue(self, meta):
        self.buffer.append({
            'staffId': meta.get('staffId'),
            'timestamp': meta.get('timestamp'),
            'emotion': meta.get('emotion'),
            'frameImage': meta.get('frameImage')
        })
        now = time.time()
        if len(self.buffer) >= self.max_batch or (now - self._last_post) >= self.post_interval:
            self.flush()

    def flush(self):
        if not self.buffer:
            return 0
        payload = {'logs': self.buffer}
        try:
            r = requests.post(f"{SERVER_URL}/emotions", json=payload, timeout=2.0)
            if r.status_code == 200:
                sent = len(self.buffer)
                self.buffer = []
                self._last_post = time.time()
                return sent
        except Exception:
            return 0
        return 0
