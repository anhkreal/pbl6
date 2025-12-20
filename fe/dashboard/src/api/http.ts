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

  // Debug: log outgoing request, but redact Authorization
  try {
    const shortBody = typeof options.body === 'string' && (options.body as string).length < 2000 ? options.body : undefined;
    const safeHeaders = { ...(headers as any) };
    if (safeHeaders.Authorization) safeHeaders.Authorization = '<redacted>';
    console.debug('[apiFetch] Request', { method: options.method || 'GET', url, headers: safeHeaders, bodyPreview: shortBody });
  } catch (_) {}

  let res: Response;
  try {
    // Always include credentials so server cookies (session_token) are sent/received
    res = await fetch(url, { ...options, headers, credentials: 'include' });
  } catch (netErr: any) {
    console.error('[apiFetch] Network error', netErr);
    throw new Error('Không thể kết nối máy chủ. Vui lòng kiểm tra mạng và thử lại.');
  }

  const status = res.status;
  const ct = res.headers.get('content-type') || '';
  const isJson = ct.includes('application/json');

  if (status === 401) {
    // If we sent an Authorization header, retry ONCE without it to allow valid cookies to authenticate.
    const hadAuthHeader = !!headers.Authorization;
    if (hadAuthHeader) {
      try {
        const { Authorization, ...restHeaders } = headers as any;
        const retry = await fetch(url, { ...options, headers: restHeaders, credentials: 'include' });
        if (retry.ok) {
          // Our bearer token was stale, but cookie worked. Drop token to avoid future 401s.
          try { sessionStorage.removeItem('authToken'); } catch {}
          const ct2 = retry.headers.get('content-type') || '';
          if (retry.status === 204) return {} as T;
          if (ct2.includes('application/json')) {
            const data2 = await retry.json();
            return data2 as T;
          } else {
            const text2 = await retry.text();
            console.error('[apiFetch] Unexpected non-JSON after retry', { status: retry.status, path, preview: text2.slice(0,200) });
            throw new Error('Phản hồi không hợp lệ từ máy chủ. Vui lòng thử lại sau.');
          }
        }
      } catch (e) {
        // fallthrough to expire flow
      }
    }
    // Final: clear session and hard-redirect to login
    try { sessionStorage.clear(); } catch {}
    console.warn('[apiFetch] Unauthorized, session expired. Redirecting to login.');
    try {
      // Signal to app and trigger redirect
      window.dispatchEvent(new CustomEvent('auth:expired'));
      if (typeof window !== 'undefined' && window.location) {
        window.location.assign('/');
      }
    } catch {}
    throw new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
  }

  if (status === 204) return {} as T;

  // If not JSON, read text and throw a clearer error
  if (!isJson) {
    const text = await res.text();
    console.error('[apiFetch] Unexpected non-JSON response', { status, path, preview: text.slice(0,200) });
    throw new Error('Phản hồi không hợp lệ từ máy chủ. Vui lòng thử lại sau.');
  }

  let data: any;
  try {
    data = await res.json();
  } catch (parseErr: any) {
    console.error('[apiFetch] JSON parse error', { status, path, error: parseErr });
    throw new Error('Dữ liệu trả về không hợp lệ. Vui lòng thử lại.');
  }

  if (!res.ok) {
    // Log full details to console, but throw a friendly message to UI
    console.error('[apiFetch] Response error', { status, url, body: data });
    const userMessage = friendlyMessageForStatus(status, data);
    throw new Error(userMessage);
  }

  return data as T;
}

function friendlyMessageForStatus(status: number, body: any): string {
  try {
    const backendMsg = typeof body === 'string' ? body : (body?.message || body?.detail || '').toString();
    // Prefer specific backend validation errors if short and user-facing
    if (status === 422 && backendMsg && backendMsg.length < 160) return `Dữ liệu không hợp lệ: ${backendMsg}`;
  } catch {}
  switch (status) {
    case 400: return 'Yêu cầu không hợp lệ. Vui lòng kiểm tra dữ liệu nhập.';
    case 401: return 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.';
    case 403: return 'Bạn không có quyền thực hiện thao tác này.';
    case 404: return 'Không tìm thấy dữ liệu hoặc đường dẫn không đúng.';
    case 409: return 'Xung đột dữ liệu. Vui lòng thử lại hoặc làm mới trang.';
    case 429: return 'Quá nhiều yêu cầu. Vui lòng thử lại sau.';
    case 500: return 'Lỗi hệ thống. Vui lòng thử lại sau.';
    case 502: return 'Máy chủ đang bảo trì. Vui lòng thử lại sau.';
    case 503: return 'Dịch vụ tạm thời không sẵn sàng. Vui lòng thử lại.';
    case 504: return 'Hết thời gian chờ phản hồi. Vui lòng thử lại sau.';
    default: return 'Đã xảy ra lỗi. Vui lòng thử lại.';
  }
}
