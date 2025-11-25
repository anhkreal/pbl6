import React, { useEffect, useState } from 'react';
import AdminLayout from '../../layouts/AdminLayout';
import { fetchCheckLogs, patchAttendanceStatus, AttendanceRow } from '../../api/attendance';
import { verifyPin } from '../../api/pin';

export default function AdminAttendance(){
  const [day, setDay] = useState('2025-01-28');
  const [name, setName] = useState('');
  const [editId, setEditId] = useState<number | null>(null);
  const [pinValue, setPinValue] = useState('');
  const [rows, setRows] = useState<AttendanceRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState<number | null>(null);

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true); setError('');
      try {
        const data = await fetchCheckLogs({ date_from: day, date_to: day, limit, offset, status: name || undefined });
        if (!ignore) {
          setRows(data.checklogs);
          setTotal(data.total);
        }
      } catch (e:any) {
        setError(e.message || 'Load thất bại');
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [day, name, limit, offset]);

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
      <h1 style={{ marginBottom: '20px', fontSize: '28px', color: '#2c3e50' }}>Quản lý chấm công</h1>

      <div style={{ marginBottom: '20px', backgroundColor: 'white', padding: '15px', borderRadius: '8px' }}>
        <label style={{ marginRight: '10px', fontWeight: 'bold' }}>Chọn ngày:</label>
        <input
          type="date"
          value={day}
          onChange={(e) => setDay(e.target.value)}
          style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
        />
      </div>

      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <div style={{ padding: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>Tổng: <strong>{total ?? 0}</strong></div>
          <div>
            <button disabled={offset <= 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Prev</button>
            <button style={{ marginLeft: 8 }} disabled={offset + limit >= (total ?? 0)} onClick={() => setOffset(offset + limit)}>Next</button>
          </div>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ecf0f1' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Nhân viên</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Ngày</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Check-in</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Check-out</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Giờ làm</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Ca</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Trạng thái</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(record => (
              <tr key={record.id} style={{ borderBottom: '1px solid #ecf0f1' }}>
                <td style={{ padding: '12px' }}>{record.userName}</td>
                <td style={{ padding: '12px' }}>{record.date}</td>
                <td style={{ padding: '12px' }}>{record.checkIn || '--'}</td>
                <td style={{ padding: '12px' }}>{record.checkOut || '--'}</td>
                <td style={{ padding: '12px' }}>{record.totalHours != null ? `${record.totalHours}h` : '--'}</td>
                <td style={{ padding: '12px' }}>
                  <span style={{
                    padding: '4px 8px',
                    backgroundColor: record.shift === 'day' ? '#3498db' : '#9b59b6',
                    color: 'white', borderRadius: '4px', fontSize: '12px'
                  }}>{record.shift === 'day' ? 'Sáng' : 'Tối'}</span>
                </td>
                <td style={{ padding: '12px' }}>
                  <span style={{
                    padding: '4px 8px',
                    backgroundColor:
                      record.status === 'late' ? '#e74c3c' :
                      record.status === 'early' ? '#f39c12' :
                      record.status === 'working' ? '#16a085' :
                      record.status === 'normal' ? '#2ecc71' : '#7f8c8d',
                    color: 'white', borderRadius: '4px', fontSize: '12px'
                  }}>
                    {record.status === 'late' ? 'Trễ' :
                     record.status === 'early' ? 'Về sớm' :
                     record.status === 'working' ? 'Đang làm việc' :
                     record.status === 'normal' ? 'Đúng giờ' : 'Vắng'}
                  </span>
                </td>
                <td style={{ padding: '12px' }}>
                  {(record.status === 'late' || record.status === 'early') && (
                    <button
                      onClick={() => handleEdit(record.id)}
                      style={{
                        padding: '5px 10px',
                        backgroundColor: '#3498db',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                    >Chỉnh sửa</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <div style={{padding:10}}>Đang tải...</div>}
        {error && <div style={{padding:10,color:'red'}}>{error}</div>}
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
              <button onClick={confirmEdit} style={{ flex: 1, padding: '10px', backgroundColor: '#2ecc71', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Xác nhận</button>
              <button onClick={() => { setEditId(null); setPinValue(''); }} style={{ flex: 1, padding: '10px', backgroundColor: '#95a5a6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Hủy</button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}