import React, { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import AdminLayout from '../../layouts/AdminLayout';
import { apiFetch } from '../../api/http';

export default function EmployeeDetail() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const username = params.get('username') || '';
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    if (!username) return;
    let ignore = false;
    (async () => {
      setLoading(true); setError('');
      try {
        const res: any = await apiFetch(`/taikhoan/${encodeURIComponent(username)}`);
        if (!ignore) setUser(res?.user ?? res ?? null);
      } catch (e:any) {
        if (!ignore) setError(e.message || String(e));
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [username]);

  return (
    <AdminLayout>
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', marginBottom: 16 }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 28, margin: 0 }}>Chi tiết nhân viên</h1>
          <div style={{ marginTop: 10 }}>
            <Link to="/admin/employees" style={{ color: '#3498db' }}>← Quay lại danh sách</Link>
          </div>
        </div>
      </div>

      {loading && <div style={{ background: '#fff', padding: 24, borderRadius: 8 }}>Đang tải...</div>}
      {error && <div style={{ background: '#fff', padding: 24, borderRadius: 8, color: 'red' }}>{error}</div>}
      {!loading && !user && !error && <div style={{ background: '#fff', padding: 24, borderRadius: 8 }}>Không tìm thấy nhân viên.</div>}
      {user && (
        <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 20 }}>
          <div style={{ background: '#fff', padding: 20, borderRadius: 8, textAlign: 'center' }}>
            <div style={{ width: 120, height: 120, margin: '0 auto', borderRadius: '50%', background: '#ecf0f1', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36, color: '#7f8c8d' }}>
              {user.full_name ? user.full_name.split(' ').map((s:string)=>s[0]).slice(-2).join('') : (user.username || 'U').toUpperCase().slice(0,2)}
            </div>
            <h2 style={{ marginTop: 12, marginBottom: 4 }}>{user.full_name ?? user.fullName ?? user.username}</h2>
            <div style={{ color: '#95a5a6', marginBottom: 8 }}>{user.role}</div>
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 12, color: '#7f8c8d' }}>Mã PIN</div>
              <div style={{ fontWeight: 600 }}>{user.pin ? '••••••' : '—'}</div>
            </div>
          </div>

          <div style={{ background: '#fff', padding: 20, borderRadius: 8 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <Field label="ID" value={user.id} />
              <Field label="Username" value={user.username} />
              <Field label="Tuổi" value={user.age} />
              <Field label="SĐT" value={user.phone} />
              <Field label="Ca làm" value={user.shift === 'day' ? 'Sáng' : 'Tối'} />
              <Field label="Vai trò" value={user.role} />
              <div style={{ gridColumn: '1 / -1' }}><Field label="Địa chỉ" value={user.address} /></div>
              <div style={{ gridColumn: '1 / -1' }}><Field label="Trạng thái" value={user.status === 'working' ? 'Đang làm' : 'Nghỉ'} /></div>
              <div style={{ gridColumn: '1 / -1', color:'#95a5a6', fontSize:13, marginTop:6 }}>Tạo: {user.created_at ?? ''} — Cập nhật: {user.updated_at ?? ''}</div>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}

function Field({ label, value }: { label: string; value: any }) {
  return (
    <div style={{ display: 'flex', gap: 12 }}>
      <div style={{ width: 140, fontWeight: 600, color: '#2c3e50' }}>{label}</div>
      <div style={{ flex: 1, color: '#34495e' }}>{String(value ?? '')}</div>
    </div>
  );
}