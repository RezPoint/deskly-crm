import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { KeyRound } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      // Имитация входа. Для реального Go-бекенда тут будет вызов POST /auth/login
      // const res = await request('/auth/login', {
      //   method: 'POST',
      //   body: JSON.stringify({ email, password })
      // });
      
      // Пока просто сохраняем фейковый токен и пускаем внутрь
      localStorage.setItem('token', 'fake-jwt-token');
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="glass-panel login-card">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <KeyRound size={48} color="var(--primary)" style={{ marginBottom: '1rem' }} />
          <h2>Вход в DesklyCRM</h2>
          <p className="text-muted">Управляйте бизнесом в пару кликов</p>
        </div>

        {error && <div style={{ color: 'var(--danger)', marginBottom: '1rem', textAlign: 'center' }}>{error}</div>}

        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label>Email</label>
            <input 
              type="email" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              placeholder="admin@deskly.com"
              required 
            />
          </div>
          <div className="input-group">
            <label>Пароль</label>
            <input 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              placeholder="••••••••"
              required 
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            Войти в систему
          </button>
        </form>
      </div>
    </div>
  );
};
