import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, ShoppingBag, LogOut, Package } from 'lucide-react';

export const Layout: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 18, fontWeight: 900 }}>D</span>
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
