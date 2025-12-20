export function downloadCSV(filename: string, rows: Array<Record<string, any>>, headers?: Array<{ key: string; label: string }>) {
  const cols = headers?.map(h => h.key) || (rows[0] ? Object.keys(rows[0]) : []);
  const labels = headers?.map(h => h.label) || cols;
  const escape = (v: any) => {
    if (v == null) return '';
    const s = String(v);
    if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  };
  const lines: string[] = [];
  if (labels.length) lines.push(labels.map(escape).join(','));
  for (const row of rows) {
    lines.push(cols.map(c => escape(row[c])).join(','));
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
