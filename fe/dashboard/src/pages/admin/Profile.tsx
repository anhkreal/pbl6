import React, { useState, useEffect } from 'react';
import AdminLayout from '../../layouts/AdminLayout';
import { changePassword, changePin } from '../../api/user';
import { fetchEmployees } from '../../api/employees';

export default function AdminProfile() {
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [address, setAddress] = useState('');
  const [phone, setPhone] = useState('');
  const [userId, setUserId] = useState<number | null>(null);
  const [profileMsg, setProfileMsg] = useState('');

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const storedId = sessionStorage.getItem('userId');
        const storedName = sessionStorage.getItem('userName');
        let userData: any = null;
        if (storedId) {
          const data = await fetchEmployees(Number(storedId));
          userData = data && data.length ? data[0] : null;
        } else if (storedName) {
          const list = await fetchEmployees();
          userData = list.find((u: any) => u.username === storedName || u.fullName === storedName) || null;
        }
        if (userData && !ignore) {
          setName(userData.fullName || '');
          setAge(userData.age ? String(userData.age) : '');
          setAddress(userData.address || '');
          setPhone(userData.phone || '');
          setUserId(userData.id ?? null);
        }
      } catch (e) {
        // ignore
      }
    })();
    return () => { ignore = true; };
  }, []);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState('');

  const [oldPin, setOldPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [pinMsg, setPinMsg] = useState('');

  const submitProfile = async () => {
    setProfileMsg('');
    try {
      const id = userId || Number(sessionStorage.getItem('userId')) || undefined;
      if (!id) throw new Error('Không xác định được user id');

      // Build JSON payload with only allowed fields when present
      // send only the allowed fields in the top-level JSON body (backend accepts fields via path)
      const data: any = {};
      if (name) data.full_name = name;
      if (age) data.age = Number(age);
      if (address) data.address = address;
      if (phone) data.phone = phone;
      // Optional fields default to undefined; not included unless set in UI

      const token = sessionStorage.getItem('authToken');
      const url = (await import('../../api/base')).buildUrl(`/edit-users/${id}`);
      // debug: log payload
      console.debug('[Profile] PUT payload', data);

      const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(data)
      });

      // try to parse response body (JSON or text) for debugging
      let parsedBody: any = null;
      const ct = (res.headers.get('content-type') || '').toLowerCase();
      try {
        if (ct.includes('application/json')) {
          parsedBody = await res.json();
        } else {
          parsedBody = await res.text();
        }
      } catch (parseErr: any) {
        parsedBody = `<<parse error: ${String(parseErr?.message || parseErr)}>>`;
      }

      if (!res.ok) {
        console.error('[Profile] update failed', res.status, parsedBody);
        const msg = (parsedBody && (parsedBody.message || parsedBody.detail)) || String(parsedBody) || `HTTP ${res.status}`;
        throw new Error(msg);
      }

      console.debug('[Profile] update success', parsedBody);
      setProfileMsg((parsedBody && (parsedBody.message || parsedBody.detail)) || 'Cập nhật thông tin thành công');
    } catch (e: any) {
      setProfileMsg(e?.message || 'Cập nhật thất bại');
    }
  };

  const submitPassword = async () => {
    setPasswordMsg('');
    if (!oldPassword || !newPassword || !confirmPassword) { setPasswordMsg('Vui lòng nhập đủ trường'); return; }
    if (newPassword !== confirmPassword) { setPasswordMsg('Mật khẩu xác nhận không khớp'); return; }
    try {
      const res: any = await changePassword(oldPassword, newPassword);
      const msg = res && (res.message || res.detail) ? (res.message || res.detail) : 'Đổi mật khẩu thành công';
      setPasswordMsg(msg);
      setOldPassword(''); setNewPassword(''); setConfirmPassword('');
    } catch (e: any) {
      setPasswordMsg(e?.message || 'Đổi mật khẩu thất bại');
    }
  };

  const submitPin = async () => {
    setPinMsg('');
    if (!oldPin || !newPin || !confirmPin) { setPinMsg('Vui lòng nhập đủ trường'); return; }
    if (newPin !== confirmPin) { setPinMsg('PIN xác nhận không khớp'); return; }
    try {
      const res: any = await changePin(oldPin, newPin);
      const msg = res && (res.message || res.detail) ? (res.message || res.detail) : 'Đổi mã PIN thành công';
      setPinMsg(msg);
      setOldPin(''); setNewPin(''); setConfirmPin('');
    } catch (e: any) {
      setPinMsg(e?.message || 'Đổi PIN thất bại');
    }
  };

  return (
    <AdminLayout>
      <h1 style={{ marginBottom: 16 }}>Thông tin cá nhân</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
        <section style={{ background: '#fff', padding: 16, borderRadius: 8 }}>
          <h3>Thông tin cá nhân</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <input placeholder="Tên" value={name} onChange={e => setName(e.target.value)} style={inp} />
            <input placeholder="Tuổi" value={age} onChange={e => setAge(e.target.value)} style={inp} />
            <input placeholder="Nơi ở" value={address} onChange={e => setAddress(e.target.value)} style={inp} />
            <input placeholder="SĐT" value={phone} onChange={e => setPhone(e.target.value)} style={inp} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={submitProfile} style={btnPrimary}>Cập nhật</button>
              <div style={{ alignSelf: 'center', color: profileMsg.includes('thành công') ? 'green' : 'red' }}>{profileMsg}</div>
            </div>
          </div>
        </section>

        <section style={{ background: '#fff', padding: 16, borderRadius: 8 }}>
          <h3>Đổi mật khẩu</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <input type="password" placeholder="Mật khẩu cũ" value={oldPassword} onChange={e => setOldPassword(e.target.value)} style={inp} />
            <input type="password" placeholder="Mật khẩu mới" value={newPassword} onChange={e => setNewPassword(e.target.value)} style={inp} />
            <input type="password" placeholder="Xác nhận mật khẩu" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} style={inp} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={submitPassword} style={btnPrimary}>Đổi mật khẩu</button>
              <div style={{ alignSelf: 'center', color: passwordMsg.includes('thành công') ? 'green' : 'red' }}>{passwordMsg}</div>
            </div>
          </div>
        </section>

        <section style={{ background: '#fff', padding: 16, borderRadius: 8 }}>
          <h3>Đổi mã PIN</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <input type="password" placeholder="PIN cũ" value={oldPin} onChange={e => setOldPin(e.target.value)} style={inp} />
            <input type="password" placeholder="PIN mới" value={newPin} onChange={e => setNewPin(e.target.value)} style={inp} />
            <input type="password" placeholder="Xác nhận PIN" value={confirmPin} onChange={e => setConfirmPin(e.target.value)} style={inp} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={submitPin} style={btnPrimary}>Đổi PIN</button>
              <div style={{ alignSelf: 'center', color: pinMsg.includes('thành công') ? 'green' : 'red' }}>{pinMsg}</div>
            </div>
          </div>
        </section>
      </div>

    </AdminLayout>
  );
}

const inp: React.CSSProperties = { padding: 8, border: '1px solid #ccc', borderRadius: 4 };
const btnPrimary: React.CSSProperties = { padding: '8px 12px', background: '#3498db', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' };