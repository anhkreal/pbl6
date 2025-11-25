import React, { useEffect, useState } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import { fetchCheckLogs, AttendanceRow } from '../../api/attendance';
import { apiFetch } from '../../api/http';

export default function StaffAttendance() {
  const [day, setDay] = useState('2025-01-28');
  const [rows, setRows] = useState<AttendanceRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState<number | null>(null);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        // Resolve user id for staff view
        const possibleKeys = ['userId', 'user_id', 'id', 'uid'];
        let uid: number | null = null;
        for (const k of possibleKeys) {
          const v = sessionStorage.getItem(k);
          if (v) {
            const n = Number(v);
            if (!Number.isNaN(n) && n > 0) { uid = n; break; }
            try {
              const parsed = JSON.parse(v);
              if (parsed && (parsed.id || parsed.user_id)) {
                const candidate = Number(parsed.id ?? parsed.user_id);
                if (!Number.isNaN(candidate) && candidate > 0) { uid = candidate; break; }
              }
            } catch (_) { }
          }
        }
        // try /auth/me then /taikhoan if not found
        if (!uid) {
          try {
            const me:any = await apiFetch('/auth/me');
            const candidate = me?.id ?? me?.user_id ?? me?.user?.id ?? null;
            if (candidate && !Number.isNaN(Number(candidate))) uid = Number(candidate);
          } catch (e) { console.debug('[StaffAttendance] /auth/me failed', e); }
        }
        if (!uid) {
          try {
            const username = sessionStorage.getItem('userName');
            if (username) {
              const info:any = await apiFetch(`/taikhoan/${encodeURIComponent(username)}`);
              const uid2 = info?.user?.id ?? info?.id ?? null;
              if (uid2 && !Number.isNaN(Number(uid2))) { uid = Number(uid2); sessionStorage.setItem('userId', String(uid)); }
            }
          } catch (e) { console.debug('[StaffAttendance] /taikhoan failed', e); }
        }

        const data = await fetchCheckLogs({ date_from: day, date_to: day, limit, offset, user_id: uid ?? undefined });
        if (!ignore) {
          setRows(data.checklogs);
          setTotal(data.total);
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; }
  }, [day, limit, offset]);

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 18 }}>Chấm công (Xem theo ngày)</h1>
      <div style={{ background: '#fff', padding: 16, borderRadius: 8, marginBottom: 16 }}>
        <input type="date" value={day} onChange={e => setDay(e.target.value)} style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }} />
      </div>
      <div style={{ background: '#fff', borderRadius: 8 }}>
        {loading && <div style={{ padding: 10 }}>Đang tải...</div>}
        {error && <div style={{ padding: 10, color: 'red' }}>{error}</div>}
        {!loading && !error && (
          <>
          <div style={{ padding: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>Tổng: <strong>{total ?? 0}</strong></div>
            <div>
              <button disabled={offset <= 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Prev</button>
              <button style={{ marginLeft: 8 }} disabled={offset + limit >= (total ?? 0)} onClick={() => setOffset(offset + limit)}>Next</button>
            </div>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={headRow}>{['STT', 'Ngày', 'Check in', 'Check out', 'Giờ làm', 'Trạng thái'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.id} style={row}>
                  <td style={td}>{offset + i + 1}</td>
                  <td style={td}>{r.date}</td>
                  <td style={td}>{r.checkIn || '--'}</td>
                  <td style={td}>{r.checkOut || '--'}</td>
                  <td style={td}>{r.totalHours != null ? r.totalHours.toFixed(1) : '--'}</td>
                  <td style={td}><span style={statusBadge(r.status)}>{statusLabel(r.status)}</span></td>
                </tr>
              ))}
              {!rows.length && <tr><td style={{ padding: 16 }} colSpan={6}>Không có dữ liệu</td></tr>}
            </tbody>
          </table>
          </>
        )}
      </div>
    </StaffLayout>
  );
}

function statusLabel(s: AttendanceRow['status']) {
  return { late: 'Đi trễ', early: 'Về sớm', working: 'Đang làm việc', normal: 'Bình thường', absent: 'Vắng' }[s];
}
function statusBadge(s: AttendanceRow['status']): React.CSSProperties {
  const c: Record<AttendanceRow['status'], string> = {
    late: '#e74c3c', early: '#f39c12', working: '#16a085', normal: '#3498db', absent: '#7f8c8d'
  };
  return { background: c[s], color: '#fff', padding: '4px 8px', borderRadius: 4, fontSize: 12 };
}
const headRow: React.CSSProperties = { background: '#f5f5f5' };
const th: React.CSSProperties = { padding: 10, fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d', letterSpacing: '.5px', textAlign: 'left' };
const row: React.CSSProperties = { borderTop: '1px solid #ecf0f1' };
const td: React.CSSProperties = { padding: 10, fontSize: 14 };