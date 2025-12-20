import { ReactNode, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import UserMenu from '../components/UserMenu';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const loc = useLocation();
  const [open, setOpen] = useState(false);
  const isActive = (p: string) => loc.pathname === p;
  const links: [string, string][] = [
    ['/admin/dashboard', '📊 Dashboard'],
    ['/admin/analysis', '📊 Phân tích'],
    ['/admin/emotions', '😊 EmotionLog'],
    ['/admin/attendance', '🗓 Check in/out'],
    ['/admin/kpi', '📈 KPI'],
    ['/admin/employees', '👥 Nhân viên']
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <header className="app-header">
        <div className="app-title">☕ Cafe Admin</div>
        <button className="btn btn-ghost mobile-only" aria-label="Mở menu" onClick={() => setOpen(true)}>
          ☰ Menu
        </button>
        <UserMenu />
      </header>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {open && <div className="backdrop mobile-only" onClick={() => setOpen(false)} />}
        <aside className={`sidebar ${open ? 'open' : ''}`}>
          {links.map(([p, l]) => (
            <Link key={p} to={p} className={`nav-link ${isActive(p) ? 'active' : ''}`} onClick={() => setOpen(false)}>{l}</Link>
          ))}
        </aside>
        <main className="content" style={{ flex: 1, overflowY: 'auto' }}>{children}</main>
      </div>
    </div>
  );
}

