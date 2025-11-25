import React from 'react';

export class ErrorBoundary extends React.Component<{children:React.ReactNode},{err:any}> {
  constructor(props:any){ super(props); this.state={err:null}; }
  static getDerivedStateFromError(err:any){ return {err}; }
  componentDidCatch(err:any,info:any){ console.error('Render error:',err,info); }
  render(){
    if(this.state.err){
      return <div style={{padding:24,fontFamily:'monospace'}}>
        <h2 style={{color:'#c0392b'}}>Lỗi giao diện</h2>
        <pre style={{whiteSpace:'pre-wrap'}}>{String(this.state.err)}</pre>
      </div>;
    }
    return this.props.children;
  }
}
