import { Link, useLocation } from 'react-router-dom';
import UserMenu from '../components/UserMenu';

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const active = (p: string) => loc.pathname === p;
  const links: [string, string][] = [
    ['/staff/dashboard', '📊 Dashboard'],
    ['/staff/analysis', '📊 Phân tích'],
    ['/staff/emotions', '😊 EmotionLog'],
    ['/staff/attendance', '🗓 Check in/out'],
    ['/staff/kpi', '📈 KPI Report'],
    ['/staff/image-update', '🖼 Cập nhật ảnh'],
    ['/staff/contact', '☎ Liên hệ']
  ];
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header className="app-header">
        <div className="app-title">☕ Cafe Staff</div>
        <UserMenu />
      </header>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <aside className="sidebar">
          {links.map(([p, l]) => (
            <Link key={p} to={p} className={`nav-link ${active(p) ? 'active' : ''}`}>{l}</Link>
          ))}
        </aside>
        <main className="content" style={{ flex: 1, overflowY: 'auto' }}>{children}</main>
      </div>
    </div>
  );
}
