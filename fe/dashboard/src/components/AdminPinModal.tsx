import { useState } from 'react';

interface AdminPinModalProps {
  title?: string;
  onConfirm: (pin: string) => void;
  onCancel: () => void;
  open: boolean;
}

export default function AdminPinModal({ title = 'Xác nhận mã PIN', onConfirm, onCancel, open }: AdminPinModalProps) {
  const [pin, setPin] = useState('');
  if (!open) return null;

  const submit = () => {
    const trimmed = String(pin ?? '').trim();
    console.debug('[AdminPinModal] user entered pin raw:', pin, 'trimmed:', trimmed);
    onConfirm(trimmed);
    setPin('');
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div style={{ background: '#fff', padding: 24, borderRadius: 8, minWidth: 300 }}>
        <h3 style={{ marginBottom: 16 }}>{title}</h3>
        <input
          type="password"
            placeholder="Nhập mã PIN (123456)"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            maxLength={6}
            style={{ width: '100%', padding: 10, border: '1px solid #ccc', borderRadius: 4, marginBottom: 16 }}
        />
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={submit} style={{ flex: 1, padding: 10, background: '#2ecc71', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
            Xác nhận
          </button>
          <button onClick={() => { setPin(''); onCancel(); }} style={{ flex: 1, padding: 10, background: '#95a5a6', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
            Hủy
          </button>
        </div>
      </div>
    </div>
  );
}
