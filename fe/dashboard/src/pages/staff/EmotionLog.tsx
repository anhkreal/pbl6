import { useEffect, useState, useMemo } from 'react';
import { fetchEmotionLogsForUser, EmotionLog } from '../../api/emotions';
import { apiFetch } from '../../api/http';
import ErrorBanner from '../../components/ErrorBanner';
import StaffLayout from '../../layouts/StaffLayout';
import { resolveUserId } from '../../utils/user';
import SkeletonTable from '../../components/SkeletonTable';
import { downloadCSV } from '../../utils/csv';

function emotionBadgeClass(emotion: string): string {
  const map: Record<string, string> = {
    angry: 'badge badge-danger',
    sad: 'badge badge-info',
    fear: 'badge',
    disgust: 'badge badge-success',
    neutral: 'badge',
    happy: 'badge badge-warning',
  };
  return map[emotion] || 'badge';
}

export default function StaffEmotionLog() {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [logs, setLogs] = useState<EmotionLog[]>([]);
  const [userId, setUserId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [total, setTotal] = useState<number | null>(null);
  const [totalAll, setTotalAll] = useState<number | null>(null);
  const [limit] = useState(30);
  const [offset, setOffset] = useState(0);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true);
      setError('');

      // Resolve user id centrally
      let resolvedId = await resolveUserId();
      try {
        // fallback path retained via resolveUserId implementation

        if (!resolvedId) {
          throw new Error('Không xác định userId. Vui lòng đăng nhập lại.');
        }

        sessionStorage.setItem('userId', String(resolvedId));
        setUserId(resolvedId);

        const res = await fetchEmotionLogsForUser(resolvedId, {
          start_ts: from || undefined,
          end_ts: to || undefined,
          limit,
          offset,
          include_image_base64: true,
        });
        if (!ignore) {
          setLogs(res.logs || []);
          setTotal(res.total ?? null);
          setTotalAll((res as any).total_all ?? null);
        }
      } catch (e: any) {
        if (!ignore) setError(e?.message || 'Lỗi tải dữ liệu');
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [from, to, offset, limit, refresh]);

  const rows = useMemo(() => Array.isArray(logs) ? logs : [], [logs]);

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 18 }}>EmotionLog (cá nhân)</h1>
      {total !== null && <div style={{ marginBottom: 12 }}>Tổng bản ghi: {total}</div>}
      {error && <div style={{ marginBottom: 12 }}><ErrorBanner message={error} onRetry={() => setRefresh(v => v + 1)} /></div>}

      <div className="card" style={{ marginBottom: 12 }}>
        <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <button className="btn btn-ghost" onClick={() => setOffset(o => Math.max(0, o - limit))} disabled={offset <= 0} style={{ marginRight: 8 }}>Trước</button>
            <button className="btn btn-ghost" onClick={() => setOffset(o => o + limit)} disabled={(() => {
              const cap = (totalAll ?? total);
              if (cap == null) return false; // unknown
              return offset + limit >= cap;
            })()}>Sau</button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className="btn" onClick={() => {
              const headers = [
                { key: 'id', label: 'ID' },
                { key: 'timestamp', label: 'ThoiDiem' },
                { key: 'emotion', label: 'CamXuc' },
                { key: 'userId', label: 'UserID' },
              ];
              downloadCSV('emotion_staff.csv', rows.map(r => ({ id: r.id, timestamp: r.timestamp, emotion: r.emotion, userId: r.userId })), headers);
            }}>Xuất CSV</button>
            {(() => {
              const page = Math.floor(offset / limit) + 1;
              const cap = (totalAll ?? total);
              const pages = cap != null ? Math.max(1, Math.ceil(cap / limit)) : undefined;
              return pages ? `Trang: ${page} / ${pages}` : `Trang: ${page}`;
            })()}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-body" style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
          <input type="datetime-local" value={from} onChange={e => setFrom(e.target.value)} />
          <input type="datetime-local" value={to} onChange={e => setTo(e.target.value)} />
        </div>
      </div>

      <div className="card" style={{ overflowX: 'auto' }}>
        {!loading && (
        <table className="table">
          <thead>
            <tr>
              {['STT', 'Thời điểm', 'Loại', 'Hình ảnh', 'Nhân viên'].map(h => <th key={h}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {!loading && rows.map((l, i) => (
              <tr key={l.id}>
                <td>{i + 1 + Math.floor(offset / limit) * limit}</td>
                <td>{l.timestamp.replace('T', ' ').replace('Z', '')}</td>
                <td><span className={emotionBadgeClass(l.emotion)}>{l.emotion}</span></td>
                <td>
                  {(() => {
                    const raw = (l.frameImage || '').toString().trim();
                    if (!raw) return '--';
                    const src = raw.startsWith('data:image') || raw.startsWith('http') ? raw : `data:image/jpeg;base64,${raw}`;
                    return <img src={src} alt="" style={{ width: 46, height: 46, borderRadius: 4, objectFit: 'cover' }} />;
                  })()}
                </td>
                <td>{l.userName || (l.userId ?? '--')}</td>
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr><td colSpan={5} style={{ padding: 16 }}>Không có dữ liệu</td></tr>
            )}
          </tbody>
        </table>
        )}
        {loading && <div className="card-body"><SkeletonTable rows={6} cols={5} /></div>}
      </div>
    </StaffLayout>
  );
}