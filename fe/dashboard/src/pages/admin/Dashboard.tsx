import React, { useEffect, useState } from 'react';
import AdminLayout from '../../layouts/AdminLayout';
import { fetchCheckLogs } from '../../api/attendance';
import { fetchEmotionLogs } from '../../api/emotions';

export default function AdminDashboard() {
  function todayGmt7() {
    const nowUtc = Date.now();
    const gmt7 = new Date(nowUtc + 7 * 60 * 60 * 1000);
    const y = gmt7.getUTCFullYear();
    const m = String(gmt7.getUTCMonth() + 1).padStart(2, '0');
    const d = String(gmt7.getUTCDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  function todayRangeIsoGmt7() {
    const nowUtc = Date.now();
    const start = new Date(nowUtc + 7 * 60 * 60 * 1000);
    start.setUTCHours(0, 0, 0, 0);
    const end = new Date(nowUtc + 7 * 60 * 60 * 1000);
    end.setUTCHours(23, 59, 59, 999);
    return { start: start.toISOString(), end: end.toISOString() };
  }

  const [checkedIn, setCheckedIn] = useState(0);
  const [working, setWorking] = useState(0);
  const [late, setLate] = useState(0);
  const [positivity, setPositivity] = useState(0);

  useEffect(() => {
    let timer: any;
    let stop = false;
    async function refresh() {
      const day = todayGmt7();
      try {
        const base = await fetchCheckLogs({ date_from: day, date_to: day, limit: 1, offset: 0 });
        setCheckedIn(base.total || 0);
      } catch {}
      try {
        const work = await fetchCheckLogs({ date_from: day, date_to: day, status: 'working', limit: 1, offset: 0 });
        setWorking(work.total || 0);
      } catch {}
      try {
        const lateRes = await fetchCheckLogs({ date_from: day, date_to: day, status: 'late', limit: 1, offset: 0 });
        setLate(lateRes.total || 0);
      } catch {}
      try {
        const { start, end } = todayRangeIsoGmt7();
        const logs = await fetchEmotionLogs({ start_ts: start, end_ts: end, limit: 400, offset: 0 });
        let total = logs.total || logs.logs.length || 0;
        if (total === 0) { setPositivity(1); return; }
        let neg = 0;
        for (const l of logs.logs) {
          const e = (l.emotion || '').toLowerCase();
          if (e.includes('anger') || e.includes('angry') || e.includes('sad') || e.includes('fear') || e.includes('disgust')) neg++;
        }
        const pos = Math.max(0, Math.min(1, (total - neg) / total));
        setPositivity(pos);
      } catch {}
    }
    refresh();
    timer = setInterval(refresh, 10000);
    return () => { stop = true; if (timer) clearInterval(timer); }
  }, []);

  const stats = [
    { label: 'Đã check-in', value: checkedIn, color: '#2ecc71' },
    { label: 'Trong ca', value: working, color: '#3498db' },
    { label: 'Đi muộn', value: late, color: '#e74c3c' },
    { label: 'Tích cực', value: (positivity * 100).toFixed(0) + '%', color: '#9b59b6' }
  ];
  return (
    <AdminLayout>
      <h1 style={{ marginBottom: 20 }}>Dashboard</h1>
      <div style={{ display: 'grid', gap: 18, gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))' }}>
        {stats.map(s => (
          <div key={s.label} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-body">
              <span style={{ fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d' }}>{s.label}</span>
              <div style={{ fontSize: 26, fontWeight: 600, color: s.color }}>{s.value}</div>
            </div>
          </div>
        ))}
      </div>
    </AdminLayout>
  );
}