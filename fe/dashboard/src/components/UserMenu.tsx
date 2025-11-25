import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function UserMenu() {
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const name = sessionStorage.getItem('userName') || 'User';
  const role = sessionStorage.getItem('userRole') || 'staff';
  const goProfile = () => { nav(role === 'admin' ? '/admin/profile' : '/staff/profile'); setOpen(false); };
  const logout = () => { sessionStorage.clear(); nav('/'); };

  return (
    <div style={{ position:'relative' }}>
      <button onClick={()=>setOpen(o=>!o)} style={btn}>{name}<span style={{fontSize:18}}>⋮</span></button>
      {open && (
        <div style={popup}>
          <button style={item} onClick={goProfile}>Thông tin cá nhân</button>
          <button style={item} onClick={logout}>Đăng xuất</button>
        </div>
      )}
    </div>
  );
}
const btn:React.CSSProperties={background:'transparent',border:'none',color:'#fff',cursor:'pointer',display:'flex',alignItems:'center',gap:6,fontSize:14};
const popup:React.CSSProperties={position:'absolute',right:0,top:'110%',background:'#fff',borderRadius:6,boxShadow:'0 4px 12px rgba(0,0,0,.15)',minWidth:170,zIndex:50,overflow:'hidden'};
const item:React.CSSProperties={width:'100%',textAlign:'left',padding:'10px 14px',border:'none',background:'transparent',cursor:'pointer',fontSize:14};
