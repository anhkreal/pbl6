import React, { useEffect, useState } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import { apiFetch } from '../../api/http';

export default function Contact() {
  const [admins, setAdmins] = useState<Array<{ name: string; address?: string; phone?: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let ignore = false;
    (async () => {
      setLoading(true); setError('');
      try {
        const res:any = await apiFetch('/users');
        const arr = Array.isArray(res?.users) ? res.users : (Array.isArray(res) ? res : []);
        const admins = arr.filter((u:any) => (u.role || '').toLowerCase() === 'admin').map((u:any) => ({ name: u.full_name ?? u.name ?? u.username ?? '', address: u.address, phone: u.phone }));
        if (!ignore) setAdmins(admins);
      } catch (e:any) {
        if (!ignore) setError(e.message || 'Không thể tải danh sách admin');
      } finally { if (!ignore) setLoading(false); }
    })();
    return () => { ignore = true; }
  }, []);

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 16 }}>Liên hệ</h1>
      <div style={{ background: '#fff', padding: 20, borderRadius: 10, maxWidth: 640 }}>
        {loading && <div>Đang tải...</div>}
        {error && <div style={{ color: 'red' }}>{error}</div>}
        {!loading && !error && admins.length === 0 && <div>Không tìm thấy admin</div>}
        {!loading && !error && admins.map((a, i) => (
          <div key={i} style={{ marginBottom: 12, padding: 12, borderRadius: 6, background: '#f9f9f9' }}>
            <Row label="Tên" value={a.name} />
            <Row label="Địa chỉ" value={a.address || '--'} />
            <Row label="SĐT" value={a.phone || '--'} />
          </div>
        ))}
      </div>
    </StaffLayout>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', gap: 10, fontSize: 14 }}>
      <strong style={{ width: 90 }}>{label}:</strong>
      <span>{value}</span>
    </div>
  );
}