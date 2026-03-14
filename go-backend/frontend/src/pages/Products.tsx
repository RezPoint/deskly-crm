import React, { useEffect, useState } from 'react';
import { request } from '../api/client';
import { Plus, Trash2, AlertTriangle, ToggleLeft, ToggleRight, PackageCheck, Archive, Edit3 } from 'lucide-react';

export const Products: React.FC = () => {
  const [products, setProducts] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'active' | 'archive'>('active');
  
  const [showModal, setShowModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [targetId, setTargetId] = useState<number | null>(null);
  const [editMode, setEditMode] = useState(false);

  const [name, setName] = useState('');
  const [price, setPrice] = useState('0');

  useEffect(() => { fetchProducts(); }, []);

  const fetchProducts = async () => {
    const data = await request('/products');
    if (data) setProducts(data);
  };

  const handleEdit = (p: any) => {
    setTargetId(p.id);
    setName(p.name);
    setPrice(p.price.toString());
    setEditMode(true);
    setShowModal(true);
  };

  const handleToggle = async (id: number) => {
    await request(`/products/${id}/toggle`, { method: 'PATCH' });
    fetchProducts();
  };

  const confirmDelete = async () => {
    if (targetId) {
      await request(`/products/${targetId}`, { method: 'DELETE' });
      setShowDeleteConfirm(false); setTargetId(null); fetchProducts();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { name, description: '', price: parseFloat(price) };
    if (editMode && targetId) {
      await request(`/products/${targetId}`, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await request('/products', { method: 'POST', body: JSON.stringify(payload) });
    }
    closeModal();
    fetchProducts();
  };

  const closeModal = () => {
    setShowModal(false);
    setEditMode(false);
    setTargetId(null);
    setName(''); setPrice('0');
  };

  const filteredProducts = products.filter(p => activeTab === 'active' ? p.is_active : !p.is_active);

  return (
    <div>
      <header className="header" style={{ padding: '0 0 2rem 0', border: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div><h1>Товары</h1><p className="text-muted">Каталог цен</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={18} /> Добавить</button>
      </header>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <button onClick={() => setActiveTab('active')} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0.75rem 1.25rem', borderRadius: '12px', border: 'none', cursor: 'pointer', background: activeTab === 'active' ? 'var(--primary)' : 'rgba(255,255,255,0.05)', color: activeTab === 'active' ? 'white' : 'var(--text-muted)' }}><PackageCheck size={18} /> Активные</button>
        <button onClick={() => setActiveTab('archive')} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0.75rem 1.25rem', borderRadius: '12px', border: 'none', cursor: 'pointer', background: activeTab === 'archive' ? 'var(--glass-border)' : 'rgba(255,255,255,0.05)', color: activeTab === 'archive' ? 'white' : 'var(--text-muted)' }}><Archive size={18} /> Архив</button>
      </div>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table className="data-table">
          <thead><tr><th>Наименование</th><th>Цена</th><th>Статус</th><th>Действия</th></tr></thead>
          <tbody>
            {filteredProducts.map((p: any) => (
              <tr key={p.id}>
                <td style={{ fontWeight: 600 }}>{p.name}</td>
                <td>{parseFloat(p.price).toLocaleString()} ₽</td>
                <td><button onClick={() => handleToggle(p.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', color: p.is_active ? 'var(--success)' : 'var(--text-muted)', fontWeight: 500, fontSize: '0.85rem' }}>{p.is_active ? <ToggleRight size={28} /> : <ToggleLeft size={28} />} {p.is_active ? 'В каталоге' : 'В архиве'}</button></td>
                <td style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn" style={{ padding: '4px 8px', background: 'rgba(59, 130, 246, 0.2)', color: 'var(--primary)' }} onClick={() => handleEdit(p)}><Edit3 size={14} /></button>
                  <button className="btn" style={{ padding: '4px 8px', background: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)' }} onClick={() => { setTargetId(p.id); setShowDeleteConfirm(true); }}><Trash2 size={14} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showDeleteConfirm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100, backdropFilter: 'blur(8px)' }}>
          <div className="glass-panel" style={{ width: '350px', padding: '2rem', textAlign: 'center' }}><AlertTriangle size={48} color="var(--danger)" style={{ margin: '0 auto 1rem' }} /><h2>Удалить товар?</h2><div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}><button className="btn" style={{ flex: 1, background: 'var(--danger)', color: 'white' }} onClick={confirmDelete}>Удалить</button><button className="btn" style={{ flex: 1, background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowDeleteConfirm(false)}>Отмена</button></div></div>
        </div>
      )}

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, backdropFilter: 'blur(4px)' }}>
          <div className="glass-panel" style={{ width: '400px', padding: '2rem' }}>
            <h2>{editMode ? 'Редактировать товар' : 'Новый товар'}</h2>
            <form onSubmit={handleSubmit} style={{ marginTop: '1.5rem' }}>
              <div className="input-group"><label>Наименование</label><input value={name} onChange={e => setName(e.target.value)} required /></div>
              <div className="input-group"><label>Цена (₽)</label><input type="number" value={price} onChange={e => setPrice(e.target.value)} /></div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>{editMode ? 'Сохранить' : 'Создать'}</button>
              <button type="button" className="btn" style={{ width: '100%', marginTop: '0.5rem' }} onClick={closeModal}>Отмена</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
