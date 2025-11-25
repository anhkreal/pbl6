import { apiFetch } from './http';
import { buildUrl } from './base';

export interface EmotionLog {
  id: number;
  userName: string;
  timestamp: string;
  emotion: string;
  frameImage?: string; // may be base64 or URL depending on include_image_base64
  userId?: number;
}

// New query parameters accepted by backend
export interface EmotionQueryParams {
  user_id?: number; // integer query
  emotion_type?: string;
  start_ts?: string; // ISO string
  end_ts?: string; // ISO string
  limit?: number; // default 30
  offset?: number; // default 0
  include_image_base64?: boolean; // default false

  // backward compatibility for existing callers
  from?: string;
  to?: string;
  staffName?: string;
  negativeOnly?: boolean;
}

export interface EmotionFetchResult {
  total: number;
  logs: EmotionLog[];
}

export async function fetchEmotionLogs(params: EmotionQueryParams = {}): Promise<EmotionFetchResult> {
  const qp = new URLSearchParams();
  // If caller didn't provide a time range, default to last 30 days to avoid heavy full-table queries
  const now = new Date();
  const defaultEnd = now.toISOString();
  const defaultStart = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
  const start_ts = params.start_ts ?? params.from ?? defaultStart;
  const end_ts = params.end_ts ?? params.to ?? defaultEnd;
  // map new names
  if (params.user_id !== undefined) qp.append('user_id', String(params.user_id));
  if (params.emotion_type) qp.append('emotion_type', params.emotion_type);
  if (start_ts) qp.append('start_ts', start_ts);
  if (end_ts) qp.append('end_ts', end_ts);
  qp.append('limit', String(params.limit ?? 30));
  qp.append('offset', String(params.offset ?? 0));
  if (params.include_image_base64) qp.append('include_image_base64', params.include_image_base64 ? '1' : '0');

  // backward compatibility: map old fields
  if (params.from && !params.start_ts) qp.append('start_ts', params.from);
  if (params.to && !params.end_ts) qp.append('end_ts', params.to);
  if (params.staffName) qp.append('user_id', params.staffName);
  if (params.negativeOnly) qp.append('emotion_type', 'negative');

  // Use the singular /emotion endpoint as specified
  // Retry a few times for transient backend errors (e.g., DB packet sequence issues)
  const maxAttempts = 3;
  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
  let lastErr: any = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res: any = await apiFetch<any>(`/emotion?${qp.toString()}`);
      // Debug: log successful response for visibility
      console.debug('[fetchEmotionLogs] success', { url: `/emotion?${qp.toString()}`, res });
      // Expected backend shape: { success: true, total: number, logs: [...] }
      // Coerce total to a number if present; otherwise use mapped.length as fallback
      // (some backends may return total as a string)
      let totalRaw: any = res?.total ?? res?.count;
      let rawLogs: any[] = [];
      if (Array.isArray(res?.logs)) rawLogs = res.logs;
      else if (Array.isArray(res)) rawLogs = res;
      else if (Array.isArray(res.data)) rawLogs = res.data;
      else if (Array.isArray(res.results)) rawLogs = res.results;
      else if (Array.isArray(res.items)) rawLogs = res.items;
      else if (res && res.id && res.captured_at) rawLogs = [res];

      // Map backend log fields to EmotionLog
      const mapped: EmotionLog[] = (rawLogs || []).map((r: any) => ({
        id: r.id,
        userId: r.user_id,
        userName: r.user_name || (r.user_id ? String(r.user_id) : r.user || ''),
        timestamp: r.captured_at || r.timestamp || r.created_at || '',
        emotion: r.emotion_type || r.emotion || '',
        frameImage: r.image_base64 || r.frame_image || r.image || r.frameImage || null,
        // include note if present
        ...(r.note ? { note: r.note } : {})
      }));

      const totalNum = totalRaw != null ? Number(totalRaw) : mapped.length;
      return { total: Number.isFinite(totalNum) ? totalNum : mapped.length, logs: mapped };
    } catch (err: any) {
      lastErr = err;
      // Debug: try a raw fetch to capture response body/status for server 500s
      try {
        const url = buildUrl(`/emotion?${qp.toString()}`);
        const token = sessionStorage.getItem('authToken');
        const headers: Record<string,string> = { 'Accept': 'application/json' };
        if (token) headers.Authorization = `Bearer ${token}`;
        const dbgRes = await fetch(url, { method: 'GET', headers });
        let dbgText: string;
        try { dbgText = await dbgRes.text(); } catch(e2) { dbgText = String(e2); }
        console.error('[fetchEmotionLogs] debug fetch', { url, status: dbgRes.status, body: dbgText });
      } catch (dbgErr) {
        console.error('[fetchEmotionLogs] debug fetch failed', dbgErr);
      }
      const msg = (err && err.message) ? String(err.message).toLowerCase() : '';
      // If error mentions packet sequence (MySQL) or is a connection/timeout, retry
      if (attempt < maxAttempts && (msg.includes('packet sequence') || msg.includes('packet sequence number') || msg.includes('connection') || msg.includes('timeout') || msg.includes('5') )) {
        await sleep(200 * attempt);
        continue;
      }
      throw err;
    }
  }
  throw new Error(`Lỗi khi truy vấn emotion logs: ${lastErr?.message || String(lastErr)}`);
}

