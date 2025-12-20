import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../layouts/AdminLayout';
import AdminPinModal from '../../components/AdminPinModal';
import { fetchEmotionLogs, deleteEmotionById, EmotionLog } from '../../api/emotions';
import { verifyPin } from '../../api/pin';
import ErrorBanner from '../../components/ErrorBanner';
import SkeletonTable from '../../components/SkeletonTable';
import { downloadCSV } from '../../utils/csv';

type AdminEmotionLog = EmotionLog & { note?: string };

export default function EmotionLogPage() {
  const [logs, setLogs] = useState<AdminEmotionLog[]>([]);
  const [filterName, setFilterName] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [pendingDelete, setPendingDelete] = useState<number | null>(null); // holds log id to delete
  const [openMenuFor, setOpenMenuFor] = useState<number | null>(null);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [total, setTotal] = useState<number | null>(null);
  const [totalAll, setTotalAll] = useState<number | null>(null);
  const [pinValue, setPinValue] = useState('');
  const [limit, setLimit] = useState(30);
  const [offset, setOffset] = useState(0);

  const filtered = useMemo(() => {
    const arr = Array.isArray(logs) ? logs : [];
    return arr.filter(l =>
      (!filterName || l.userName.toLowerCase().includes(filterName.toLowerCase())) &&
      (!from || l.timestamp >= from) &&
      (!to || l.timestamp <= to)
    );
  }, [logs, filterName, from, to]);

  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let ignore = false;
    const loadData = async () => {
      setLoading(true); setError('');
      try {
        const res = await fetchEmotionLogs({
          start_ts: from || undefined,
          end_ts: to || undefined,
          staffName: filterName || undefined,
          limit,
          offset,
          include_image_base64: true
        });
        if (!ignore) { setLogs(res.logs || []); setTotal(res.total ?? null); setTotalAll((res as any).total_all ?? null); }
      } catch (e:any) {
        console.error('fetchEmotionLogs error', e);
        setError(e.message || String(e));
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    loadData();
    return () => { ignore = true; };
  }, [from, to, filterName, limit, offset, refresh]);

  const confirmDelete = async () => {
    if (pendingDelete === null) return;
    // kept for backward compatibility (unused) - actual confirm will be called with pin param
  };

  const handleConfirmWithPin = async (pin: string) => {
    if (pendingDelete === null) return;
    console.debug('[EmotionLog] handleConfirmWithPin pendingDelete:', pendingDelete, 'pin:', pin);
    const ok = await verifyPin(pin);
    if (!ok) { alert('PIN sai'); return; }
    try {
      const res = await deleteEmotionById(pendingDelete, pin);
      if (res && res.success) {
        setLogs(ls => ls.filter(x => x.id !== pendingDelete));
        alert(res.message || 'Xóa emotion log thành công');
      } else {
        alert(res?.message || 'Xóa thất bại');
      }
    } catch (e:any) {
      alert(e?.message || 'Lỗi khi xóa');
    } finally {
      setPendingDelete(null);
    }
  };

  return (
    <AdminLayout>
      <h1 style={{ marginBottom: 18 }}>Emotion Log</h1>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-body" style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <input placeholder="Tên nhân viên" value={filterName} onChange={e => setFilterName(e.target.value)} />
          <input type="datetime-local" value={from} onChange={e => setFrom(e.target.value)} />
          <input type="datetime-local" value={to} onChange={e => setTo(e.target.value)} />
        </div>
      </div>
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
              const exportRows = (filtered.length ? filtered : logs).map(l => ({
                id: l.id,
                userName: l.userName,
                timestamp: l.timestamp,
                emotion: l.emotion,
                note: (l as any).note ?? ''
              }));
              const headers = [
                { key: 'id', label: 'ID' },
                { key: 'userName', label: 'NhanVien' },
                { key: 'timestamp', label: 'ThoiDiem' },
                { key: 'emotion', label: 'CamXuc' },
                { key: 'note', label: 'GhiChu' },
              ];
              downloadCSV('emotion_admin.csv', exportRows, headers);
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
      <div className="card">
        {loading && <div className="card-body">Đang tải...</div>}
        {totalAll !== null && <div className="card-body">Tổng bản ghi: {totalAll}</div>}
        {error && <div className="card-body"><ErrorBanner message={error} onRetry={()=>setRefresh(v=>v+1)} /></div>}
        <div className="card-body" style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}></div>
        {!loading && (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nhân viên</th>
              <th>Thời điểm</th>
              <th>Cảm xúc</th>
              <th>Hình ảnh</th>
              <th>Ghi chú</th>
              <th>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(log => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.userName}</td>
                <td>{log.timestamp.replace('T',' ').replace('Z','')}</td>
                <td><span className={emotionBadgeClass(log.emotion)}>{log.emotion}</span></td>
                <td>{log.frameImage ? (
                  <img
                    src={
                      log.frameImage.startsWith('data:image')
                        ? log.frameImage
                        : `data:image/jpeg;base64,${log.frameImage}`
                    }
                    alt=""
                    style={{ width: 48, height: 48, borderRadius: 4, objectFit: 'cover' }}
                  />
                ) : '--'}</td>
                <td>{log.note || '--'}</td>
                <td>
                  <div style={{ position: 'relative', display: 'inline-block' }}>
                    <button
                      onClick={(e) => { e.stopPropagation(); setOpenMenuFor(openMenuFor === log.id ? null : log.id); }}
                      aria-expanded={openMenuFor === log.id}
                      title="Hành động"
                      style={{ padding: '6px 8px', background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 18, color: '#2c3e50' }}
                    >⋮</button>
                    {openMenuFor === log.id && (
                      <div style={{ position: 'absolute', right: 0, top: '100%', background: '#fff', border: '1px solid #ddd', boxShadow: '0 4px 8px rgba(0,0,0,0.08)', borderRadius: 6, overflow: 'hidden', zIndex: 50 }}>
                        <button onClick={() => { setPendingDelete(log.id); setOpenMenuFor(null); }} style={{ display: 'block', padding: '8px 12px', width: 180, textAlign: 'left', border: 'none', background: 'transparent', cursor: 'pointer' }}>Xóa</button>
                        <button onClick={() => { setOpenMenuFor(null); const username = log.userName; navigate('/admin/employeedetail?username=' + encodeURIComponent(String(username))); }} style={{ display: 'block', padding: '8px 12px', width: 180, textAlign: 'left', border: 'none', background: 'transparent', cursor: 'pointer' }}>Xem nhân viên</button>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td style={{ padding: 16 }} colSpan={7}>Không có dữ liệu</td></tr>
            )}
          </tbody>
        </table>
        )}
        {loading && <div className="card-body"><SkeletonTable rows={6} cols={7} /></div>}
      </div>
      <AdminPinModal
        open={pendingDelete !== null}
        title="Xác nhận xóa log cảm xúc"
        onConfirm={handleConfirmWithPin}
        onCancel={() => setPendingDelete(null)}
      />
    </AdminLayout>
  );
}

function emotionBadgeClass(e: string): string {
  const map: Record<string,string> = {
    angry: 'badge badge-danger',
    sad: 'badge badge-info',
    fear: 'badge',
    disgust: 'badge badge-success',
    neutral: 'badge',
    happy: 'badge badge-warning',
  };
  return map[e] || 'badge';
}