import React, { useState } from 'react';
import { useUIStore } from '../state/uiStore';
import { verifyPin } from '../api/pin';

export default function PinConfirmModal(){
  const { showPinModal, pinAction, closePin } = useUIStore();
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  if(!showPinModal || !pinAction) return null;
  // Try automatic verification if adminPin is stored
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const stored = sessionStorage.getItem('adminPin');
        console.debug('[PinConfirmModal] auto-check stored adminPin raw:', stored);
        if (stored) {
          setLoading(true);
          const ok = await verifyPin(stored);
          if (ok && !cancelled) {
            pinAction.onConfirm();
            closePin();
          }
        }
      } catch (e) {
        // ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [showPinModal, pinAction, closePin]);
  async function submit(){
    setLoading(true); setError('');
    const trimmed = String(pin ?? '').trim();
    console.debug('[PinConfirmModal] user entered pin raw:', pin, 'trimmed:', trimmed);
    const ok = await verifyPin(trimmed);
    setLoading(false);
    if(!ok){ setError('PIN sai'); return; }
    pinAction.onConfirm();
    closePin();
  }
  return <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center'}}>
    <div style={{background:'#fff', padding:20, minWidth:300}}>
      <h4>Xác nhận: {pinAction.label}</h4>
      <input placeholder='PIN' value={pin} onChange={e=>setPin(e.target.value)} />
      {error && <div style={{color:'red'}}>{error}</div>}
      <div style={{marginTop:10}}>
        <button disabled={loading} onClick={submit}>Xác nhận</button>
        <button onClick={closePin} style={{marginLeft:8}}>Hủy</button>
      </div>
    </div>
  </div>;
}
