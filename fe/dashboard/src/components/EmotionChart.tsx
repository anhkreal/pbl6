interface Dist { angry: number; sad: number; fear: number; disgust: number; }
const colors: Record<keyof Dist, string> = {
  angry: '#e74c3c',
  sad: '#3498db',
  fear: '#9b59b6',
  disgust: '#2ecc71'
};

export default function EmotionChart({ dist }: { dist: Dist }) {
  const total = Object.values(dist).reduce((a, b) => a + b, 0) || 1;
  let acc = 0;
  const slices = Object.entries(dist).map(([k, v]) => {
    const start = acc / total * 2 * Math.PI;
    acc += v;
    const end = acc / total * 2 * Math.PI;
    const large = end - start > Math.PI ? 1 : 0;
    const r = 50, cx = 55, cy = 55;
    const x1 = cx + r * Math.sin(start), y1 = cy - r * Math.cos(start);
    const x2 = cx + r * Math.sin(end), y2 = cy - r * Math.cos(end);
    return (
      <path key={k}
        d={`M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${large} 1 ${x2},${y2} Z`}
        fill={colors[k as keyof Dist]} />
    );
  });
  return (
    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
      <svg width={110} height={110}>{slices}</svg>
      <div style={{ display: 'grid', gap: 6 }}>
        {Object.keys(dist).map(k => (
          <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <span style={{ width: 14, height: 14, borderRadius: 3, background: colors[k as keyof Dist] }} />
            <span style={{ fontWeight: 500 }}>{k}</span>
            <span style={{ color: '#555' }}>{((dist[k as keyof Dist] / total) * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
