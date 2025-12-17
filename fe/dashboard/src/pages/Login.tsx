import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { login as apiLogin } from '../api/auth';
import { useAuthStore } from '../state/authStore';
import ErrorBanner from '../components/ErrorBanner';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const authLogin = useAuthStore(s => s.login);
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await apiLogin(username, password);
      if (!res || !res.token) throw new Error(res?.message || 'Đăng nhập thất bại');
      const role = (res.role === 'admin' ? 'admin' : 'staff');
      authLogin(res.token, role);
      // navigate based on role
      if (role === 'admin') navigate('/admin/dashboard');
      else navigate('/staff/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Đăng nhập thất bại');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 420, margin: '10vh auto', padding: 0 }}>
      <div className="card" style={{ overflow: 'hidden' }}>
        <div className="card-body">
          <h2 style={{ textAlign: 'center', marginBottom: 16 }}>Đăng nhập</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="text"
            placeholder="Tên đăng nhập"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={inputStyle}
            disabled={loading}
            required
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="password"
            placeholder="Mật khẩu"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={inputStyle}
            disabled={loading}
            required
          />
        </div>
        {error && (
          <div style={{ marginBottom: '15px' }}>
            <ErrorBanner message={error} onRetry={() => setError('')} />
          </div>
        )}
        <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
          {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>
      </form>
        </div>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px',
  border: '1px solid #ccc',
  borderRadius: '4px',
  boxSizing: 'border-box'
};
