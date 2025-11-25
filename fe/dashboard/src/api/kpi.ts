import { apiFetch } from './http';

export interface KPIItem {
  id: number;
  userName: string;
  date: string;
  emotionScore: number;
  attendanceScore: number;
  totalScore: number;
  remark?: string;
}

export async function fetchKPI(
  mode: 'day' | 'month',
  date: string,
  staffIdOrName?: string | number,
  limit?: number,
  offset?: number
): Promise<KPIItem[]> {
  const qp = new URLSearchParams();
  // use date or month parameter name depending on mode
  if (mode === 'day') qp.append('date', date);
  else qp.append('month', date);

  // default limits: day -> 30, month -> 100
  qp.append('limit', String(limit ?? (mode === 'day' ? 30 : 100)));
  qp.append('offset', String(offset ?? 0));

  let url = '';
  if (staffIdOrName !== undefined && staffIdOrName !== null && String(staffIdOrName).trim() !== '') {
    // if numeric id provided, call /kpi/{id}
    const s = String(staffIdOrName);
    if (/^\d+$/.test(s)) {
      url = `/kpi/${s}?${qp.toString()}`;
    } else {
      // fallback: send staffName as a query param
      qp.append('staffName', s);
      url = `/kpi?${qp.toString()}`;
    }
  } else {
    url = `/kpi?${qp.toString()}`;
  }

  const res: any = await apiFetch<any>(url);

  let arr: any[] = [];
  if (Array.isArray(res)) arr = res;
  else if (Array.isArray(res?.data)) arr = res.data;
  else if (Array.isArray(res?.items)) arr = res.items;
  else if (Array.isArray(res?.results)) arr = res.results;
  else if (Array.isArray(res?.kpis)) arr = res.kpis;
  else if (res && typeof res === 'object') {
    const vals = Object.values(res).filter(v => v && typeof v === 'object');
    if (
      vals.length &&
      vals.every(v => v && typeof v === 'object' && (('date' in v) || ('user_name' in v) || ('userName' in v)))
    ) {
      arr = vals as any[];
    }
  }

  const mapped: KPIItem[] = arr.map((r: any, idx: number) => ({
    id: Number(r.id ?? r.kpi_id ?? idx),
    userName: r.user_name ?? r.userName ?? r.name ?? '',
    date: r.date ?? r.day ?? r.record_date ?? '',
    emotionScore: Number(r.emotion_score ?? r.emotionScore ?? 0),
    attendanceScore: Number(r.attendance_score ?? r.attendanceScore ?? 0),
    totalScore: Number(r.total_score ?? r.totalScore ?? 0),
    remark: r.remark ?? r.note ?? r.comment
  }));

  return mapped;
}
