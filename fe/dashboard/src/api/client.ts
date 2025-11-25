import { buildUrl } from './base';

async function request(path: string, options: RequestInit = {}) {
  const token = sessionStorage.getItem('authToken') || sessionStorage.getItem('token');
  const baseHeaders: Record<string,string> = { 'Content-Type': 'application/json' };
  const optHeaders = options.headers && typeof options.headers === 'object' ? options.headers as Record<string,string> : {};
  const headers: Record<string,string> = { ...baseHeaders, ...optHeaders };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const url = buildUrl(path);
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) { sessionStorage.clear(); window.location.reload(); }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  try { return await res.json(); } catch { return {}; }
}

export function post(path: string, body: any){
  return request(path, { method: 'POST', body: JSON.stringify(body) });
}
export function get(path: string){
  return request(path);
}
export function patch(path: string, body: any){
  return request(path, { method: 'PATCH', body: JSON.stringify(body) });
}
export function del(path: string){
  return request(path, { method: 'DELETE' });
}
