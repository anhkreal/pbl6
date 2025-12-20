import React, { useEffect, useState } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import { fetchKPI, KPIItem } from '../../api/kpi';
import { apiFetch } from '../../api/http';
import ErrorBanner from '../../components/ErrorBanner';
import SkeletonTable from '../../components/SkeletonTable';
import { downloadCSV } from '../../utils/csv';

export default function StaffKPIReport() {
  const [mode, setMode] = useState<'day' | 'month'>('day');
  function todayGmt7() {
    const nowUtc = Date.now();
    const gmt7 = new Date(nowUtc + 7 * 60 * 60 * 1000);
    const y = gmt7.getUTCFullYear();
    const m = String(gmt7.getUTCMonth() + 1).padStart(2, '0');
    const d = String(gmt7.getUTCDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  function thisMonthGmt7() {
    const nowUtc = Date.now();
    const gmt7 = new Date(nowUtc + 7 * 60 * 60 * 1000);
    const y = gmt7.getUTCFullYear();
    const m = String(gmt7.getUTCMonth() + 1).padStart(2, '0');
    return `${y}-${m}`;
  }
  const [day, setDay] = useState(todayGmt7());
  const [month, setMonth] = useState(thisMonthGmt7());
  const [items, setItems] = useState<KPIItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);

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
  }, [mode, day, month, refresh]);

  const getRemark = (score: number): string => {
    if (score < 60) return 'Cảnh cáo nặng';
    if (score <= 75) return 'Cần cố gắng';
    if (score <= 85) return 'Ổn';
    return 'Tốt/Xuất sắc';
  };

  const processedData = React.useMemo(() => {
    if (mode === 'month' && items.length > 0) {
      const totalRecords = items.length;
      const sum = items.reduce((acc, item) => {
        acc.attendanceScore += item.attendanceScore;
        acc.emotionScore += item.emotionScore;
        acc.totalScore += item.totalScore;
        return acc;
      }, { attendanceScore: 0, emotionScore: 0, totalScore: 0 });

      const avgTotalScore = sum.totalScore / totalRecords;
      
      const aggregatedData: KPIItem = {
        id: -1, // Mock ID for aggregated data
        userName: items[0]?.userName || 'Aggregated',
        date: month,
        attendanceScore: sum.attendanceScore / totalRecords,
        emotionScore: sum.emotionScore / totalRecords,
        totalScore: avgTotalScore,
        remark: getRemark(avgTotalScore),
      };
      return [aggregatedData];
    }
    return items;
  }, [items, mode, month]);

  const data = processedData;

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 18 }}>KPI Report (Ngày / Tháng)</h1>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-body" style={{ display: 'flex', gap: 12 }}>
        <select value={mode} onChange={e => setMode(e.target.value as any)}>
          <option value="day">Theo ngày</option>
          <option value="month">Theo tháng</option>
        </select>
        {mode === 'day' && <input type="date" value={day} onChange={e => setDay(e.target.value)} />}
        {mode === 'month' && <input type="month" value={month} onChange={e => setMonth(e.target.value)} />}
        </div>
      </div>
      <div className="card">
        <div className="card-body" style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn" onClick={() => {
            const headers = [
              { key: 'date', label: 'Ngay' },
              { key: 'attendanceScore', label: 'ChuyenCan' },
              { key: 'emotionScore', label: 'CamXuc' },
              { key: 'totalScore', label: 'Tong' },
              { key: 'remark', label: 'NhanXet' },
            ];
            downloadCSV('kpi_staff.csv', data.map(r => ({
              date: r.date,
              attendanceScore: r.attendanceScore.toFixed(2),
              emotionScore: r.emotionScore.toFixed(2),
              totalScore: r.totalScore.toFixed(2),
              remark: r.remark || ''
            })), headers);
          }}>Xuất CSV</button>
        </div>
        <table className="table">
          <thead><tr>{['STT', 'Ngày', 'Chuyên cần', 'Cảm xúc', 'Tổng', 'Nhận xét'].map(h => <th key={h}>{h}</th>)}</tr></thead>
          <tbody>
            {loading && <tr><td style={{ padding: 10 }} colSpan={6}><SkeletonTable rows={4} cols={6} /></td></tr>}
            {error && <tr><td style={{ padding: 10 }} colSpan={6}><ErrorBanner message={error} onRetry={()=>setRefresh(v=>v+1)} /></td></tr>}
            {data.map((r, i) => (
              <tr key={r.date}>
                <td>{i + 1}</td>
                <td>{r.date}</td>
                <td>{r.attendanceScore.toFixed(2)}</td>
                <td>{r.emotionScore.toFixed(2)}</td>
                <td><strong>{r.totalScore.toFixed(2)}</strong></td>
                <td>{r.remark || '--'}</td>
              </tr>
            ))}
            {!data.length && !loading && <tr><td style={{ padding: 16 }} colSpan={6}>Không có dữ liệu</td></tr>}
          </tbody>
        </table>
      </div>
    </StaffLayout>
  );
}
