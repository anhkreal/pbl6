declare global {
  interface Window { __API_BASE__?: string; }
}

// Default to this local IP:port when no env var or window override is provided.
// Keep existing behavior of preferring VITE_API_URL then window.__API_BASE__.
// let RAW_BASE = (import.meta as any).env?.VITE_API_URL || (window as any).__API_BASE__ || 'http://192.168.1.2:8000';
let RAW_BASE =  'http://127.0.0.1:8000';
let API_BASE = RAW_BASE.trim().replace(/\/+$/, '');
if (!API_BASE) {
  console.warn('[api] VITE_API_URL not set. Using relative requests. Create .env.local with: VITE_API_URL=http://localhost:8000');
}

export function getApiBase(): string {
  return API_BASE;
}

export function setApiBase(url: string) {
  API_BASE = (url || '').trim().replace(/\/+$/, '');
}

export function buildUrl(path: string): string {
  const baseOk = !!API_BASE;
  return baseOk ? (path.startsWith('http') ? path : API_BASE + path) : path;
}
