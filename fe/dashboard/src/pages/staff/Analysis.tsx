import React, { useEffect, useMemo, useState } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import EmotionChart from '../../components/EmotionChart';
import BarChart from '../../components/BarChart';
import { fetchEmotionLogs } from '../../api/emotions';
import { fetchCheckLogs } from '../../api/attendance';
import { fetchKPI } from '../../api/kpi';
import { apiFetch } from '../../api/http';
import ErrorBanner from '../../components/ErrorBanner';

export default function StaffAnalysis() {
  const [mode, setMode] = useState<'day'|'month'>('day');
  const [day, setDay] = useState(todayGmt7());
  const [month, setMonth] = useState(thisMonthGmt7());
  const [uid, setUid] = useState<number | null>(null);

  const [kpi, setKpi] = useState<number>(0);
  const [negDist, setNegDist] = useState({ angry: 0, sad: 0, fear: 0, disgust: 0 });
  const [hoursSeries, setHoursSeries] = useState<{ label: string; value: number }[]>([]);
  const [negSeries, setNegSeries] = useState<{ label: string; value: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);

  useEffect(() => { resolveUserId().then(setUid); }, []);

  useEffect(() => {
    if (!uid) return;
    let ignore = false;
    (async () => {
      setLoading(true); setError('');
      try {
        if (mode === 'day') {
          const { start, end } = dayRangeIsoGmt7(day);
          // KPI
          const items = await fetchKPI('day', day, uid, 1, 0);
          if (!ignore && items?.length) setKpi(items[0].totalScore);
          // Emotions
          const logs = await fetchEmotionLogs({ user_id: uid, start_ts: start.toISOString(), end_ts: end.toISOString(), limit: 500, offset: 0 });
          if (!ignore) setNegDist(toNegDist(logs.logs));
          // Attendance hours (single day)
          const chk = await fetchCheckLogs({ user_id: uid, date_from: day, date_to: day, limit: 100, offset: 0 });
          const h = dailyHoursFromLogs(chk.checklogs);
          if (!ignore) setHoursSeries([{ label: day.slice(5), value: h[day] ?? 0 }]);
          if (!ignore) setNegSeries([{ label: day.slice(5), value: sumNegDist(toNegDist(logs.logs)) }]);
        } else {
          // month mode
          const monthStr = month;
          const { from, to } = monthBoundsGmt7(monthStr);
          // KPI aggregated for month
          const items = await fetchKPI('month', monthStr, uid, 1, 0);
          if (!ignore && items?.length) setKpi(items[0].totalScore);
          // Emotions over month
          const logs = await fetchEmotionLogs({ user_id: uid, start_ts: from.toISOString(), end_ts: to.toISOString(), limit: 2000, offset: 0 });
          const perDayNeg = aggregateNegByDay(logs.logs);
          if (!ignore) setNegSeries(Object.keys(perDayNeg).sort().map(d => ({ label: d.slice(5), value: perDayNeg[d] })));
          // Attendance over month
          const chk = await fetchCheckLogs({ user_id: uid, date_from: fmtYmd(from), date_to: fmtYmd(to), limit: 1000, offset: 0 });
          const perDayH = dailyHoursFromLogs(chk.checklogs);
          const series = Object.keys(perDayH).sort().map(d => ({ label: d.slice(5), value: perDayH[d] }));
          if (!ignore) setHoursSeries(series);
          // quick dist for legend (from whole month)
          if (!ignore) setNegDist(toNegDist(logs.logs));
        }
      } catch (e:any) {
        if (!ignore) setError(e.message || 'Lỗi tải dữ liệu');
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [mode, day, month, uid, refresh]);

  const conclusion = useMemo(() => buildConclusion({ kpi, negDist, hoursSeries }), [kpi, negDist, hoursSeries]);

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 16 }}>Phân tích cá nhân</h1>
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="card-body" style={{ display: 'flex', gap: 12 }}>
          <select value={mode} onChange={e => setMode(e.target.value as any)}>
            <option value="day">Theo ngày</option>
            <option value="month">Theo tháng</option>
          </select>
          {mode === 'day' && <input type="date" value={day} onChange={e => setDay(e.target.value)} />}
          {mode === 'month' && <input type="month" value={month} onChange={e => setMonth(e.target.value)} />}
        </div>
      </div>

      {loading && <div className="card"><div className="card-body">Đang tải...</div></div>}
      {error && <div className="card"><div className="card-body"><ErrorBanner message={error} onRetry={()=>setRefresh(v=>v+1)} /></div></div>}

      {!loading && !error && (
        <>
          <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', marginBottom: 16 }}>
            <Card label="KPI" value={kpi.toFixed(2)} color="#9b59b6" />
            <Card label="Tổng giờ" value={sumSeries(hoursSeries).toFixed(1) + 'h'} color="#16a085" />
            <Card label="Số cảm xúc tiêu cực" value={String(sumNegDist(negDist))} color="#e67e22" />
          </div>

          <div style={{ display: 'grid', gap: 16, gridTemplateColumns: '1fr 1fr' }}>
            <div className="card">
              <div className="card-body">
                <h3>Biểu đồ cảm xúc tiêu cực</h3>
                <EmotionChart dist={negDist} />
              </div>
            </div>
            <div className="card">
              <div className="card-body">
                <BarChart title={mode === 'day' ? 'Giờ làm hôm nay' : 'Giờ làm theo ngày'} data={hoursSeries} color="#3498db" />
                <div style={{ height: 12 }} />
                <BarChart title={mode === 'day' ? 'Số cảm xúc tiêu cực hôm nay' : 'Tiêu cực theo ngày'} data={negSeries} color="#e74c3c" />
              </div>
            </div>
          </div>

          <div className="card" style={{ marginTop: 16 }}>
            <div className="card-body">
              <h3>Kết luận</h3>
              <ul>
                {conclusion.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
          </div>
        </>
      )}
    </StaffLayout>
  );
}

function Card({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-body">
        <span style={{ fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d' }}>{label}</span>
        <div style={{ fontSize: 26, fontWeight: 600, color }}>{value}</div>
      </div>
    </div>
  );
}


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
function dayRangeIsoGmt7(ymd: string) {
  const [y, m, d] = ymd.split('-').map(Number);
  const start = new Date(Date.UTC(y, (m - 1), d, 0, 0, 0));
  const end = new Date(Date.UTC(y, (m - 1), d, 23, 59, 59, 999));
  return { start, end };
}
function monthBoundsGmt7(ym: string) {
  const [y, m] = ym.split('-').map(Number);
  const from = new Date(Date.UTC(y, (m - 1), 1, 0, 0, 0));
  const to = new Date(Date.UTC(y, m, 0, 23, 59, 59, 999));
  return { from, to };
}
function fmtYmd(d: Date) {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const da = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${da}`;
}
async function resolveUserId(): Promise<number | null> {
  const possibleKeys = ['userId', 'user_id', 'id', 'uid'];
  for (const k of possibleKeys) {
    const v = sessionStorage.getItem(k);
    if (v) {
      const n = Number(v);
      if (!Number.isNaN(n) && n > 0) return n;
      try { const parsed = JSON.parse(v); const cand = Number(parsed?.id ?? parsed?.user_id); if (!Number.isNaN(cand) && cand > 0) return cand; } catch {}
    }
  }
  try { const me:any = await apiFetch('/auth/me'); const c = Number(me?.id ?? me?.user_id ?? me?.user?.id); if (!Number.isNaN(c) && c > 0) return c; } catch {}
  try { const username = sessionStorage.getItem('userName'); if (username) { const info:any = await apiFetch(`/taikhoan/${encodeURIComponent(username)}`); const uid = Number(info?.user?.id ?? info?.id); if (!Number.isNaN(uid) && uid > 0) { sessionStorage.setItem('userId', String(uid)); return uid; } } } catch {}
  return null;
}
function toNegDist(logs: any[]) {
  const neg = { angry: 0, sad: 0, fear: 0, disgust: 0 } as any;
  for (const l of logs) {
    const e = (l.emotion || '').toLowerCase();
    if (e.includes('anger') || e.includes('angry')) neg.angry++;
    else if (e.includes('sad')) neg.sad++;
    else if (e.includes('fear')) neg.fear++;
    else if (e.includes('disgust')) neg.disgust++;
  }
  return neg;
}
function sumNegDist(d: { angry: number; sad: number; fear: number; disgust: number }) { return d.angry + d.sad + d.fear + d.disgust; }
function aggregateNegByDay(logs: any[]) {
  const map: Record<string, number> = {};
  for (const l of logs) {
    const ts = l.timestamp || l.captured_at || '';
    const day = ts ? (new Date(ts)).toISOString().slice(0,10) : 'unknown';
    const e = (l.emotion || '').toLowerCase();
    const isNeg = e.includes('anger') || e.includes('angry') || e.includes('sad') || e.includes('fear') || e.includes('disgust');
    if (!map[day]) map[day] = 0;
    if (isNeg) map[day]++;
  }
  return map;
}
function dailyHoursFromLogs(rows: any[]) {
  const map: Record<string, number> = {};
  for (const r of rows) {
    const key = r.date;
    if (!map[key]) map[key] = 0;
    const th = Number(r.totalHours ?? r.total_hours ?? 0);
    if (Number.isFinite(th) && th > 0) map[key] += th;
    else if (r.check_in && r.check_out) {
      try {
        const start = new Date(`${r.date}T${r.check_in}:00+07:00`).getTime();
        const end = new Date(`${r.date}T${r.check_out}:00+07:00`).getTime();
        const hrs = Math.max(0, (end - start) / 3600000);
        map[key] += hrs;
      } catch {}
    }
  }
  return map;
}
function sumSeries(s: { label: string; value: number }[]) { return s.reduce((a, b) => a + b.value, 0); }
function negRate(dist: { angry: number; sad: number; fear: number; disgust: number }) {
  const total = Math.max(1, dist.angry + dist.sad + dist.fear + dist.disgust);
  return ((dist.angry + dist.sad + dist.fear + dist.disgust) / total) * 100;
}
function buildConclusion({ kpi, negDist, hoursSeries }: { kpi: number; negDist: any; hoursSeries: { label:string; value:number }[] }) {
  const out: string[] = [];
  // Strengths
  if (kpi >= 85) out.push('Điểm mạnh: Hiệu suất công việc tốt và ổn định.');
  if (sumSeries(hoursSeries) >= 8) out.push('Điểm mạnh: Thời lượng làm việc đầy đủ.');
  // Weaknesses
  const neg = sumNegDist(negDist);
  if (neg > 5) out.push('Điểm yếu: Tần suất cảm xúc tiêu cực cao.');
  if (sumSeries(hoursSeries) < 6) out.push('Điểm yếu: Thời lượng làm việc thấp hơn kỳ vọng.');
  // Improvements
  if (neg > 5) out.push('Cần cải thiện: Quản lý căng thẳng và giao tiếp tích cực.');
  if (kpi < 75) out.push('Cần cải thiện: Tập trung tăng hiệu quả và chất lượng công việc.');
  if (!out.length) out.push('Tổng quan: Hiệu suất ổn, tiếp tục duy trì.');
  return out;
}
