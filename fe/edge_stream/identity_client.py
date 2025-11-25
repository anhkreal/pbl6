import requests, os
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:8000')

def query_identity(embedding):
    try:
        r = requests.post(f"{SERVER_URL}/query", json={'embedding': embedding}, timeout=1.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None
