import React, { useState } from 'react';
import { useAuthStore } from '../state/authStore';
import { useUIStore } from '../state/uiStore';
import PinConfirmModal from './PinConfirmModal';
import { useNavigate, useLocation } from 'react-router-dom';

interface NavItem { label: string; path: string; roles: ('admin'|'staff')[] }
const NAV: NavItem[] = [
  { label:'Dashboard', path:'dashboard', roles:['admin','staff'] },
  { label:'EmotionLog', path:'emotions', roles:['admin','staff'] },
  { label:'Attendance', path:'attendance', roles:['admin','staff'] },
  { label:'KPI Report', path:'kpi', roles:['admin','staff'] },
  { label:'Employees', path:'employees', roles:['admin'] },
  { label:'Chi tiết nhân viên', path:'employeedetail', roles:['admin'] },
  { label:'Image Update', path:'image', roles:['staff'] },
  { label:'Contact', path:'contact', roles:['staff'] },
  { label:'Profile', path:'profile', roles:['admin','staff'] },
];

export default function LayoutShell({ children }: { children: React.ReactNode }){
  const { role, profile, logout } = useAuthStore();
  const nav = useNavigate();
  const loc = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const { openPin } = useUIStore();
  function go(p: string){ nav('/'+p); }
  return (
    <div style={{display:'flex', height:'100vh', fontFamily:'Arial'}}>
      <aside style={{width:220, background:'#222', color:'#eee', padding:12}}>
        <h3 style={{marginTop:0}}>Cafe App</h3>
        <nav>
          {NAV.filter(i=> role && i.roles.includes(role)).map(i=> {
            const active = loc.pathname.includes(i.path);
            return <div key={i.path} style={{padding:'6px 8px', background: active? '#444':'transparent', cursor:'pointer'}} onClick={()=>go(i.path)}>{i.label}</div>;
          })}
        </nav>
      </aside>
      <main style={{flex:1, position:'relative'}}>
        <header style={{display:'flex', justifyContent:'space-between', alignItems:'center', padding:'8px 16px', borderBottom:'1px solid #ddd'}}>
          <div></div>
          <div style={{position:'relative'}}>
            <button onClick={()=>setMenuOpen(o=>!o)}>{profile?.name || 'User'} ⋮</button>
            {menuOpen && <div style={{position:'absolute', right:0, top:'100%', background:'#fff', border:'1px solid #ccc', minWidth:160}}>
              <div style={{padding:8, cursor:'pointer'}} onClick={()=>{ go('profile'); setMenuOpen(false); }}>Thông tin cá nhân</div>
              <div style={{padding:8, cursor:'pointer'}} onClick={()=>{ logout(); }}>Đăng xuất</div>
            </div>}
          </div>
        </header>
        <div style={{padding:16, overflow:'auto', height:'calc(100% - 50px)'}}>
          {children}
        </div>
        <PinConfirmModal />
      </main>
    </div>
  );
}
