import { apiFetch } from './http';

export interface UserProfile {
  id?: number;
  username?: string;
  full_name?: string;
  age?: number;
  address?: string;
  phone?: string;
}

export async function updateProfile(payload: Partial<UserProfile>) {
  // If backend expects PUT to /edit-users/{id}, prefer that when id provided.
  const id = (payload.id || (payload as any).user_id) as number | undefined;
  if (id) {
    // Remove id/user_id from payload body per backend expectation (id is in path)
    const bodyPayload: any = { ...payload } as any;
    delete bodyPayload.id;
    delete bodyPayload.user_id;
    return apiFetch(`/edit-users/${id}`, { method: 'PUT', body: JSON.stringify(bodyPayload) as any });
  }
  // Fallback to PATCH /users
  try {
    return await apiFetch('/users', { method: 'PATCH', body: JSON.stringify(payload) });
  } catch (err) {
    throw err;
  }
}

export async function changePassword(oldPassword: string, newPassword: string) {
  // Try form-encoded first (many backends expect this), then fallback to JSON
  try {
    const form = new URLSearchParams();
    form.append('current_password', oldPassword);
    form.append('new_password', newPassword);
    return await apiFetch('/change-password', {
      method: 'POST',
      body: form.toString(),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  } catch (err) {
    return apiFetch('/change-password', { method: 'POST', body: JSON.stringify({ current_password: oldPassword, new_password: newPassword }) });
  }
}

export async function changePin(oldPin: string, newPin: string) {
  // Try form-encoded body first (backend expects application/x-www-form-urlencoded)
  try {
    const form = new URLSearchParams();
    form.append('old_pin', oldPin);
    form.append('new_pin', newPin);
    return await apiFetch('/change-pin', {
      method: 'POST',
      body: form.toString(),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  } catch (err) {
    // fallback to JSON body
    return apiFetch('/change-pin', { method: 'POST', body: JSON.stringify({ old_pin: oldPin, new_pin: newPin }) });
  }
}
