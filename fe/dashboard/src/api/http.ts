import { buildUrl } from './base';

function getToken() {
  return sessionStorage.getItem('authToken');
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = buildUrl(path);

  const headers: Record<string, string> = {
    'Accept': 'application/json, text/plain,*/*',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(options.headers as any)
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  // Debug: log outgoing request
  try {
    const shortBody = typeof options.body === 'string' && (options.body as string).length < 2000 ? options.body : undefined;
    console.debug('[apiFetch] Request', { method: options.method || 'GET', url, headers, bodyPreview: shortBody });
  } catch (_) {}

  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch (netErr: any) {
    throw new Error(`Network error: ${netErr.message || netErr}`);
  }

  const status = res.status;
  const ct = res.headers.get('content-type') || '';
  const isJson = ct.includes('application/json');

  if (status === 401) {
    sessionStorage.clear();
    throw new Error('Unauthorized (401)');
  }

  if (status === 204) return {} as T;

  // If not JSON, read text and throw a clearer error
  if (!isJson) {
    const text = await res.text();
    const snippet = text.slice(0, 200).replace(/\s+/g, ' ');
    throw new Error(`Unexpected non-JSON response (status ${status}) at ${path}: ${snippet}`);
  }

  let data: any;
  try {
    data = await res.json();
  } catch (parseErr: any) {
    throw new Error(`JSON parse error (status ${status}) at ${path}: ${parseErr.message}`);
  }

  if (!res.ok) {
    // If backend returned structured JSON (validation errors), include it verbatim for debugging
    const message = (data && (data.message || data.detail)) || data || `HTTP ${status}`;
    const text = typeof message === 'string' ? message : JSON.stringify(message);
    console.debug('[apiFetch] Response error', { status, url, body: data });
    throw new Error(text);
  }

  return data as T;
}
