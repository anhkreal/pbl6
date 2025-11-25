import { useState } from 'react';
import AdminLayout from '../../layouts/AdminLayout';

export default function ChangePinPage() {
  const [oldPin, setOldPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [message, setMessage] = useState('');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    if (oldPin !== '123456') return setMessage('Mã PIN cũ không đúng');
    if (newPin.length !== 6) return setMessage('Mã PIN mới phải 6 số');
    if (newPin !== confirmPin) return setMessage('Xác nhận không khớp');
    setMessage('Đổi mã PIN thành công (mock)');
    setOldPin(''); setNewPin(''); setConfirmPin('');
  };

  return (
    <AdminLayout>
      <h1 style={{ fontSize: 28, marginBottom: 20 }}>Thay đổi mã PIN</h1>
      <form onSubmit={submit} style={{
        background: '#fff', padding: 24, borderRadius: 8, maxWidth: 400,
        display: 'flex', flexDirection: 'column', gap: 14
      }}>
        <input
          type="password"
          placeholder="Mã PIN cũ"
          value={oldPin}
          onChange={e => setOldPin(e.target.value)}
          maxLength={6}
          style={input}
          required
        />
        <input
          type="password"
          placeholder="Mã PIN mới"
          value={newPin}
          onChange={e => setNewPin(e.target.value)}
          maxLength={6}
          style={input}
          required
        />
        <input
          type="password"
          placeholder="Xác nhận mã PIN mới"
          value={confirmPin}
          onChange={e => setConfirmPin(e.target.value)}
          maxLength={6}
          style={input}
          required
        />
        {message && <div style={{ color: message.includes('thành công') ? '#16a085' : '#e74c3c', fontSize: 14 }}>{message}</div>}
        <button type="submit" style={btn}>Lưu thay đổi</button>
      </form>
    </AdminLayout>
  );
}

const input: React.CSSProperties = { padding: 10, border: '1px solid #ccc', borderRadius: 4 };
const btn: React.CSSProperties = {
  padding: 12, background: '#3498db', color: '#fff', border: 'none',
  borderRadius: 4, cursor: 'pointer', fontSize: 16
};
