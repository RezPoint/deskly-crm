import React, { useEffect, useState } from 'react';
import { request } from '../api/client';
import { UserPlus, Phone, MessageSquare, Trash2, AlertTriangle, Edit3 } from 'lucide-react';

export const Clients: React.FC = () => {
  const [clients, setClients] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [targetId, setTargetId] = useState<number | null>(null);
  const [editMode, setEditMode] = useState(false);

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [telegram, setTelegram] = useState('');

  useEffect(() => { fetchClients(); }, []);

  const fetchClients = async () => {
    const data = await request('/clients');
    if (data) setClients(data);
  };

  const handleEdit = (c: any) => {
    setTargetId(c.id);
    setName(c.name);
    setPhone(c.phone || '');
    setTelegram(c.telegram || '');
    setEditMode(true);
    setShowModal(true);
  };

  const confirmDelete = async () => {
    if (targetId) {
      await request(`/clients/${targetId}`, { method: 'DELETE' });
      setShowDeleteConfirm(false); setTargetId(null); fetchClients();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { name, phone, telegram };
    if (editMode && targetId) {
      await request(`/clients/${targetId}`, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await request('/clients', { method: 'POST', body: JSON.stringify({ ...payload, notes: '' }) });
    }
    closeModal();
    fetchClients();
  };

  const closeModal = () => {
    setShowModal(false);
    setEditMode(false);
    setTargetId(null);
    setName(''); setPhone(''); setTelegram('');
  };

  return (
    <div>
      <header className="header" style={{ padding: '0 0 2rem 0', border: 'none', display: 'flex', justifyContent: 'space-between' }}>
        <div><h1>Клиенты</h1><p className="text-muted">База заказчиков</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><UserPlus size={18} /> Добавить клиента</button>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {clients.map((c: any) => (
          <div key={c.id} className="glass-panel" style={{ padding: '1.5rem', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '1rem', right: '1rem', display: 'flex', gap: '8px' }}>
              <button onClick={() => handleEdit(c)} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', opacity: 0.7 }}><Edit3 size={18}/></button>
              <button onClick={() => { setTargetId(c.id); setShowDeleteConfirm(true); }} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', opacity: 0.7 }}><Trash2 size={18}/></button>
            </div>
            <h3 style={{ marginBottom: '1rem', paddingRight: '3rem' }}>{c.name}</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.95rem' }}><Phone size={16} /> {c.phone || '—'}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.95rem' }}><MessageSquare size={16} /> {c.telegram || '—'}</div>
            </div>
          </div>
        ))}
      </div>

      {showDeleteConfirm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100, backdropFilter: 'blur(8px)' }}>
          <div className="glass-panel" style={{ width: '350px', padding: '2rem', textAlign: 'center' }}>
            <AlertTriangle size={48} color="var(--danger)" style={{ margin: '0 auto 1rem' }} />
            <h2>Удалить клиента?</h2>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
              <button className="btn" style={{ flex: 1, background: 'var(--danger)', color: 'white' }} onClick={confirmDelete}>Удалить</button>
              <button className="btn" style={{ flex: 1, background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowDeleteConfirm(false)}>Отмена</button>
            </div>
          </div>
        </div>
      )}

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, backdropFilter: 'blur(4px)' }}>
          <div className="glass-panel" style={{ width: '400px', padding: '2rem' }}>
            <h2>{editMode ? 'Редактировать клиента' : 'Новый клиент'}</h2>
            <form onSubmit={handleSubmit} style={{ marginTop: '1.5rem' }}>
              <div className="input-group"><label>ФИО</label><input value={name} onChange={e => setName(e.target.value)} required /></div>
              <div className="input-group"><label>Телефон</label><input value={phone} onChange={e => setPhone(e.target.value)} /></div>
              <div className="input-group"><label>Telegram</label><input value={telegram} onChange={e => setTelegram(e.target.value)} /></div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>{editMode ? 'Сохранить изменения' : 'Создать'}</button>
              <button type="button" className="btn" style={{ width: '100%', marginTop: '0.5rem' }} onClick={closeModal}>Отмена</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
