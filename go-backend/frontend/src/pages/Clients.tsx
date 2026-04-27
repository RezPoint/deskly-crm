import React, { useState } from 'react';
import { UserPlus, Phone, MessageSquare, Trash2, Edit3, Search, StickyNote, ExternalLink, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../hooks/useClients';
import { Modal } from '../components/Modal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import type { Client } from '../types';

const emptyForm = { name: '', phone: '', telegram: '', notes: '' };

export const Clients: React.FC = () => {
  const navigate = useNavigate();
  const { clients, searchQuery, setSearchQuery, loading, error, mutationError, clearMutationError, create, update, remove } = useClients();

  const [showModal, setShowModal] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [editTarget, setEditTarget] = useState<Client | null>(null);
  const [form, setForm] = useState(emptyForm);

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Загрузка...</div>;
  if (error) return <div style={{ padding: '2rem', color: 'var(--danger)' }}>{error}</div>;

  const field = (key: keyof typeof emptyForm) => ({
    value: form[key],
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm(prev => ({ ...prev, [key]: e.target.value })),
  });

  const openCreate = () => { setForm(emptyForm); setEditTarget(null); setShowModal(true); };

  const openEdit = (c: Client) => {
    setForm({ name: c.name, phone: c.phone, telegram: c.telegram, notes: c.notes });
    setEditTarget(c);
    setShowModal(true);
  };

  const closeModal = () => { setShowModal(false); setEditTarget(null); };

  const exportCSV = () => {
    const rows = [['ID', 'Имя', 'Телефон', 'Telegram', 'Заметки', 'Дата добавления']];
    clients.forEach(c => rows.push([String(c.id), c.name, c.phone, c.telegram, c.notes, new Date(c.created_at).toLocaleDateString('ru-RU')]));
    const csv = rows.map(r => r.map(f => `"${f.replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'clients.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editTarget) {
      await update(editTarget.id, form);
    } else {
      await create(form);
    }
    closeModal();
  };

  return (
    <div>
      {mutationError && (
        <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', color: '#ef4444', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{mutationError}</span>
          <button onClick={clearMutationError} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
        </div>
      )}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div><h1>Клиенты</h1><p className="text-muted">База заказчиков</p></div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn" onClick={exportCSV}><Download size={16} /> CSV</button>
          <button className="btn btn-primary" onClick={openCreate}><UserPlus size={18} /> Добавить клиента</button>
        </div>
      </header>

      <div style={{ position: 'relative', marginBottom: '1.5rem' }}>
        <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
        <input
          type="text"
          placeholder="Поиск по имени, телефону, Telegram..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{ paddingLeft: '2.75rem' }}
        />
      </div>

      {clients.length === 0 && (
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>
          {searchQuery ? 'Ничего не найдено' : 'Клиентов пока нет'}
        </p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {clients.map(c => (
          <ClientCard
            key={c.id}
            client={c}
            onView={() => navigate(`/clients/${c.id}`)}
            onEdit={() => openEdit(c)}
            onDelete={() => setDeleteId(c.id)}
          />
        ))}
      </div>

      {showModal && (
        <Modal title={editTarget ? 'Редактировать клиента' : 'Новый клиент'} onClose={closeModal}>
          <form onSubmit={handleSubmit}>
            <div className="input-group"><label>ФИО *</label><input required {...field('name')} /></div>
            <div className="input-group"><label>Телефон</label><input {...field('phone')} /></div>
            <div className="input-group"><label>Telegram</label><input {...field('telegram')} /></div>
            <div className="input-group">
              <label>Заметки</label>
              <textarea rows={3} style={{ resize: 'vertical' }} {...field('notes')} />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
              {editTarget ? 'Сохранить изменения' : 'Создать'}
            </button>
          </form>
        </Modal>
      )}

      {deleteId && (
        <ConfirmDialog
          message="Удалить клиента?"
          onConfirm={() => { remove(deleteId); setDeleteId(null); }}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
};

const ClientCard: React.FC<{ client: Client; onView: () => void; onEdit: () => void; onDelete: () => void }> = ({ client, onView, onEdit, onDelete }) => (
  <div className="glass-panel" style={{ padding: '1.5rem', position: 'relative' }}>
    <div style={{ position: 'absolute', top: '1rem', right: '1rem', display: 'flex', gap: '8px' }}>
      <button onClick={onView} title="Открыть профиль" style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', opacity: 0.7 }}><ExternalLink size={16} /></button>
      <button onClick={onEdit} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', opacity: 0.7 }}><Edit3 size={18} /></button>
      <button onClick={onDelete} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', opacity: 0.7 }}><Trash2 size={18} /></button>
    </div>
    <h3 style={{ marginBottom: '1rem', paddingRight: '3rem' }}>{client.name}</h3>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <Row icon={<Phone size={16} />} text={client.phone || '—'} />
      <Row icon={<MessageSquare size={16} />} text={client.telegram || '—'} />
      {client.notes && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', color: 'var(--text-muted)', fontSize: '0.9rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem' }}>
          <StickyNote size={16} style={{ marginTop: 2, flexShrink: 0 }} />
          <span>{client.notes}</span>
        </div>
      )}
    </div>
  </div>
);

const Row: React.FC<{ icon: React.ReactNode; text: string }> = ({ icon, text }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
    {icon} {text}
  </div>
);
