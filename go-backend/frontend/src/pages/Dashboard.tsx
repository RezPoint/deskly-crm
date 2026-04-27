import React from 'react';
import { Users, ShoppingBag, Wallet, DollarSign, AlertCircle, CheckSquare, Activity } from 'lucide-react';
import { useDashboard } from '../hooks/useDashboard';
import { STATUS_MAP } from './Orders';
import type { DashboardStats, ActivityLog, RevenuePoint } from '../types';

export const Dashboard: React.FC = () => {
  const { stats, activity, revenueChart, loading } = useDashboard();

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Загрузка...</div>;

  return (
    <div>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}>
        <div><h1>Дашборд</h1><p className="text-muted">Финансовые показатели и активность</p></div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>обновляется каждые 30 сек</span>
      </header>

      <StatsGrid stats={stats} />

      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Выручка за 30 дней</h3>
        <RevenueChart data={revenueChart} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <RecentOrders orders={stats.recent_orders} />
        <ActivityFeed logs={activity} />
      </div>
    </div>
  );
};

// ── Сетка метрик ────────────────────────────────────────────────────────────

const StatsGrid: React.FC<{ stats: DashboardStats }> = ({ stats }) => {
  const cards = [
    { label: 'Клиенты',           value: stats.clients,                              icon: <Users size={18} />,       iconColor: '#06b6d4' },
    { label: 'Активные заказы',    value: stats.orders,                               icon: <ShoppingBag size={18} />, iconColor: '#a78bfa' },
    { label: 'Оборот',             value: `${stats.total.toLocaleString()} ₽`,        icon: <Wallet size={18} />,      iconColor: '#8b949e' },
    { label: 'Выручка',            value: `${stats.revenue.toLocaleString()} ₽`,      icon: <DollarSign size={18} />,  iconColor: '#3fb950', highlight: true },
    { label: 'Долг клиентов',      value: `${Math.max(0, stats.debt).toLocaleString()} ₽`, icon: <AlertCircle size={18} />, iconColor: '#d29922', warn: stats.debt > 0 },
    { label: 'Активных задач',     value: stats.active_tasks,                         icon: <CheckSquare size={18} />, iconColor: '#818cf8' },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
      {cards.map(({ label, value, icon, iconColor, highlight, warn }) => (
        <StatCard key={label} label={label} value={value} icon={icon} iconColor={iconColor} highlight={highlight} warn={warn} />
      ))}
    </div>
  );
};

const StatCard: React.FC<{
  label: string;
  value: string | number;
  icon: React.ReactNode;
  iconColor: string;
  highlight?: boolean;
  warn?: boolean;
}> = ({ label, value, icon, iconColor, highlight, warn }) => (
  <div className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.875rem' }}>
      <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.07em' }}>{label}</span>
      <span style={{ color: iconColor, opacity: 0.8 }}>{icon}</span>
    </div>
    <div style={{ fontSize: '1.75rem', fontWeight: 700, color: highlight ? '#3fb950' : warn ? '#d29922' : 'var(--text-main)', letterSpacing: '-0.03em', lineHeight: 1 }}>{value}</div>
  </div>
);

// ── Последние заказы ─────────────────────────────────────────────────────────

