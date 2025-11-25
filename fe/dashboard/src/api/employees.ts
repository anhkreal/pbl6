import { apiFetch } from './http';

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

export async function createEmployee(data: { fullName: string; age: number; address: string; phone: string; shift: 'day' | 'night' }): Promise<Employee> {
  return apiFetch<Employee>('/employees', { method: 'POST', body: JSON.stringify(data) });
}

export async function shiftEmployee(id: number): Promise<void> {
  await apiFetch(`/employees/${id}/shift`, { method: 'POST' });
}

export async function resetEmployee(id: number): Promise<void> {
  await apiFetch(`/employees/${id}/reset`, { method: 'POST' });
}

export async function deleteEmployee(id: number): Promise<void> {
  await apiFetch(`/employees/${id}`, { method: 'DELETE' });
}
