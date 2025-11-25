import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import UserMenu from '../components/UserMenu';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const loc = useLocation();
  const isActive = (p: string) => loc.pathname === p;
  const links: [string, string][] = [
    ['/admin/dashboard', '📊 Dashboard'],
    ['/admin/emotions', '😊 EmotionLog'],
    ['/admin/attendance', '🗓 Check in/out'],
    ['/admin/kpi', '📈 KPI'],
    ['/admin/employees', '👥 Nhân viên']
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <header style={top}>
        <div style={{ fontSize: 18, fontWeight: 600 }}>☕ Cafe Admin</div>
        <UserMenu />
      </header>
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <aside style={aside}>
          {links.map(([p, l]) => (
            <Link
              key={p}
              to={p}
              style={{
                padding: '10px 12px',
                borderRadius: 6,
                fontSize: 14,
                color: '#fff',
                background: isActive(p) ? '#2f4858' : 'transparent'
              }}
            >
              {l}
            </Link>
          ))}
        </aside>
        <main style={{ flex: 1, padding: 28, overflowY: 'auto' }}>{children}</main>
      </div>
    </div>
  );
}

const top: React.CSSProperties = {
  height: 58,
  background: '#1f2d3a',
  color: '#fff',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0 24px',
  borderBottom: '1px solid #16232d'
};
const aside: React.CSSProperties = {
  width: 230,
  background: '#223240',
  color: '#fff',
  padding: '18px 14px',
  display: 'flex',
  flexDirection: 'column',
  gap: 6
};
