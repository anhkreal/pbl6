import { apiFetch } from './http';

export interface AttendanceRow {
  id: number;
  userName: string;
  date: string;
  checkIn: string | null;
  checkOut: string | null;
  totalHours: number | null;
  shift: 'day' | 'night';
  status: 'late' | 'early' | 'working' | 'normal' | 'absent';
}
// NOTE: backend should supply one of above; UI maps working/normal -> on_time

export interface CheckLogQuery {
  date?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  user_id?: number;
  limit?: number;
  offset?: number;
}

export interface CheckLogResult {
  total: number;
  checklogs: AttendanceRow[];
}

export async function fetchCheckLogs(q: CheckLogQuery = {}): Promise<CheckLogResult> {
  const qp = new URLSearchParams();
  if (q.date) qp.append('date', q.date);
  if (q.date_from) qp.append('date_from', q.date_from);
  if (q.date_to) qp.append('date_to', q.date_to);
  if (q.status) qp.append('status', q.status);
  if (q.user_id !== undefined) qp.append('user_id', String(q.user_id));
  qp.append('limit', String(q.limit ?? 100));
  qp.append('offset', String(q.offset ?? 0));

  const res: any = await apiFetch<any>(`/checklog?${qp.toString()}`);
  const totalRaw = res?.total ?? 0;
  const totalNum = Number(totalRaw) || 0;
  const logs = Array.isArray(res?.checklogs) ? res.checklogs : [];
  // Map backend fields to AttendanceRow if necessary
  const mapped: AttendanceRow[] = logs.map((r: any) => ({
    id: r.id,
    userName: r.user_name || (r.user_id ? String(r.user_id) : ''),
    date: r.date,
    checkIn: r.check_in || null,
    checkOut: r.check_out || null,
    totalHours: r.total_hours ?? null,
    shift: r.shift || 'day',
    status: r.status || 'normal'
  }));
  return { total: totalNum, checklogs: mapped };
}

export async function patchAttendanceStatus(id: number): Promise<void> {
  await apiFetch(`/attendance/${id}`, { method: 'PATCH', body: JSON.stringify({ status: 'normal' }) });
}
