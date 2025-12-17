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
      <h1 style={{ marginBottom: 20 }}>Thay đổi mã PIN</h1>
      <form onSubmit={submit} className="card" style={{ maxWidth: 400 }}>
        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <input
          type="password"
          placeholder="Mã PIN cũ"
          value={oldPin}
          onChange={e => setOldPin(e.target.value)}
          maxLength={6}
          required
        />
        <input
          type="password"
          placeholder="Mã PIN mới"
          value={newPin}
          onChange={e => setNewPin(e.target.value)}
          maxLength={6}
          required
        />
        <input
          type="password"
          placeholder="Xác nhận mã PIN mới"
          value={confirmPin}
          onChange={e => setConfirmPin(e.target.value)}
          maxLength={6}
          required
        />
        {message && <div style={{ color: message.includes('thành công') ? '#16a085' : '#e74c3c', fontSize: 14 }}>{message}</div>}
        <button type="submit" className="btn btn-primary">Lưu thay đổi</button>
        </div>
      </form>
    </AdminLayout>
  );
}

