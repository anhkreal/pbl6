import React, { useEffect, useState } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import { fetchCheckLogs, AttendanceRow } from '../../api/attendance';
import { apiFetch } from '../../api/http';
import ErrorBanner from '../../components/ErrorBanner';

export default function StaffAttendance() {
  function todayGmt7() {
    const nowUtc = Date.now();
    const gmt7 = new Date(nowUtc + 7 * 60 * 60 * 1000);
    const y = gmt7.getUTCFullYear();
    const m = String(gmt7.getUTCMonth() + 1).padStart(2, '0');
    const d = String(gmt7.getUTCDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  const [day, setDay] = useState(todayGmt7());
  const [rows, setRows] = useState<AttendanceRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState<number | null>(null);
  const [refresh, setRefresh] = useState(0);

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
  }, [day, limit, offset, refresh]);

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 18 }}>Chấm công (Xem theo ngày)</h1>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-body">
          <input type="date" value={day} onChange={e => setDay(e.target.value)} />
        </div>
      </div>
      <div className="card">
        {loading && <div className="card-body">Đang tải...</div>}
        {error && <div className="card-body"><ErrorBanner message={error} onRetry={()=>setRefresh(v=>v+1)} /></div>}
        {!loading && !error && (
          <>
          <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>Tổng: <strong>{total ?? 0}</strong></div>
            <div>
              <button className="btn btn-ghost" disabled={offset <= 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Prev</button>
              <button className="btn btn-ghost" style={{ marginLeft: 8 }} disabled={offset + limit >= (total ?? 0)} onClick={() => setOffset(offset + limit)}>Next</button>
            </div>
          </div>
          <table className="table">
            <thead><tr>{['STT', 'Ngày', 'Check in', 'Check out', 'Giờ làm', 'Trạng thái'].map(h => <th key={h}>{h}</th>)}</tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.id}>
                  <td>{offset + i + 1}</td>
                  <td>{r.date}</td>
                  <td>{r.checkIn || '--'}</td>
                  <td>{r.checkOut || '--'}</td>
                  <td>{r.totalHours != null ? r.totalHours.toFixed(1) : '--'}</td>
                  <td><span className={statusBadgeClass(r.status)}>{statusLabel(r.status)}</span></td>
                </tr>
              ))}
              {!rows.length && <tr><td colSpan={6} style={{ padding: 16 }}>Không có dữ liệu</td></tr>}
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
function statusBadgeClass(s: AttendanceRow['status']): string {
  const m: Record<AttendanceRow['status'], string> = {
    late: 'badge badge-danger',
    early: 'badge badge-warning',
    working: 'badge badge-success',
    normal: 'badge badge-info',
    absent: 'badge'
  };
  return m[s] || 'badge';
}