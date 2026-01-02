import React from 'react';

export interface BarDatum { label: string; value: number }

export default function BarChart({ data, height = 160, color = '#3498db', title }: { data: BarDatum[]; height?: number; color?: string; title?: string }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, textAlign: 'center', color: '#999' }}>
        {title && <div style={{ marginBottom: 8, fontWeight: 600 }}>{title}</div>}
        <div style={{ height: height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Không có dữ liệu</div>
      </div>
    );
  }
  const max = Math.max(1, ...data.map(d => d.value));
  const barW = Math.max(12, Math.floor(600 / Math.max(1, data.length)) - 4);
  const minHeight = Math.max(4, (height || 160) * 0.1);
  return (
    <div style={{ background: '#fff', padding: 12, borderRadius: 8 }}>
      {title && <div style={{ marginBottom: 8, fontWeight: 600 }}>{title}</div>}
      <div style={{ display: 'flex', alignItems: 'end', gap: 6, height }}>
        {data.map((d, i) => (
          <div key={i} title={`${d.label}: ${d.value.toFixed(2)}`}
               style={{ width: barW, background: color, height: `${Math.max(minHeight, (d.value / max) * 100)}%`, minHeight: minHeight, borderRadius: 4 }} />
        ))}
      </div>
      <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
        {data.map((d, i) => (
          <div key={i} style={{ width: barW, fontSize: 10, textAlign: 'center', color: '#555' }}>{d.label}</div>
        ))}
      </div>
    </div>
  );
}
