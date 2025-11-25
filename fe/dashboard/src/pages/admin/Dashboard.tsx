import React from 'react';
import AdminLayout from '../../layouts/AdminLayout';

export default function AdminDashboard() {
  const stats = [
    { label: 'Đã check-in', value: 9, color: '#2ecc71' },
    { label: 'Trong ca', value: 12, color: '#3498db' },
    { label: 'Đi muộn', value: 3, color: '#e74c3c' },
    { label: 'Tích cực', value: '67%', color: '#9b59b6' }
  ];
  return (
    <AdminLayout>
      <h1 style={{ marginBottom: 20 }}>Dashboard</h1>
      <div style={{ display: 'grid', gap: 18, gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))' }}>
        {stats.map(s => (
          <div key={s.label} style={{ background: '#fff', padding: 16, borderRadius: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d' }}>{s.label}</span>
            <span style={{ fontSize: 26, fontWeight: 600, color: s.color }}>{s.value}</span>
          </div>
        ))}
      </div>
    </AdminLayout>
  );
}