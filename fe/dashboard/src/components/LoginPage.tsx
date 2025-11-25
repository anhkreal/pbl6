import React, { useState } from 'react';
import { useAuthStore } from '../state/authStore';
import { login as apiLogin } from '../api/auth';

export default function LoginPage(){
  const login = useAuthStore(s => s.login);
  const [username, setU] = useState('');
  const [password, setP] = useState('');
  const [error, setError] = useState('');

  async function onSubmit(e: React.FormEvent){
    e.preventDefault();
    if (!username || !password) { setError('Thiếu thông tin'); return; }
    try {
      const res = await apiLogin(username, password);
      if (!res || !res.token) throw new Error('No token');
      login(res.token, (res.role === 'admin' ? 'admin' : 'staff'));
    } catch (err){
      setError('Đăng nhập thất bại');
    }
  }

  return <div style={{maxWidth:360, margin:'80px auto', padding:20, border:'1px solid #ccc'}}>
    <h3>Đăng nhập</h3>
    <form onSubmit={onSubmit}>
      <div><input placeholder='Username' value={username} onChange={e=>setU(e.target.value)} /></div>
      <div><input type='password' placeholder='Password' value={password} onChange={e=>setP(e.target.value)} /></div>
      {error && <div style={{color:'red'}}>{error}</div>}
      <button type='submit'>Login</button>
    </form>
  </div>;
}