const RecentOrders: React.FC<{ orders: DashboardStats['recent_orders'] }> = ({ orders }) => (
  <div className="glass-panel" style={{ padding: '1.5rem' }}>
    <h3 style={{ marginBottom: '1rem', marginTop: 0 }}>Последние заказы</h3>
    {orders.length > 0 ? (
      <table className="data-table">
        <thead><tr><th>ID</th><th>Название</th><th>Клиент</th><th>Статус</th></tr></thead>
        <tbody>
          {orders.map(o => {
            const st = STATUS_MAP[o.status];
            return (
              <tr key={o.id}>
                <td>#{o.id}</td>
                <td style={{ fontWeight: 500 }}>{o.title}</td>
                <td style={{ color: 'var(--text-muted)' }}>{o.client_name || '—'}</td>
                <td><span style={{ color: st.color, fontWeight: 600, fontSize: '0.85rem' }}>{st.label}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    ) : (
      <p style={{ color: 'var(--text-muted)', margin: 0 }}>Заказов пока нет</p>
    )}
  </div>
);

// ── Лог активности ───────────────────────────────────────────────────────────

const ACTION_STYLE: Record<string, { label: string; bg: string; color: string }> = {
  create:  { label: 'создан',  bg: 'rgba(59,130,246,0.2)',  color: '#3b82f6' },
  delete:  { label: 'удалён',  bg: 'rgba(239,68,68,0.2)',   color: '#ef4444' },
  payment: { label: 'оплата',  bg: 'rgba(16,185,129,0.2)',  color: '#10b981' },
};

// ── График выручки ───────────────────────────────────────────────────────────

const RevenueChart: React.FC<{ data: RevenuePoint[] }> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div style={{ height: 130, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: 0 }}>Оплат пока не было</p>
      </div>
    );
  }

  const W = 600, H = 130;
  const padL = 64, padR = 16, padT = 12, padB = 28;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  const maxAmt = Math.max(...data.map(d => d.amount)) || 1;

  const pts = data.map((d, i) => ({
    x: padL + (data.length === 1 ? plotW / 2 : (i / (data.length - 1)) * plotW),
    y: padT + plotH - (d.amount / maxAmt) * plotH,
    d,
  }));

  const linePath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const areaPath = `${linePath} L${pts[pts.length - 1].x.toFixed(1)},${(padT + plotH).toFixed(1)} L${pts[0].x.toFixed(1)},${(padT + plotH).toFixed(1)} Z`;

  const yTicks = [0, 0.5, 1].map(f => ({
    y: padT + plotH - f * plotH,
    label: `${Math.round(maxAmt * f).toLocaleString()} ₽`,
  }));

  const xIndices = data.length <= 3
    ? data.map((_, i) => i)
    : [0, Math.floor((data.length - 1) / 2), data.length - 1];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      <defs>
        <linearGradient id="rev-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.02" />
        </linearGradient>
      </defs>

      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={t.y} x2={W - padR} y2={t.y} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
          <text x={padL - 6} y={t.y + 4} textAnchor="end" fontSize="10" fill="rgba(139,148,158,0.75)">{t.label}</text>
        </g>
      ))}

      {pts.length > 1 && <path d={areaPath} fill="url(#rev-grad)" />}
      {pts.length > 1 && <path d={linePath} fill="none" stroke="#06b6d4" strokeWidth="2" strokeLinejoin="round" />}
      {pts.map((p, i) => <circle key={i} cx={p.x} cy={p.y} r="3.5" fill="#06b6d4" />)}

      {xIndices.map(i => (
        <text key={i} x={pts[i].x} y={H - 4} textAnchor="middle" fontSize="10" fill="rgba(139,148,158,0.75)">
          {new Date(data[i].date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
        </text>
      ))}
    </svg>
  );
};

// ── Лог активности ───────────────────────────────────────────────────────────

const ActivityFeed: React.FC<{ logs: ActivityLog[] }> = ({ logs }) => (
  <div className="glass-panel" style={{ padding: '1.5rem' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '1rem' }}>
      <Activity size={20} color="var(--primary)" />
      <h3 style={{ margin: 0 }}>Активность</h3>
    </div>
    {logs.length > 0 ? (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {logs.map(log => {
          const style = ACTION_STYLE[log.action] ?? ACTION_STYLE.create;
          return (
            <div key={log.id} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', fontSize: '0.85rem' }}>
              <span style={{ flexShrink: 0, padding: '2px 6px', borderRadius: 4, fontSize: '0.75rem', fontWeight: 600, background: style.bg, color: style.color }}>
                {style.label}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>{log.message}</span>
            </div>
          );
        })}
      </div>
    ) : (
      <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.9rem' }}>Действий пока нет</p>
    )}
  </div>
);
