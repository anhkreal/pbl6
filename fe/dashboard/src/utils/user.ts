import { apiFetch } from '../api/http';

/**
 * Resolve current user's id from session or backend.
 * 1) Check common sessionStorage keys
 * 2) Fallback to /auth/me
 * 3) Fallback to /taikhoan/{username} if username is available
 * Returns number or null.
 */
export async function resolveUserId(): Promise<number | null> {
  const possibleKeys = ['userId', 'user_id', 'id', 'uid'];
  for (const k of possibleKeys) {
    const v = sessionStorage.getItem(k);
    if (v) {
      const n = Number(v);
      if (!Number.isNaN(n) && n > 0) return n;
      try {
        const parsed = JSON.parse(v);
        const cand = Number((parsed as any)?.id ?? (parsed as any)?.user_id);
        if (!Number.isNaN(cand) && cand > 0) return cand;
      } catch {}
    }
  }
  try {
    const me: any = await apiFetch('/auth/me');
    const c = Number(me?.id ?? me?.user_id ?? me?.user?.id);
    if (!Number.isNaN(c) && c > 0) return c;
  } catch {}
  try {
    const username = sessionStorage.getItem('userName');
    if (username) {
      const info: any = await apiFetch(`/taikhoan/${encodeURIComponent(username)}`);
      const uid = Number(info?.user?.id ?? info?.id);
      if (!Number.isNaN(uid) && uid > 0) {
        sessionStorage.setItem('userId', String(uid));
        return uid;
      }
    }
  } catch {}
  return null;
}
