import { apiFetch } from './http';
import { buildUrl } from './base';

interface LoginResponse { success: boolean; message: string; username: string; token: string; role: 'admin' | 'user' | 'staff' | string; }

export async function login(username: string, password: string): Promise<LoginResponse> {
  // Try form-encoded first (many backends expect form data)
  try {
    const data = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username, password }).toString(),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    sessionStorage.setItem('authToken', data.token);
    sessionStorage.setItem('userRole', data.role);
    sessionStorage.setItem('userName', data.username);
    // Try to fetch current user info to obtain user id for staff flows
    try {
      const me: any = await apiFetch('/auth/me');
      const uid = me?.id ?? me?.user_id ?? me?.user?.id ?? null;
      if (uid) sessionStorage.setItem('userId', String(uid));
        // If this account is admin try to capture admin PIN
        try {
          if (data.role === 'admin') {
            const adminPin = me?.pin ?? me?.user?.pin ?? null;
            if (adminPin) {
              const trimmed = String(adminPin).trim();
              sessionStorage.setItem('adminPin', trimmed);
              console.debug('[login] stored adminPin from /auth/me:', trimmed);
            }
          }
        } catch (e) { /* ignore pin extraction errors */ }
    } catch (e) {
      console.debug('[login] /auth/me fetch failed', e);
    }
    // Always attempt to fetch /taikhoan/{username} to ensure we obtain user.id and pin
    try {
      const uname = data.username;
      if (uname) {
        const info: any = await apiFetch(`/taikhoan/${encodeURIComponent(uname)}`);
        console.debug('[login] /taikhoan after login payload:', info);
        const uid2 = info?.user?.id ?? info?.id ?? null;
        if (uid2) sessionStorage.setItem('userId', String(uid2));
        try {
          if (data.role === 'admin') {
            const adminPin2 = info?.user?.pin ?? info?.pin ?? null;
            if (adminPin2) {
              const trimmed = String(adminPin2).trim();
              sessionStorage.setItem('adminPin', trimmed);
              console.debug('[login] stored adminPin from /taikhoan after login:', trimmed);
            }
          }
        } catch (e) { /* ignore */ }
      }
    } catch (e) {
      console.debug('[login] post-login /taikhoan fetch failed', e);
    }
    return data;
  } catch (err) {
    // Fallback: try JSON body if form-encoded fails
    try {
      const data = await apiFetch<LoginResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
      sessionStorage.setItem('authToken', data.token);
      sessionStorage.setItem('userRole', data.role);
      sessionStorage.setItem('userName', data.username);
      // Try to fetch current user info to obtain user id for staff flows
      try {
        const me: any = await apiFetch('/auth/me');
        console.debug('[login] /auth/me payload:', me);
        const uid = me?.id ?? me?.user_id ?? me?.user?.id ?? null;
        console.debug('[login] resolved uid from /auth/me:', uid);
        if (uid) sessionStorage.setItem('userId', String(uid));
        // capture admin PIN if available in /auth/me response
        try {
          if (data.role === 'admin') {
            const adminPin = me?.pin ?? me?.user?.pin ?? null;
            if (adminPin) sessionStorage.setItem('adminPin', String(adminPin));
          }
        } catch (e) { /* ignore */ }
      } catch (e) {
        console.debug('[login] /auth/me fetch failed', e);
      }
      // Always attempt to fetch /taikhoan/{username} to ensure we obtain user.id and pin
      try {
        const uname = data.username;
        if (uname) {
          const info: any = await apiFetch(`/taikhoan/${encodeURIComponent(uname)}`);
          console.debug('[login] /taikhoan after login payload (fallback branch):', info);
          const uid2 = info?.user?.id ?? info?.id ?? null;
          if (uid2) sessionStorage.setItem('userId', String(uid2));
          try {
            if (data.role === 'admin') {
              const adminPin2 = info?.user?.pin ?? info?.pin ?? null;
              if (adminPin2) {
                const trimmed = String(adminPin2).trim();
                sessionStorage.setItem('adminPin', trimmed);
                console.debug('[login] stored adminPin from /taikhoan after login (fallback branch):', trimmed);
              }
            }
          } catch (e) { /* ignore */ }
        }
      } catch (e) {
        console.debug('[login] post-login /taikhoan fetch failed (fallback branch)', e);
      }
      // Fallback: if /auth/me didn't provide an id, but username is numeric, use it as userId
      if (!sessionStorage.getItem('userId')) {
        const maybe = Number(data.username);
        if (!Number.isNaN(maybe) && maybe > 0) {
          sessionStorage.setItem('userId', String(maybe));
          console.debug('[login] fallback: set userId from username:', maybe);
        }
      }
      return data;
    } catch (err2) {
      // Rethrow original error or the fallback error for visibility
      throw err2 || err;
    }
  }
}

export function logout() {
  sessionStorage.clear();
}
