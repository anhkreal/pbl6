import { Link, useLocation } from 'react-router-dom';
import UserMenu from '../components/UserMenu';

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const active = (p: string) => loc.pathname === p;
  const links: [string, string][] = [
    ['/staff/dashboard', '📊 Dashboard'],
    ['/staff/emotions', '😊 EmotionLog'],
    ['/staff/attendance', '🗓 Check in/out'],
    ['/staff/kpi', '📈 KPI Report'],
    ['/staff/image-update', '🖼 Cập nhật ảnh'],
    ['/staff/contact', '☎ Liên hệ']
  ];
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#eef2f3' }}>
      <header style={{
        height: 58, background: '#0f6b5b', color: '#fff',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '0 24px', borderBottom: '1px solid #0d5a4c'
      }}>
        <div style={{ fontSize: 18, fontWeight: 600 }}>☕ Cafe Staff</div>
        <UserMenu />
      </header>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <aside style={{
          width: 230, background: '#13816f', color: '#fff',
          padding: '18px 14px', display: 'flex', flexDirection: 'column', gap: 6
        }}>
          {links.map(([p, l]) => (
            <Link key={p} to={p} style={{
              textDecoration: 'none',
              padding: '10px 12px',
              borderRadius: 6,
              fontSize: 14,
              color: '#fff',
              background: active(p) ? 'rgba(255,255,255,.22)' : 'transparent'
            }}>{l}</Link>
          ))}
        </aside>
        <main style={{ flex: 1, padding: 28, overflowY: 'auto' }}>{children}</main>
      </div>
    </div>
  );
}
