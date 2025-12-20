import React, { useEffect, useState } from 'react';
import AdminLayout from '../../layouts/AdminLayout';
import { fetchCheckLogs, patchAttendanceStatus, AttendanceRow } from '../../api/attendance';
import { verifyPin } from '../../api/pin';
import ErrorBanner from '../../components/ErrorBanner';
import SkeletonTable from '../../components/SkeletonTable';
import { downloadCSV } from '../../utils/csv';

export default function AdminAttendance(){
  function todayGmt7() {
    const nowUtc = Date.now();
    const gmt7 = new Date(nowUtc + 7 * 60 * 60 * 1000);
    const y = gmt7.getUTCFullYear();
    const m = String(gmt7.getUTCMonth() + 1).padStart(2, '0');
    const d = String(gmt7.getUTCDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  const [day, setDay] = useState(todayGmt7());
  const [name, setName] = useState('');
  const [editId, setEditId] = useState<number | null>(null);
  const [pinValue, setPinValue] = useState('');
  const [rows, setRows] = useState<AttendanceRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState<number | null>(null);
  const [totalAll, setTotalAll] = useState<number | null>(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true); setError('');
      try {
        const data = await fetchCheckLogs({ date_from: day, date_to: day, limit, offset, status: name || undefined });
        if (!ignore) {
          setRows(data.checklogs);
          setTotal(data.total);
          setTotalAll((data as any).total_all ?? null);
        }
      } catch (e:any) {
        setError(e.message || 'Load thất bại');
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [day, name, limit, offset, refresh]);

  const handleEdit = (recordId: number) => {
    setEditId(recordId);
  };

  const confirmEdit = async () => {
    if (editId === null) return;
    const trimmed = String(pinValue ?? '').trim();
    console.debug('[AdminAttendance] confirmEdit pin raw:', pinValue, 'trimmed:', trimmed);
    const ok = await verifyPin(trimmed);
    if (!ok) { alert('PIN sai'); return; }
    try {
      await patchAttendanceStatus(editId);
      setRows(r => r.map(x => x.id === editId ? { ...x, status: 'normal' } : x));
    } catch (e:any) {
      alert(e.message || 'Cập nhật lỗi');
    } finally {
      setEditId(null); setPinValue('');
    }
  };

  return (
    <AdminLayout>
      <h1 style={{ marginBottom: 18 }}>Quản lý chấm công</h1>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-body">
          <label style={{ marginRight: 10, fontWeight: 600 }}>Chọn ngày:</label>
          <input
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
          />
        </div>
      </div>

      <div className="card">
        <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>Tổng: <strong>{(totalAll ?? total) ?? 0}</strong></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button className="btn" onClick={() => {
              const headers = [
                { key: 'userName', label: 'NhanVien' },
                { key: 'date', label: 'Ngay' },
                { key: 'checkIn', label: 'CheckIn' },
                { key: 'checkOut', label: 'CheckOut' },
                { key: 'totalHours', label: 'GioLam' },
                { key: 'shift', label: 'Ca' },
                { key: 'status', label: 'TrangThai' },
              ];
              downloadCSV('attendance_admin.csv', rows.map(r => ({
                userName: r.userName,
                date: r.date,
                checkIn: r.checkIn || '',
                checkOut: r.checkOut || '',
                totalHours: r.totalHours ?? '',
                shift: r.shift,
                status: r.status
              })), headers);
            }}>Xuất CSV</button>
            <button className="btn btn-ghost" disabled={offset <= 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Prev</button>
            <button className="btn btn-ghost" style={{ marginLeft: 8 }} disabled={(() => { const cap = (totalAll ?? total) ?? 0; return offset + limit >= cap; })()} onClick={() => setOffset(offset + limit)}>Next</button>
          </div>
        </div>
        {!loading && (
        <table className="table">
          <thead>
            <tr>
              <th>Nhân viên</th>
              <th>Ngày</th>
              <th>Check-in</th>
              <th>Check-out</th>
              <th>Giờ làm</th>
              <th>Ca</th>
              <th>Trạng thái</th>
              <th>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(record => (
              <tr key={record.id}>
                <td>{record.userName}</td>
                <td>{record.date}</td>
                <td>{record.checkIn || '--'}</td>
                <td>{record.checkOut || '--'}</td>
                <td>{record.totalHours != null ? `${record.totalHours}h` : '--'}</td>
                <td>
                  <span className={shiftBadgeClass(record.shift)}>{record.shift === 'day' ? 'Sáng' : 'Tối'}</span>
                </td>
                <td>
                  <span className={statusBadgeClass(record.status)}>
                    {record.status === 'late' ? 'Trễ' :
                     record.status === 'early' ? 'Về sớm' :
                     record.status === 'working' ? 'Đang làm việc' :
                     record.status === 'normal' ? 'Đúng giờ' : 'Vắng'}
                  </span>
                </td>
                <td>
                  {(record.status === 'late' || record.status === 'early') && (
                    <button className="btn btn-primary" onClick={() => handleEdit(record.id)}>Chỉnh sửa</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )}
        {loading && <div className="card-body"><SkeletonTable rows={6} cols={8} /></div>}
        {error && <div className="card-body"><ErrorBanner message={error} onRetry={()=>setRefresh(v=>v+1)} /></div>}
      </div>

      {editId !== null && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            minWidth: '300px'
          }}>
            <h3 style={{ marginBottom: '20px' }}>Xác nhận mã PIN</h3>
            <input
              type="password"
              placeholder="Nhập mã PIN (6 số)"
              value={pinValue}
              onChange={(e) => setPinValue(e.target.value)}
              maxLength={6}
              style={{
                width: '100%',
                padding: '10px',
                marginBottom: '15px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                boxSizing: 'border-box'
              }}
            />
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn btn-primary" onClick={confirmEdit} style={{ flex: 1 }}>Xác nhận</button>
              <button className="btn btn-ghost" onClick={() => { setEditId(null); setPinValue(''); }} style={{ flex: 1 }}>Hủy</button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}

function statusBadgeClass(s: AttendanceRow['status']): string {
  const m: Record<AttendanceRow['status'], string> = {
    late: 'badge badge-danger',
    early: 'badge badge-warning',
    working: 'badge badge-success',
    normal: 'badge badge-info',
    absent: 'badge'
  };
  return m[s] || 'badge';
}

function shiftBadgeClass(shift: 'day' | 'night'): string {
  return shift === 'day' ? 'badge badge-info' : 'badge badge-warning';
}