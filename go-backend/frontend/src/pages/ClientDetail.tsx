import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Phone, MessageSquare, StickyNote, ShoppingBag, Wallet, AlertCircle } from 'lucide-react';
import { useClientDetail } from '../hooks/useClientDetail';
import { STATUS_MAP } from './Orders';

export const ClientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { client, orders, loading, error } = useClientDetail(Number(id));

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Загрузка...</div>;
  if (error || !client) return <div style={{ padding: '2rem', color: 'var(--danger)' }}>{error || 'Клиент не найден'}</div>;

  const totalAmount = orders.reduce((s, o) => s + Number(o.price), 0);
  const totalPaid = orders.reduce((s, o) => s + Number(o.paid_amount), 0);
  const totalDebt = totalAmount - totalPaid;

  return (
    <div>
      <button onClick={() => navigate('/clients')} className="btn" style={{ marginBottom: '1.5rem' }}>
        <ArrowLeft size={16} /> Назад к клиентам
      </button>

      <header style={{ marginBottom: '2rem' }}>
        <h1>{client.name}</h1>
        <p className="text-muted">Профиль клиента</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1fr) 2fr', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Контакты */}
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.25rem' }}>Контакты</h3>
          {client.phone ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              <Phone size={15} /> {client.phone}
            </div>
          ) : null}
          {client.telegram ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              <MessageSquare size={15} /> {client.telegram}
            </div>
          ) : null}
          {!client.phone && !client.telegram && (
            <p style={{ color: 'var(--text-subtle)', fontSize: '0.875rem', margin: 0 }}>Контакты не указаны</p>
          )}
          {client.notes && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: '0.875rem', fontSize: '0.875rem' }}>
              <StickyNote size={15} style={{ marginTop: 2, flexShrink: 0 }} />
              <span>{client.notes}</span>
            </div>
          )}
        </div>

        {/* Статистика */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          {[
            { label: 'Заказов', value: orders.length, icon: <ShoppingBag size={18} />, color: '#a78bfa' },
            { label: 'Оборот', value: `${totalAmount.toLocaleString()} ₽`, icon: <Wallet size={18} />, color: '#8b949e' },
            { label: 'Долг', value: `${Math.max(0, totalDebt).toLocaleString()} ₽`, icon: <AlertCircle size={18} />, color: totalDebt > 0 ? '#d29922' : 'var(--success)' },
          ].map(s => (
            <div key={s.label} className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 500 }}>{s.label}</span>
                <span style={{ color: s.color, opacity: 0.8 }}>{s.icon}</span>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: s.color, letterSpacing: '-0.03em' }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* История заказов */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
          <h3 style={{ margin: 0 }}>История заказов</h3>
        </div>
        {orders.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Дата</th>
                <th>Сумма</th>
                <th>Оплачено</th>
                <th>Долг</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(o => {
                const debt = Number(o.price) - Number(o.paid_amount);
                const st = STATUS_MAP[o.status];
                return (
                  <tr key={o.id}>
                    <td>#{o.id}</td>
                    <td style={{ fontWeight: 500 }}>{o.title}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                      {new Date(o.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td>{Number(o.price).toLocaleString()} ₽</td>
                    <td style={{ color: debt > 0 ? '#f59e0b' : 'var(--success)' }}>
                      {Number(o.paid_amount).toLocaleString()} ₽
                    </td>
                    <td style={{ color: debt > 0 ? '#d29922' : 'var(--text-muted)' }}>
                      {debt > 0 ? `${debt.toLocaleString()} ₽` : '—'}
                    </td>
                    <td>
                      <span style={{ color: st.color, fontWeight: 600, fontSize: '0.85rem' }}>{st.label}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>Заказов пока нет</p>
        )}
      </div>
    </div>
  );
};
