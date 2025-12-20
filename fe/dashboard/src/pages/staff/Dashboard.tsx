import React, { useEffect, useState } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import EmotionChart from '../../components/EmotionChart';
import { fetchCheckLogs } from '../../api/attendance';
import { fetchKPI } from '../../api/kpi';
import { fetchEmotionLogs } from '../../api/emotions';
import { apiFetch } from '../../api/http';
import { resolveUserId } from '../../utils/user';

export default function StaffDashboard() {
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
  function parseHm(s?: string | null): string {
    if (!s) return '--';
    const m = /^(\d{2}:\d{2})/.exec(s);
    return m ? m[1] : s;
  }
  // resolveUserId moved to utils/user.ts

  const [checkIn, setCheckIn] = useState('--');
  const [hoursSoFar, setHoursSoFar] = useState(0);
  const [kpiToday, setKpiToday] = useState(0);
  const [dist, setDist] = useState({ angry: 0, sad: 0, fear: 0, disgust: 0 });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let stop = false;
    let timer: any;
    (async () => {
      const uid = await resolveUserId();
      async function refresh() {
        if (stop) return;
        const day = todayGmt7();
        // Attendance for user today
        try {
          const res = await fetchCheckLogs({ date_from: day, date_to: day, user_id: uid ?? undefined, limit: 50, offset: 0 });
          const row = res.checklogs[0];
          const hm = parseHm(row?.checkIn || null);
          setCheckIn(hm);
          // hours so far
          let hours = 0;
          if (row && row.checkIn) {
            const base = new Date(`${row.date}T${row.checkIn}:00+07:00`).getTime();
            const now = Date.now();
            const worked = row.checkOut ? (new Date(`${row.date}T${row.checkOut}:00+07:00`).getTime() - base) : (now - base);
            hours = Math.max(0, worked / 3600000);
          }
          setHoursSoFar(hours);
        } catch {}

        // KPI today for user
        try {
          if (uid) {
            const items = await fetchKPI('day', day, uid, 1, 0);
            if (items && items.length) setKpiToday(items[0].totalScore);
          }
        } catch {}

        // Emotions distribution today for user
        try {
          const { start, end } = todayRangeIsoGmt7();
          const logs = await fetchEmotionLogs({ user_id: uid ?? undefined, start_ts: start, end_ts: end, limit: 200, offset: 0 });
          const neg = { angry: 0, sad: 0, fear: 0, disgust: 0 } as any;
          for (const l of logs.logs) {
            const e = (l.emotion || '').toLowerCase();
            if (e.includes('anger') || e.includes('angry')) neg.angry++;
            else if (e.includes('sad')) neg.sad++;
            else if (e.includes('fear')) neg.fear++;
            else if (e.includes('disgust')) neg.disgust++;
          }
          setDist(neg);
        } catch {}
      }
      await refresh();
      timer = setInterval(() => { setTick(t => t + 1); refresh(); }, 10000);
    })();
    return () => { stop = true; if (timer) clearInterval(timer); };
  }, []);

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 20 }}>Dashboard cá nhân</h1>
      <div style={{
        display: 'grid',
        gap: 20,
        gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))',
        marginBottom: 28
      }}>
        <Card label="Giờ check-in" value={checkIn} color="#3498db" />
        <Card label="Giờ làm đến hiện tại" value={hoursSoFar.toFixed(1) + 'h'} color="#16a085" />
        <Card label="KPI hôm nay" value={kpiToday.toFixed(2)} color="#9b59b6" />
      </div>
      <div className="card">
        <div className="card-body">
          <h3 style={{ marginBottom: 14 }}>Biểu đồ cảm xúc tiêu cực hôm nay</h3>
          <EmotionChart dist={dist} />
        </div>
      </div>
    </StaffLayout>
  );
}

function Card({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-body">
        <span style={{ fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d', letterSpacing: '.5px' }}>{label}</span>
        <div style={{ fontSize: 28, fontWeight: 600, color }}>{value}</div>
      </div>
    </div>
  );
}