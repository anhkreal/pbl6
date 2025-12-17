import { apiFetch } from './http';

/**
 * Verify PIN against backend `/system/pin-verify`.
 * Prefers server validation; falls back to legacy client-side compare if server unavailable.
 */
export async function verifyPin(pin?: string): Promise<boolean> {
  const username = sessionStorage.getItem('userName') || undefined;
  const userIdStr = sessionStorage.getItem('userId') || undefined;
  const user_id = userIdStr && /^\d+$/.test(userIdStr) ? Number(userIdStr) : undefined;
  const trimmed = (pin ?? '').toString().trim();

  // If caller didn't pass a pin but we have one stored (legacy), still attempt server verify with stored
  const candidatePin = trimmed || (sessionStorage.getItem('adminPin') || '').toString().trim();
  if (!candidatePin) return false;

  try {
    const body: any = { pin: candidatePin };
    if (user_id) body.user_id = user_id; else if (username) body.username = username;
    const res: any = await apiFetch('/system/pin-verify', {
      method: 'POST',
      body: JSON.stringify(body)
    });
    // Expecting { success: boolean }
    if (res && typeof res === 'object') {
      if (typeof res.success === 'boolean') return !!res.success;
      // some backends might return { valid: true }
      if (typeof (res as any).valid === 'boolean') return !!(res as any).valid;
    }
    return false;
  } catch (e) {
    // Fallback legacy compare if server call fails
    try {
      const localStored = (sessionStorage.getItem('adminPin') || '').toString().trim();
      return !!localStored && localStored === candidatePin;
    } catch {
      return false;
    }
  }
}
