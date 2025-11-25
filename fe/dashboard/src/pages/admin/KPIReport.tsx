import React, { useState, useEffect } from 'react';
import AdminLayout from '../../layouts/AdminLayout';
import { fetchKPI, KPIItem } from '../../api/kpi';

const inputStyle: React.CSSProperties = { padding: 8, border: '1px solid #ccc', borderRadius: 4, flex: '1 1 200px' };
const headRow: React.CSSProperties = { borderBottom: '2px solid #ecf0f1', textAlign: 'left' };
const th: React.CSSProperties = { padding: 10, fontSize: 13, textTransform: 'uppercase', letterSpacing: '.5px', color: '#7f8c8d' };
const td: React.CSSProperties = { padding: 10, fontSize: 14 };

export default function AdminKPIReport() {
  const [mode, setMode] = useState<'day' | 'month'>('day');
  const [value, setValue] = useState('2025-01-27');
  const [name, setName] = useState('');
  const [items, setItems] = useState<KPIItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
  }, [mode, value, name]);

  const avg = (arr: number[]) => arr.length ? (arr.reduce((a, b) => a + b, 0) / arr.length) : 0;

  const filtered = items.filter(k => (!name || k.userName.toLowerCase().includes(name.toLowerCase())));

  return (
    <AdminLayout>
      <h1 style={{ fontSize: 28, marginBottom: 20 }}>KPI Report</h1>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', background: '#fff', padding: 16, borderRadius: 8, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ marginRight: 8 }}>Chế độ:</label>
          <select value={mode} onChange={e => setMode(e.target.value as any)} style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}>
            <option value="day">Theo ngày</option>
            <option value="month">Theo tháng</option>
          </select>
        </div>
        {mode === 'day' ? (
          <input type="date" value={value} onChange={e => setValue(e.target.value)} style={inputStyle} />
        ) : (
          <input type="month" value={value} onChange={e => setValue(e.target.value)} style={inputStyle} />
        )}
        <input placeholder="Tên nhân viên" value={name} onChange={e => setName(e.target.value)} style={inputStyle} />
      </div>

      <div style={{ marginBottom: 20, display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 16 }}>
        <Stat label="Avg Emotion" value={(avg(filtered.map(f => f.emotionScore)) * 100).toFixed(1) + '%'} color="#9b59b6" />
        <Stat label="Avg Attendance" value={(avg(filtered.map(f => f.attendanceScore)) * 100).toFixed(1) + '%'} color="#3498db" />
        <Stat label="Avg Total KPI" value={(avg(filtered.map(f => f.totalScore)) * 100).toFixed(1) + '%'} color="#16a085" />
        <Stat label="Records" value={filtered.length.toString()} color="#e67e22" />
      </div>

      <div style={{ background: '#fff', padding: 16, borderRadius: 8 }}>
        {loading && <div style={{ padding: 10 }}>Đang tải...</div>}
        {error && <div style={{ padding: 10, color: 'red' }}>{error}</div>}
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={headRow}>
              <th style={th}>Ngày</th>
              <th style={th}>Nhân viên</th>
              <th style={th}>Emotion</th>
              <th style={th}>Attendance</th>
              <th style={th}>Total</th>
              <th style={th}>Nhận xét</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(k => (
              <tr key={k.id} style={{ borderBottom: '1px solid #ecf0f1' }}>
                <td style={td}>{k.date}</td>
                <td style={td}>{k.userName}</td>
                <td style={td}>{(k.emotionScore * 100).toFixed(1)}%</td>
                <td style={td}>{(k.attendanceScore * 100).toFixed(1)}%</td>
                <td style={td}>
                  <strong>{(k.totalScore * 100).toFixed(1)}%</strong>
                </td>
                <td style={td}>{k.remark || '--'}</td>
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
    <div style={{ background: '#fff', padding: 16, borderRadius: 8, boxShadow: '0 2px 4px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: 8 }}>
      <span style={{ fontSize: 12, letterSpacing: '.5px', textTransform: 'uppercase', color: '#7f8c8d' }}>{label}</span>
      <span style={{ fontSize: 26, fontWeight: 600, color }}>{value}</span>
    </div>
  );
}