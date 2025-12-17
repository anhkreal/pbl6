import React from 'react';

export interface BarDatum { label: string; value: number }

export default function BarChart({ data, height = 160, color = '#3498db', title }: { data: BarDatum[]; height?: number; color?: string; title?: string }) {
  const max = Math.max(1, ...data.map(d => d.value));
  const barW = Math.max(12, Math.floor(600 / Math.max(1, data.length)) - 4);
  return (
    <div style={{ background: '#fff', padding: 12, borderRadius: 8 }}>
      {title && <div style={{ marginBottom: 8, fontWeight: 600 }}>{title}</div>}
      <div style={{ display: 'flex', alignItems: 'end', gap: 6, height }}>
        {data.map((d, i) => (
          <div key={i} title={`${d.label}: ${d.value.toFixed(2)}`}
               style={{ width: barW, background: color, height: `${(d.value / max) * 100}%`, borderRadius: 4 }} />
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
