import React, { useState, useEffect } from 'react';
import StaffLayout from '../../layouts/StaffLayout';
import { updateProfile, changePassword } from '../../api/user';
import { fetchEmployees } from '../../api/employees';

export default function StaffProfile() {
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [address, setAddress] = useState('');
  const [phone, setPhone] = useState('');
  const [userId, setUserId] = useState<number | null>(null);

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

  const [profileMsg, setProfileMsg] = useState('');

  const saveInfo = async () => {
    setProfileMsg('');
    try {
      const id = userId || Number(sessionStorage.getItem('userId')) || undefined;
      if (!id) throw new Error('Không xác định user id');
      const payload: any = { id };
      if (name) payload.full_name = name;
      if (age) payload.age = Number(age);
      if (address) payload.address = address;
      if (phone) payload.phone = phone;
      const res = await updateProfile(payload);
      const msg = res && typeof res === 'object' && (res as any).message ? (res as any).message : 'Cập nhật thông tin thành công';
      setProfileMsg(msg);
    } catch (e:any) {
      setProfileMsg(e?.message || 'Cập nhật thất bại');
    }
  };

  const changePwd = async () => {
    setPasswordMsg('');
    if (!oldPassword || !newPassword || !confirmPassword) { setPasswordMsg('Vui lòng nhập đủ trường'); return; }
    if (newPassword !== confirmPassword) { setPasswordMsg('Mật khẩu xác nhận không khớp'); return; }
    try {
      const res:any = await changePassword(oldPassword, newPassword);
      const msg = res && (res.message || res.detail) ? (res.message || res.detail) : 'Đổi mật khẩu thành công';
      setPasswordMsg(msg);
      setOldPassword(''); setNewPassword(''); setConfirmPassword('');
    } catch (e:any) {
      setPasswordMsg(e?.message || 'Đổi mật khẩu thất bại');
    }
  };

  // PIN change not available for staff

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 18 }}>Thông tin cá nhân</h1>
      <div style={{ display: 'grid', gap: 20, gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))' }}>
        <Section title="Cập nhật thông tin">
          <input placeholder="Tên" value={name} onChange={e => setName(e.target.value)} style={inp} />
          <input placeholder="Tuổi" value={age} onChange={e => setAge(e.target.value)} style={inp} />
          <input placeholder="Nơi ở" value={address} onChange={e => setAddress(e.target.value)} style={inp} />
          <input placeholder="SĐT" value={phone} onChange={e => setPhone(e.target.value)} style={inp} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={saveInfo} style={btn}>Lưu</button>
            <div style={{ alignSelf: 'center', color: profileMsg.includes('thành công') ? 'green' : 'red' }}>{profileMsg}</div>
          </div>
        </Section>

        <Section title="Đổi mật khẩu">
          <input type="password" placeholder="Mật khẩu cũ" value={oldPassword} onChange={e => setOldPassword(e.target.value)} style={inp} />
          <input type="password" placeholder="Mật khẩu mới" value={newPassword} onChange={e => setNewPassword(e.target.value)} style={inp} />
          <input type="password" placeholder="Xác nhận mật khẩu" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} style={inp} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={changePwd} style={btn}>Đổi mật khẩu</button>
            <div style={{ alignSelf: 'center', color: passwordMsg.includes('thành công') ? 'green' : 'red' }}>{passwordMsg}</div>
          </div>
        </Section>

        {/* PIN change not available for staff */}
      </div>
    </StaffLayout>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: '#fff', padding: 16, borderRadius: 10,
      display: 'flex', flexDirection: 'column', gap: 12
    }}>
      <h3 style={{ margin: 0 }}>{title}</h3>
      {children}
    </div>
  );
}

const inp: React.CSSProperties = { padding: 10, border: '1px solid #ccc', borderRadius: 6 };
const btn: React.CSSProperties = {
  padding: 12, background: '#3498db', color: '#fff', border: 'none',
  borderRadius: 6, cursor: 'pointer', fontSize: 14
};