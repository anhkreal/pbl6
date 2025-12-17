import React from 'react';

export default function ErrorBanner({ message, details, onRetry }: { message: string; details?: string; onRetry?: ()=>void }){
  const [show, setShow] = React.useState(false);
  return (
    <div style={{ background:'#fdecea', border:'1px solid #f5c6cb', color:'#a94442', padding:12, borderRadius:8 }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div>{message || 'Đã xảy ra lỗi. Vui lòng thử lại.'}</div>
        <div style={{ display:'flex', gap:8 }}>
          {onRetry && <button onClick={onRetry} style={btn}>Thử lại</button>}
          {details && <button onClick={()=>setShow(s=>!s)} style={btnAlt}>{show ? 'Ẩn chi tiết' : 'Chi tiết'}</button>}
        </div>
      </div>
      {show && details && (
        <pre style={{ whiteSpace:'pre-wrap', marginTop:8, background:'#fff', color:'#333', padding:10, borderRadius:6, border:'1px solid #eee' }}>{details}</pre>
      )}
    </div>
  );
}

const btn: React.CSSProperties = { padding:'6px 10px', background:'#c0392b', color:'#fff', border:'none', borderRadius:6, cursor:'pointer' };
const btnAlt: React.CSSProperties = { padding:'6px 10px', background:'#ecf0f1', color:'#2c3e50', border:'1px solid #bdc3c7', borderRadius:6, cursor:'pointer' };
