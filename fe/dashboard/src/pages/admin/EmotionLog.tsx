import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../layouts/AdminLayout';
import AdminPinModal from '../../components/AdminPinModal';
import { fetchEmotionLogs, deleteEmotionLog, deleteEmotionById, EmotionLog } from '../../api/emotions';
import { verifyPin } from '../../api/pin';

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
        if (!ignore) { setLogs(res.logs || []); setTotal(res.total ?? null); }
      } catch (e:any) {
        console.error('fetchEmotionLogs error', e);
        setError(e.message || String(e));
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    loadData();
    return () => { ignore = true; };
  }, [from, to, filterName, limit, offset]);

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
      <h1 style={{ fontSize: 28, marginBottom: 20 }}>Emotion Log</h1>
      <div style={{ marginBottom: 16, background: '#fff', padding: 16, borderRadius: 8, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <input placeholder="Tên nhân viên" value={filterName} onChange={e => setFilterName(e.target.value)} style={inputStyle} />
        <input type="datetime-local" value={from} onChange={e => setFrom(e.target.value)} style={inputStyle} />
        <input type="datetime-local" value={to} onChange={e => setTo(e.target.value)} style={inputStyle} />
      </div>
      <div style={{ background: '#fff', borderRadius: 8, padding: 16 }}>
        {loading && <div style={{padding:10}}>Đang tải...</div>}
        {total !== null && <div style={{padding:10}}>Tổng bản ghi: {total}</div>}
        {error && <div style={{padding:10,color:'red'}}>
          <div>{error}</div>
          <div style={{marginTop:8}}>
            <button onClick={() => { setError(''); setLoading(true); (async()=>{ try { const res = await fetchEmotionLogs({ start_ts: from || undefined, end_ts: to || undefined, staffName: filterName || undefined, emotion_type: 'negative', limit: 30, offset: 0, include_image_base64: false }); setLogs(res.logs || []); } catch(e:any){ setError(e.message||String(e)); } finally { setLoading(false); } })(); }} style={{ padding: '6px 10px', borderRadius:4, border:'1px solid #ccc', background:'#fff', cursor:'pointer' }}>Thử lại</button>
          </div>
        </div>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: 12 }}>
          <div>Trang: {total === 0 ? 0 : (Math.floor(offset / limit) + 1)} / {total !== null ? (total === 0 ? 0 : Math.max(1, Math.ceil(total / limit))) : '?'}</div>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={headRow}>
              <th style={th}>ID</th>
              <th style={th}>Nhân viên</th>
              <th style={th}>Thời điểm</th>
              <th style={th}>Cảm xúc</th>
              <th style={th}>Hình ảnh</th>
              <th style={th}>Ghi chú</th>
              <th style={th}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(log => (
              <tr key={log.id} style={{ borderBottom: '1px solid #ecf0f1' }}>
                <td style={td}>{log.id}</td>
                <td style={td}>{log.userName}</td>
                <td style={td}>{log.timestamp.replace('T',' ').replace('Z','')}</td>
                <td style={td}><span style={badge(log.emotion)}>{log.emotion}</span></td>
                <td style={td}>{log.frameImage ? (
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
                <td style={td}>{log.note || '--'}</td>
                <td style={td}>
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

const inputStyle: React.CSSProperties = { padding: 8, border: '1px solid #ccc', borderRadius: 4, flex: '1 1 200px' };
const headRow: React.CSSProperties = { borderBottom: '2px solid #ecf0f1', textAlign: 'left' };
const th: React.CSSProperties = { padding: 10, fontSize: 13, textTransform: 'uppercase', letterSpacing: '.5px', color: '#7f8c8d' };
const td: React.CSSProperties = { padding: 10, fontSize: 14 };

function badge(e: string): React.CSSProperties {
  const colors: Record<string,string>={angry:'#e74c3c',sad:'#3498db',fear:'#9b59b6',disgust:'#2ecc71',neutral:'#7f8c8d',happy:'#f1c40f'};
  return {background:colors[e]||'#34495e',color:'#fff',padding:'4px 8px',borderRadius:4,fontSize:12};
}