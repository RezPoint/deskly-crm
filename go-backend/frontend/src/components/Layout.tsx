import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, ShoppingBag, LogOut, Package, CheckSquare } from 'lucide-react';
import { request } from '../api/client';

export const Layout: React.FC = () => {
  const navigate = useNavigate();
  const [overdueCount, setOverdueCount] = useState(0);

  useEffect(() => {
    const fetchOverdue = async () => {
      const data = await request('/tasks');
      if (Array.isArray(data)) {
        const now = new Date();
        setOverdueCount(data.filter((t: any) =>
          t.status !== 'done' && t.due_date && new Date(t.due_date) < now
        ).length);
      }
    };
    fetchOverdue();
    const interval = setInterval(fetchOverdue, 60_000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div style={{ width: 30, height: 30, borderRadius: 8, background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 12px rgba(6,182,212,0.35)', flexShrink: 0 }}>
            <span style={{ fontSize: 15, fontWeight: 800, color: '#000', letterSpacing: '-0.5px' }}>D</span>
          </div>
          DesklyCRM
        </div>

        <nav className="nav-menu">
          <NavLink to="/dashboard" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={20} /> Дашборд
          </NavLink>
          <NavLink to="/clients" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
            <Users size={20} /> Клиенты
          </NavLink>
          <NavLink to="/orders" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
            <ShoppingBag size={20} /> Заказы
          </NavLink>
          <NavLink to="/products" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
            <Package size={20} /> Товары
          </NavLink>
          <NavLink to="/tasks" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
            <CheckSquare size={20} /> Задачи
            {overdueCount > 0 && (
              <span style={{ marginLeft: 'auto', background: 'var(--danger)', color: '#fff', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 700, padding: '1px 6px', lineHeight: '1.4' }}>
                {overdueCount}
              </span>
            )}
          </NavLink>
        </nav>

        <div style={{ marginTop: 'auto', borderTop: '1px solid var(--glass-border)', paddingTop: '1.5rem' }}>
          <button className="nav-item" style={{ width: '100%', background: 'transparent', border: 'none', cursor: 'pointer', textAlign: 'left', color: 'var(--danger)' }} onClick={handleLogout}>
            <LogOut size={20} /> Выйти
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="content-area">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
