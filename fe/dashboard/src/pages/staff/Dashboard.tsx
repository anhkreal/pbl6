import React from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import EmotionChart from '../../components/EmotionChart';

export default function StaffDashboard() {
  // mock data
  const checkIn = '08:05';
  const hoursSoFar = 3.5;
  const kpiToday = 0.83;
  const dist = { angry: 1, sad: 2, fear: 0, disgust: 0 };

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 20 }}>Dashboard cá nhân</h1>
      <div style={{
        display: 'grid',
        gap: 20,
        gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))',
        marginBottom: 28
      }}>
        <Card label="Giờ check-in" value={checkIn} color="#3498db" />
        <Card label="Giờ làm đến hiện tại" value={hoursSoFar.toFixed(1) + 'h'} color="#16a085" />
        <Card label="KPI hôm nay" value={(kpiToday * 100).toFixed(1) + '%'} color="#9b59b6" />
      </div>
      <div style={{ background: '#fff', padding: 20, borderRadius: 10 }}>
        <h3 style={{ marginBottom: 14 }}>Biểu đồ cảm xúc tiêu cực hôm nay</h3>
        <EmotionChart dist={dist} />
      </div>
    </StaffLayout>
  );
}

function Card({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{
      background: '#fff',
      padding: 16,
      borderRadius: 10,
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      boxShadow: '0 1px 3px rgba(0,0,0,.08)'
    }}>
      <span style={{ fontSize: 12, textTransform: 'uppercase', color: '#7f8c8d', letterSpacing: '.5px' }}>{label}</span>
      <span style={{ fontSize: 28, fontWeight: 600, color }}>{value}</span>
    </div>
  );
}