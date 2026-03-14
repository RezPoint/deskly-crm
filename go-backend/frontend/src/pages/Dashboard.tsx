import React, { useEffect, useState } from 'react';
import { request } from '../api/client';
import { Users, ShoppingBag, DollarSign, Activity, Wallet } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({ clients: 0, orders: 0, total: 0, revenue: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await request('/dashboard/stats');
      if (data) setStats(data);
    } catch (error) { console.error(error); }
    finally { setLoading(false); }
  };

  if (loading) return <div style={{ padding: '2rem' }}>Загрузка...</div>;

  return (
    <div>
      <header className="header" style={{ padding: '0 0 2rem 0', border: 'none' }}>
        <div>
          <h1>Дашборд</h1>
          <p className="text-muted">Финансовые показатели и активность</p>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.2)', padding: '0.75rem', borderRadius: '10px', color: 'var(--primary)' }}><Users size={24} /></div>
          <div><p className="text-muted" style={{ fontSize: '0.8rem' }}>Клиенты</p><h2 style={{ fontSize: '1.5rem', margin: 0 }}>{stats.clients}</h2></div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(168, 85, 247, 0.2)', padding: '0.75rem', borderRadius: '10px', color: '#a855f7' }}><ShoppingBag size={24} /></div>
          <div><p className="text-muted" style={{ fontSize: '0.8rem' }}>Заказы</p><h2 style={{ fontSize: '1.5rem', margin: 0 }}>{stats.orders}</h2></div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.1)', padding: '0.75rem', borderRadius: '10px', color: 'white' }}><Wallet size={24} /></div>
          <div><p className="text-muted" style={{ fontSize: '0.8rem' }}>Оборот (заказы)</p><h2 style={{ fontSize: '1.5rem', margin: 0 }}>{stats.total.toLocaleString()} ₽</h2></div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <div style={{ background: 'rgba(16, 185, 129, 0.2)', padding: '0.75rem', borderRadius: '10px', color: 'var(--success)' }}><DollarSign size={24} /></div>
          <div><p className="text-muted" style={{ fontSize: '0.8rem' }}>Выручка (оплачено)</p><h2 style={{ fontSize: '1.5rem', margin: 0, color: 'var(--success)' }}>{stats.revenue.toLocaleString()} ₽</h2></div>
        </div>

      </div>

      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1.5rem' }}>
          <Activity size={24} color="var(--primary)" />
          <h3 style={{ margin: 0 }}>Состояние системы</h3>
        </div>
        <p className="text-muted">Все показатели рассчитываются автоматически на основе данных из SQLite.</p>
      </div>
    </div>
  );
};
