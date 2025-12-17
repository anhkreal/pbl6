import React, { useState, useEffect } from 'react';
import AdminLayout from '../../layouts/AdminLayout';
import { fetchKPI, KPIItem } from '../../api/kpi';
import ErrorBanner from '../../components/ErrorBanner';

const td: React.CSSProperties = { padding: 10, fontSize: 14 };

export default function AdminKPIReport() {
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
  const [value, setValue] = useState(todayGmt7());
  const [name, setName] = useState('');
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
        if (mode === 'day') {
          const data = await fetchKPI('day', value, name || undefined, 30, 0);
          if (!ignore) setItems(data);
        } else {
          const data = await fetchKPI('month', value, name || undefined, 100, 0);
          if (!ignore) setItems(data);
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; }
  }, [mode, value, name, refresh]);

  const avg = (arr: number[]) => arr.length ? (arr.reduce((a, b) => a + b, 0) / arr.length) : 0;

  const filtered = items.filter(k => (!name || k.userName.toLowerCase().includes(name.toLowerCase())));

  return (
    <AdminLayout>
      <h1 style={{ marginBottom: 18 }}>KPI Report</h1>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <label style={{ marginRight: 8 }}>Chế độ:</label>
            <select value={mode} onChange={e => { const v = e.target.value as 'day'|'month'; setMode(v); setValue(v === 'day' ? todayGmt7() : thisMonthGmt7()); }}>
              <option value="day">Theo ngày</option>
              <option value="month">Theo tháng</option>
            </select>
          </div>
          {mode === 'day' ? (
            <input type="date" value={value} onChange={e => setValue(e.target.value)} />
          ) : (
            <input type="month" value={value} onChange={e => setValue(e.target.value)} />
          )}
          <input placeholder="Tên nhân viên" value={name} onChange={e => setName(e.target.value)} />
        </div>
      </div>

      <div style={{ marginBottom: 20, display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 16 }}>
        <Stat label="Avg Emotion" value={avg(filtered.map(f => f.emotionScore)).toFixed(2)} color="#9b59b6" />
        <Stat label="Avg Attendance" value={avg(filtered.map(f => f.attendanceScore)).toFixed(2)} color="#3498db" />
        <Stat label="Avg Total KPI" value={avg(filtered.map(f => f.totalScore)).toFixed(2)} color="#16a085" />
        <Stat label="Records" value={filtered.length.toString()} color="#e67e22" />
      </div>

      <div className="card">
        {loading && <div className="card-body">Đang tải...</div>}
        {error && <div className="card-body"><ErrorBanner message={error} onRetry={()=>setRefresh(v=>v+1)} /></div>}
        <table className="table">
          <thead>
            <tr>
              <th>Ngày</th>
              <th>Nhân viên</th>
              <th>Emotion</th>
              <th>Attendance</th>
              <th>Total</th>
              <th>Nhận xét</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(k => (
              <tr key={k.id}>
                <td>{k.date}</td>
                <td>{k.userName}</td>
                <td>{k.emotionScore.toFixed(2)}</td>
                <td>{k.attendanceScore.toFixed(2)}</td>
                <td>
                  <strong>{k.totalScore.toFixed(2)}</strong>
                </td>
                <td>{k.remark || '--'}</td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={6} style={{ padding: 16 }}>Không có dữ liệu</td></tr>}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-body">
        <span style={{ fontSize: 12, letterSpacing: '.5px', textTransform: 'uppercase', color: '#7f8c8d' }}>{label}</span>
        <div style={{ fontSize: 26, fontWeight: 600, color }}>{value}</div>
      </div>
    </div>
  );
}