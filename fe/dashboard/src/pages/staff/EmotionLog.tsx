import { useEffect, useState, useMemo } from 'react';
import { fetchEmotionLogsForUser, EmotionLog } from '../../api/emotions';
import { apiFetch } from '../../api/http';
import StaffLayout from '../../layouts/StaffLayout';

export default function StaffEmotionLog() {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [logs, setLogs] = useState<EmotionLog[]>([]);
  const [userId, setUserId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [total, setTotal] = useState<number | null>(null);
  const [limit, setLimit] = useState(30);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true);
      setError('');
      // determine current user id from sessionStorage if available
      // try common keys that may be used by different auth flows
      const possibleKeys = ['userId', 'user_id', 'id', 'uid'];
      let uid: number | null = null;
      for (const k of possibleKeys) {
        const v = sessionStorage.getItem(k);
        if (v) {
          const n = Number(v);
          if (!Number.isNaN(n) && n > 0) { uid = n; break; }
          // sometimes user info is stored as JSON
          try {
            const parsed = JSON.parse(v);
            if (parsed && (parsed.id || parsed.user_id)) {
              const candidate = Number(parsed.id ?? parsed.user_id);
              if (!Number.isNaN(candidate) && candidate > 0) { uid = candidate; break; }
            }
          } catch (_) { /* ignore parse errors */ }
        }
      }
      if (uid !== null) setUserId(uid);
      const loadData = async () => {
        setLoading(true);
        setError('');
        try {
          // resolve user id: if not found from sessionStorage, try /auth/me
          // debug: snapshot sessionStorage keys (do not print authToken)
          try {
            const keys = Object.keys(sessionStorage).filter(k => k !== 'authToken');
            const snap: Record<string,string> = {};
            for (const k of keys) snap[k] = sessionStorage.getItem(k) || '';
            console.debug('[StaffEmotionLog] sessionStorage snapshot:', snap);
          } catch (e) { console.debug('[StaffEmotionLog] sessionStorage read failed', e); }

          let resolvedId = uid;
          let me: any = null;
          if (!resolvedId) {
            try {
              me = await apiFetch('/auth/me');
              console.debug('[StaffEmotionLog] /auth/me response:', me);
              const candidate = me?.id ?? me?.user_id ?? me?.user?.id ?? null;
              console.debug('[StaffEmotionLog] candidate id from /auth/me:', candidate);
              if (candidate && !Number.isNaN(Number(candidate))) resolvedId = Number(candidate);
            } catch (e) {
              console.debug('[StaffEmotionLog] /auth/me fallback failed', e);
            }
          }
          if (!resolvedId) {
            // try to fetch user info using username endpoint as a fallback
            try {
              const username = sessionStorage.getItem('userName') || (me && me.username) || null;
              if (username) {
                const info: any = await apiFetch(`/taikhoan/${encodeURIComponent(username)}`);
                console.debug('[StaffEmotionLog] /taikhoan payload:', info);
                const uid2 = info?.user?.id ?? info?.id ?? null;
                if (uid2 && !Number.isNaN(Number(uid2))) {
                  resolvedId = Number(uid2);
                  sessionStorage.setItem('userId', String(resolvedId));
                  setUserId(resolvedId);
                }
              }
            } catch (e) {
              console.debug('[StaffEmotionLog] /taikhoan fallback failed', e);
            }
          }
          if (!resolvedId) {
            setError('Không xác định userId. Vui lòng đăng nhập lại.');
            return;
          }
          // debug: show which user_id will be sent
          console.debug('[StaffEmotionLog] fetching emotion logs for user_id=', resolvedId);
          const res = await fetchEmotionLogsForUser(resolvedId, { start_ts: from || undefined, end_ts: to || undefined, limit, offset, include_image_base64: true });
          if (!ignore) { setLogs(res.logs || []); setTotal(res.total ?? null); }
        } catch (e: any) {
          setError(e.message || 'Lỗi tải dữ liệu');
        } finally {
          if (!ignore) setLoading(false);
        }
      };
      loadData();
    })();
    return () => { ignore = true; }
  }, [from, to, limit, offset]);

  const filtered = useMemo(() => {
    const arr = Array.isArray(logs) ? logs : [];
    return arr.slice(0, 30);
  }, [logs]);

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 18 }}>EmotionLog (cá nhân)</h1>
      {total !== null && <div style={{ marginBottom: 12 }}>Tổng bản ghi: {total}</div>}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div>
          <button onClick={() => setOffset(o => Math.max(0, o - limit))} disabled={offset <= 0} style={{ marginRight: 8 }}>Trước</button>
          <button onClick={() => setOffset(o => o + limit)} disabled={total !== null && offset + limit >= (total ?? 0)}>Sau</button>
        </div>
        <div>Trang: {total === 0 ? 0 : (Math.floor(offset / limit) + 1)} / {total !== null ? (total === 0 ? 0 : Math.max(1, Math.ceil(total / limit))) : '?'}</div>
      </div>
      <div style={{ background: '#fff', padding: 16, borderRadius: 8, marginBottom: 16, display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        <input type="datetime-local" value={from} onChange={e => setFrom(e.target.value)} style={inp} />
        <input type="datetime-local" value={to} onChange={e => setTo(e.target.value)} style={inp} />
      </div>
      <div style={{ background: '#fff', borderRadius: 8, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={headRow}>
              {['STT', 'Thời điểm', 'Loại', 'Hình ảnh', 'User ID'].map(h => <th key={h} style={th}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td style={{ padding: 10 }} colSpan={5}>Đang tải...</td></tr>}
            {error && !loading && <tr><td style={{ padding: 10, color: 'red' }} colSpan={5}>
              <div>{error}</div>
                <div style={{ marginTop: 8 }}>
                <button onClick={() => { setError(''); setLoading(true); (async()=>{ try { let resolved = userId; if (!resolved) { try { const me:any = await apiFetch('/auth/me'); resolved = me?.id ?? me?.user_id ?? null; } catch(e2){ console.debug('retry /auth/me failed', e2); } }
                  if (!resolved) {
                    // try /taikhoan using stored username
                    try {
                      const username = sessionStorage.getItem('userName');
                      if (username) {
                        const info:any = await apiFetch(`/taikhoan/${encodeURIComponent(username)}`);
                        const uid2 = info?.user?.id ?? info?.id ?? null;
                        if (uid2 && !Number.isNaN(Number(uid2))) {
                          resolved = Number(uid2);
                          sessionStorage.setItem('userId', String(resolved));
                        }
                      }
                    } catch(e3){ console.debug('retry /taikhoan failed', e3); }
                  }
                  if (!resolved) throw new Error('Không xác định userId');
                  const res = await fetchEmotionLogsForUser(resolved, { start_ts: from || undefined, end_ts: to || undefined, limit: 30, offset: 0, include_image_base64: false }); setLogs(res.logs || []);
                } catch(e:any){ setError(e.message||String(e)); } finally { setLoading(false); } })(); }} style={{ padding: '6px 10px', borderRadius:4, border:'1px solid #ccc', background:'#fff', cursor:'pointer' }}>Thử lại</button>
              </div>
            </td></tr>}
            {!loading && !error && filtered.map((l, i) => (
              <tr key={l.id} style={row}>
                <td style={td}>{i + 1}</td>
                <td style={td}>{l.timestamp.replace('T', ' ').replace('Z', '')}</td>
                <td style={td}><span style={badge(l.emotion)}>{l.emotion}</span></td>
                <td style={td}>
                  {l.frameImage
                    ? <img src={l.frameImage} alt="" style={{ width: 46, height: 46, borderRadius: 4, objectFit: 'cover' }} />
                    : '--'}
                </td>
                <td style={td}>{l.userId ?? '--'}</td>
              </tr>
            ))}
            {!filtered.length && !loading && !error && <tr><td style={{ padding: 16 }} colSpan={5}>Không có dữ liệu</td></tr>}
          </tbody>
        </table>
      </div>
    </StaffLayout>
  );
}

const inp: React.CSSProperties = { padding: 8, border: '1px solid #ccc', borderRadius: 4, flex: '1 1 220px' };
const headRow: React.CSSProperties = { background: '#f5f5f5' };
const th: React.CSSProperties = { padding: 10, fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d', letterSpacing: '.5px', textAlign: 'left' };
const row: React.CSSProperties = { borderTop: '1px solid #ecf0f1' };
const td: React.CSSProperties = { padding: 10, fontSize: 14 };

// Màu cảm xúc
function badge(emotion: string): React.CSSProperties {
  const colors: Record<string, string> = {
    angry: '#e74c3c',
    sad: '#3498db',
    fear: '#9b59b6',
    disgust: '#2ecc71',
    neutral: '#7f8c8d',
    happy: '#f1c40f'
  };
  return {
    background: colors[emotion] || '#34495e',
    color: '#fff',
    padding: '4px 8px',
    borderRadius: 4,
    fontSize: 12,
    textTransform: 'lowercase'
  };
}