import React from 'react';

export class ErrorBoundary extends React.Component<{children:React.ReactNode},{err:any,showDetails:boolean}> {
  constructor(props:any){ super(props); this.state={err:null, showDetails:false}; }
  static getDerivedStateFromError(err:any){ return {err, showDetails:false}; }
  componentDidCatch(err:any,info:any){ console.error('Render error:',err,info); }
  handleReload = () => { window.location.reload(); };
  toggleDetails = () => this.setState(s=>({ ...s, showDetails: !s.showDetails }));
  render(){
    if(this.state.err){
      const msg = 'Đã xảy ra lỗi không mong muốn. Vui lòng thử tải lại trang hoặc liên hệ hỗ trợ nếu lỗi tiếp diễn.';
      return <div style={{padding:24, fontFamily:'Arial, sans-serif'}}>
        <div style={{background:'#fdecea', border:'1px solid #f5c6cb', color:'#a94442', padding:16, borderRadius:8}}>
          <h2 style={{margin:'0 0 8px 0'}}>Lỗi giao diện</h2>
          <div style={{marginBottom:12}}>{msg}</div>
          <div style={{display:'flex', gap:8}}>
            <button onClick={this.handleReload} style={btnStyle}>Tải lại trang</button>
            <button onClick={this.toggleDetails} style={btnAltStyle}>{this.state.showDetails ? 'Ẩn chi tiết' : 'Xem chi tiết (kỹ thuật)'}</button>
          </div>
          {this.state.showDetails && (
            <pre style={{whiteSpace:'pre-wrap', marginTop:12, background:'#fff', padding:12, borderRadius:6, border:'1px solid #eee'}}>{String(this.state.err?.stack || this.state.err)}</pre>
          )}
        </div>
      </div>;
    }
    return this.props.children;
  }
}

const btnStyle: React.CSSProperties = { padding:'8px 12px', background:'#c0392b', color:'#fff', border:'none', borderRadius:6, cursor:'pointer' };
const btnAltStyle: React.CSSProperties = { padding:'8px 12px', background:'#ecf0f1', color:'#2c3e50', border:'1px solid #bdc3c7', borderRadius:6, cursor:'pointer' };
