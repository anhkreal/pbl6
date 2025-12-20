import React from 'react';

export default function SkeletonTable({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  const r = Array.from({ length: rows });
  const c = Array.from({ length: cols });
  return (
    <table className="table">
      <thead>
        <tr>
          {c.map((_, i) => (<th key={i}><div style={{ height: 10, background: '#f0f2f5', borderRadius: 4 }} /></th>))}
        </tr>
      </thead>
      <tbody>
        {r.map((_, ri) => (
          <tr key={ri}>
            {c.map((_, ci) => (
              <td key={ci}>
                <div style={{ height: 14, background: '#f3f4f6', borderRadius: 4 }} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
