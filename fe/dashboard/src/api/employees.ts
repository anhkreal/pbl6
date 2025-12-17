// Đổi ca theo username
export async function shiftEmployeeByUsername(username: string, currentShift: 'day' | 'night'): Promise<any> {
  const newShift = currentShift === 'day' ? 'night' : 'day';
  const body = new URLSearchParams({ new_shift: newShift }).toString();
  return apiFetch(`/edit-users/by-username/${encodeURIComponent(username)}/shift`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body
  });
}

// Cho nghỉ việc theo username
export async function resignEmployeeByUsername(username: string): Promise<any> {
  // Nếu BE yêu cầu status=off, truyền vào body
  const body = new URLSearchParams({ status: 'off' }).toString();
  return apiFetch(`/edit-users/by-username/${encodeURIComponent(username)}/resign`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body
  });
}
import { apiFetch } from './http';

// Thêm mới nhân viên và tài khoản qua API /add-user-account (form-data)
export async function addUserAndAccount(data: { username: string; full_name?: string; age?: string | number; address?: string; phone?: string; shift?: 'day' | 'night' }): Promise<any> {
  const params = new URLSearchParams();
  params.append('username', data.username);
  params.append('full_name', data.full_name ?? '');
  params.append('age', data.age !== undefined && data.age !== null && data.age !== '' ? String(data.age) : '');
  params.append('address', data.address ?? '');
  params.append('phone', data.phone ?? '');
  params.append('shift', data.shift || 'day');
  // Debug: log all params
  for (const [k, v] of params.entries()) {
    console.debug('[addUserAndAccount] param', k, v);
  }
  return apiFetch('/add-user-account', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
}

export interface Employee {
  id: number;
  username?: string;
  fullName: string;
  age?: number;
  address?: string;
  phone?: string;
  gender?: string;
  role?: string;
  shift: 'day' | 'night';
  status: 'working' | 'resigned' | 'absent' | 'off';
  avatar_base64?: string | null;
}

export interface EmployeeListResult {
  total: number;
  users: Employee[];
}

export async function fetchEmployees(query?: string | number): Promise<Employee[]> {
  // If query is numeric, call /users/{id}?include_avatar_base64=true
  const s = query === undefined || query === null ? '' : String(query).trim();
  if (s && /^\d+$/.test(s)) {
    const res: any = await apiFetch<any>(`/users/${s}?include_avatar_base64=true`);
    const u = res?.user ?? res;
    if (!u) return [];
    return [{
      id: Number(u.id),
      username: u.username,
      fullName: u.full_name ?? u.fullName ?? u.name ?? '',
      age: u.age,
      address: u.address,
      phone: u.phone,
      gender: u.gender,
      role: u.role,
      shift: u.shift ?? 'day',
      status: u.status ?? 'working',
      avatar_base64: u.avatar_base64 ?? null
    }];
  }

  // Otherwise fetch full list from /users (no pagination) and filter client-side if query provided
  const res: any = await apiFetch<any>('/users');
  const arr = Array.isArray(res?.users) ? res.users : (Array.isArray(res) ? res : []);
  const mapped = arr.map((u: any) => ({
    id: Number(u.id),
    username: u.username,
    fullName: u.full_name ?? u.fullName ?? u.name ?? '',
    age: u.age,
    address: u.address,
    phone: u.phone,
    gender: u.gender,
    role: u.role,
    shift: u.shift ?? 'day',
    status: u.status ?? 'working',
    avatar_base64: u.avatar_base64 ?? null
  }));

  if (!s) return mapped;
  const qLower = s.toLowerCase();
  return mapped.filter((u: Employee) => (u.fullName || '').toLowerCase().includes(qLower) || (u.username || '').toLowerCase().includes(qLower));
}

export async function createEmployee(data: { fullName: string; username: string; password: string; age: number; address: string; phone: string; shift: 'day' | 'night' }): Promise<Employee> {
  // Deprecated: backend has no /employees endpoint. Use /add-user-account (form) instead via addUserAndAccount().
  throw new Error('Deprecated API: use addUserAndAccount()');
}

export async function shiftEmployee(id: number): Promise<void> {
  // Deprecated: use shiftEmployeeByUsername().
  throw new Error('Deprecated API: use shiftEmployeeByUsername()');
}

export async function resetEmployee(id: number): Promise<void> {
  // Deprecated: backend endpoint does not exist.
  throw new Error('Deprecated API: endpoint not available');
}

export async function deleteEmployee(id: number): Promise<void> {
  // Deprecated: use resignEmployeeByUsername().
  throw new Error('Deprecated API: use resignEmployeeByUsername()');
}