// Convenience wrapper for staff: fetch logs for a single user id with sensible defaults
export async function fetchEmotionLogsForUser(userId: number, opts: Omit<EmotionQueryParams, 'user_id'> = {}): Promise<EmotionFetchResult> {
  // debug: log raw inputs to help trace Invalid userId issues
  console.debug('[fetchEmotionLogsForUser] raw userId:', userId, 'opts:', opts);
  const uid = Number(userId);
  // construct a query preview for debugging using the same keys fetchEmotionLogs expects
  try {
    const qp = new URLSearchParams();
    if (opts.start_ts) qp.append('start_ts', opts.start_ts);
    if (opts.end_ts) qp.append('end_ts', opts.end_ts);
    qp.append('limit', String(opts.limit ?? 30));
    qp.append('offset', String(opts.offset ?? 0));
    if (opts.include_image_base64) qp.append('include_image_base64', opts.include_image_base64 ? '1' : '0');
    qp.append('user_id', String(uid));
    console.debug('[fetchEmotionLogsForUser] constructed url preview: /emotion?' + qp.toString());
  } catch (e) {
    console.debug('[fetchEmotionLogsForUser] preview qp build failed', e);
  }

  if (!uid || Number.isNaN(uid)) {
    console.error('[fetchEmotionLogsForUser] Invalid userId after Number():', uid);
    throw new Error('Invalid userId');
  }

  return fetchEmotionLogs({ ...opts, user_id: uid });
}

export async function deleteEmotionLog(id: number, pin: string): Promise<void> {
  // legacy helper: delete via /emotions/{id}
  await apiFetch(`/emotions/${id}`, { method: 'DELETE' });
}

export async function deleteEmotionLogsByUser(userId: number, pin: string): Promise<void> {
  // assume backend supports deleting by user id with PIN verification
  return apiFetch(`/emotions/user/${userId}`, { method: 'DELETE', body: JSON.stringify({ pin }) });
}

// New API: delete a single emotion log using /delete-emotion/{id}
export async function deleteEmotionById(id: number, pin?: string): Promise<{ success: boolean; message?: string }> {
  // Backend expects DELETE for /delete-emotion/{id}.
  // Send PIN as a query parameter to avoid potential issues with request bodies on DELETE.
  let url = `/delete-emotion/${id}`;
  if (pin) url += `?pin=${encodeURIComponent(String(pin).trim())}`;
  const res: any = await apiFetch(url, { method: 'DELETE' });
  return { success: !!res?.success, message: res?.message };
}
