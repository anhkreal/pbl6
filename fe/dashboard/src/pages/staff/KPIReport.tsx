import React, { useEffect, useState } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import { fetchKPI, KPIItem } from '../../api/kpi';
import { apiFetch } from '../../api/http';

export default function StaffKPIReport() {
  const [mode, setMode] = useState<'day' | 'month'>('day');
  const [day, setDay] = useState('2025-01-28');
  const [month, setMonth] = useState('2025-01');
  const [items, setItems] = useState<KPIItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        // Resolve user id for staff KPI
        const possibleKeys = ['userId', 'user_id', 'id', 'uid'];
        let uid: number | null = null;
        for (const k of possibleKeys) {
          const v = sessionStorage.getItem(k);
          if (v) {
            const n = Number(v);
            if (!Number.isNaN(n) && n > 0) { uid = n; break; }
            try { const parsed = JSON.parse(v); if (parsed && (parsed.id || parsed.user_id)) { const c = Number(parsed.id ?? parsed.user_id); if (!Number.isNaN(c) && c > 0) { uid = c; break; } } } catch(_){}
          }
        }
        if (!uid) {
          try { const me:any = await apiFetch('/auth/me'); const c = me?.id ?? me?.user_id ?? me?.user?.id ?? null; if (c && !Number.isNaN(Number(c))) uid = Number(c); } catch(e){ console.debug('[StaffKPI] /auth/me failed', e); }
        }
        if (!uid) {
          try { const username = sessionStorage.getItem('userName'); if (username) { const info:any = await apiFetch(`/taikhoan/${encodeURIComponent(username)}`); const uid2 = info?.user?.id ?? info?.id ?? null; if (uid2 && !Number.isNaN(Number(uid2))) { uid = Number(uid2); sessionStorage.setItem('userId', String(uid)); } } } catch(e){ console.debug('[StaffKPI] /taikhoan failed', e); }
        }

        const data = await fetchKPI(mode, mode === 'day' ? day : month, uid ?? undefined, mode === 'day' ? 30 : 100, 0);
        if (!ignore) setItems(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; }
  }, [mode, day, month]);

  const data = items;

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 18 }}>KPI Report (Ngày / Tháng)</h1>
      <div style={{ background: '#fff', padding: 16, borderRadius: 8, marginBottom: 16, display: 'flex', gap: 12 }}>
        <select value={mode} onChange={e => setMode(e.target.value as any)} style={inp}>
          <option value="day">Theo ngày</option>
          <option value="month">Theo tháng</option>
        </select>
        {mode === 'day' && <input type="date" value={day} onChange={e => setDay(e.target.value)} style={inp} />}
        {mode === 'month' && <input type="month" value={month} onChange={e => setMonth(e.target.value)} style={inp} />}
      </div>
      <div style={{ background: '#fff', borderRadius: 8 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead><tr style={headRow}>{['STT', 'Ngày', 'Chuyên cần', 'Cảm xúc', 'Tổng'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
          <tbody>
            {loading && <tr><td style={{ padding: 10 }} colSpan={5}>Đang tải...</td></tr>}
            {error && <tr><td style={{ padding: 10, color: 'red' }} colSpan={5}>{error}</td></tr>}
            {data.map((r, i) => (
              <tr key={r.date} style={row}>
                <td style={td}>{i + 1}</td>
                <td style={td}>{r.date}</td>
                <td style={td}>{(r.attendanceScore * 100).toFixed(1)}%</td>
                <td style={td}>{(r.emotionScore * 100).toFixed(1)}%</td>
                <td style={{ ...td, fontWeight: 600 }}>{(r.totalScore * 100).toFixed(1)}%</td>
              </tr>
            ))}
            {!data.length && !loading && <tr><td style={{ padding: 16 }} colSpan={5}>Không có dữ liệu</td></tr>}
          </tbody>
        </table>
      </div>
    </StaffLayout>
  );
}

const inp: React.CSSProperties = { padding: 8, border: '1px solid #ccc', borderRadius: 4 };
const headRow: React.CSSProperties = { background: '#f5f5f5' };
const th: React.CSSProperties = { padding: 10, fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d', letterSpacing: '.5px', textAlign: 'left' };
const row: React.CSSProperties = { borderTop: '1px solid #ecf0f1' };
const td: React.CSSProperties = { padding: 10, fontSize: 14 };