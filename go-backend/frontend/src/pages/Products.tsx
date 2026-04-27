import React, { useState } from 'react';
import { Package, Plus, Trash2, Edit3, Archive, ArchiveRestore } from 'lucide-react';
import { useProducts } from '../hooks/useProducts';
import { Modal } from '../components/Modal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import type { Product } from '../types';

const emptyForm = { name: '', description: '', price: '' };

export const Products: React.FC = () => {
  const { active, archived, create, update, toggle, remove, loading, error, mutationError, clearMutationError } = useProducts();

  const [tab, setTab] = useState<'active' | 'archived'>('active');
  const [showModal, setShowModal] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [editTarget, setEditTarget] = useState<Product | null>(null);
  const [form, setForm] = useState(emptyForm);

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Загрузка...</div>;
  if (error) return <div style={{ padding: '2rem', color: 'var(--danger)' }}>{error}</div>;

  const field = (key: keyof typeof emptyForm) => ({
    value: form[key],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value })),
  });

  const openCreate = () => { setForm(emptyForm); setEditTarget(null); setShowModal(true); };

  const openEdit = (p: Product) => {
    setForm({ name: p.name, description: p.description, price: String(p.price) });
    setEditTarget(p);
    setShowModal(true);
  };

  const closeModal = () => { setShowModal(false); setEditTarget(null); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { name: form.name, description: form.description, price: parseFloat(form.price) || 0 };
    if (editTarget) {
      await update(editTarget.id, payload);
    } else {
      await create(payload);
    }
    closeModal();
  };

  const list = tab === 'active' ? active : archived;

  return (
    <div>
      {mutationError && (
        <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', color: '#ef4444', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{mutationError}</span>
          <button onClick={clearMutationError} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
        </div>
      )}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div><h1>Товары</h1><p className="text-muted">Каталог услуг и продуктов</p></div>
        <button className="btn btn-primary" onClick={openCreate}><Plus size={18} /> Добавить</button>
      </header>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <TabBtn active={tab === 'active'} onClick={() => setTab('active')}>Активные ({active.length})</TabBtn>
        <TabBtn active={tab === 'archived'} onClick={() => setTab('archived')}>Архив ({archived.length})</TabBtn>
      </div>

      {list.length === 0 && (
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>Пусто</p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {list.map(p => (
          <ProductCard
            key={p.id}
            product={p}
            onEdit={() => openEdit(p)}
            onToggle={() => toggle(p.id)}
            onDelete={() => setDeleteId(p.id)}
          />
        ))}
      </div>

      {showModal && (
        <Modal title={editTarget ? 'Редактировать' : 'Новый товар'} onClose={closeModal}>
          <form onSubmit={handleSubmit}>
            <div className="input-group"><label>Название *</label><input required {...field('name')} /></div>
            <div className="input-group"><label>Описание</label><input {...field('description')} /></div>
            <div className="input-group"><label>Цена (₽)</label><input type="number" min="0" {...field('price')} /></div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
              {editTarget ? 'Сохранить' : 'Создать'}
            </button>
          </form>
        </Modal>
      )}

      {deleteId && (
        <ConfirmDialog
          message="Удалить товар?"
          onConfirm={() => { remove(deleteId); setDeleteId(null); }}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
};

const ProductCard: React.FC<{
  product: Product;
  onEdit: () => void;
  onToggle: () => void;
  onDelete: () => void;
}> = ({ product, onEdit, onToggle, onDelete }) => (
  <div className="glass-panel" style={{ padding: '1.5rem', position: 'relative', opacity: product.is_active ? 1 : 0.6 }}>
    <div style={{ position: 'absolute', top: '1rem', right: '1rem', display: 'flex', gap: '6px' }}>
      <button onClick={onEdit} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', opacity: 0.7 }}><Edit3 size={16} /></button>
      <button onClick={onToggle} title={product.is_active ? 'В архив' : 'Восстановить'} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', opacity: 0.7 }}>
        {product.is_active ? <Archive size={16} /> : <ArchiveRestore size={16} />}
      </button>
      <button onClick={onDelete} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', opacity: 0.7 }}><Trash2 size={16} /></button>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.75rem', paddingRight: '4rem' }}>
      <Package size={20} color="var(--primary)" />
      <h3 style={{ margin: 0 }}>{product.name}</h3>
    </div>
    {product.description && <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>{product.description}</p>}
    <p style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0 }}>{parseFloat(String(product.price)).toLocaleString()} ₽</p>
  </div>
);

const TabBtn: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className="btn"
    style={{ background: active ? 'var(--primary)' : 'rgba(255,255,255,0.08)', color: active ? 'white' : 'var(--text-muted)' }}
  >
    {children}
  </button>
);
