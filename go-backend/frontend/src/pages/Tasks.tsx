import React, { useState } from 'react';
import { Plus, Trash2, CheckSquare, Clock, Circle, Search, User, Edit3 } from 'lucide-react';
import { useTasks } from '../hooks/useTasks';
import { useClients } from '../hooks/useClients';
import { Modal } from '../components/Modal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import type { Task } from '../types';

const STATUS_OPTIONS: Array<{ value: Task['status']; label: string }> = [
  { value: 'new',         label: 'Новая' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'done',        label: 'Выполнена' },
];

const STATUS_COLOR: Record<Task['status'], string> = {
  new:         'var(--text-muted)',
  in_progress: '#f59e0b',
  done:        '#22c55e',
};

const StatusIcon: React.FC<{ status: Task['status'] }> = ({ status }) => {
  const color = STATUS_COLOR[status];
  if (status === 'done')        return <CheckSquare size={18} color={color} />;
  if (status === 'in_progress') return <Clock size={18} color={color} />;
  return <Circle size={18} color={color} />;
};

const isOverdue = (task: Task) =>
  !!task.due_date && task.status !== 'done' && new Date(task.due_date) < new Date();

export const Tasks: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<Task['status'] | ''>('');
  const [search, setSearch] = useState('');
  const { tasks, create, update, remove, loading, error, mutationError, clearMutationError } = useTasks(filterStatus);
  const { clients } = useClients();

  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState<Task | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState({ title: '', description: '', dueDate: '', clientId: '' });

  const openEdit = (t: Task) => {
    setEditTarget(t);
    setForm({
      title: t.title,
      description: t.description || '',
      dueDate: t.due_date ? t.due_date.substring(0, 10) : '',
      clientId: t.client_id ? String(t.client_id) : '',
    });
    setShowModal(true);
  };

  const closeModal = () => { setShowModal(false); setEditTarget(null); };

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Загрузка...</div>;
  if (error) return <div style={{ padding: '2rem', color: 'var(--danger)' }}>{error}</div>;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editTarget) {
      await update(editTarget.id, {
        title: form.title,
        description: form.description,
        status: editTarget.status,
        due_date: form.dueDate || null,
        client_id: form.clientId ? Number(form.clientId) : undefined,
      });
    } else {
      await create({
        title: form.title,
        description: form.description,
        due_date: form.dueDate || null,
        client_id: form.clientId ? Number(form.clientId) : undefined,
      });
    }
    closeModal();
    setForm({ title: '', description: '', dueDate: '', clientId: '' });
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
        <div><h1>Задачи</h1><p className="text-muted">Список дел</p></div>
        <button className="btn btn-primary" onClick={() => { setEditTarget(null); setForm({ title: '', description: '', dueDate: '', clientId: '' }); setShowModal(true); }}><Plus size={18} /> Новая задача</button>
      </header>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <FilterBtn active={filterStatus === ''} onClick={() => setFilterStatus('')}>Все</FilterBtn>
        {STATUS_OPTIONS.map(o => (
          <FilterBtn key={o.value} active={filterStatus === o.value} onClick={() => setFilterStatus(o.value)}>
            {o.label}
          </FilterBtn>
        ))}
      </div>

      <div style={{ position: 'relative', marginBottom: '1.5rem' }}>
        <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
        <input
          type="text"
          placeholder="Поиск по задаче..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ paddingLeft: '2.5rem' }}
        />
      </div>

      {(() => {
        const filtered = search
          ? tasks.filter(t =>
              t.title.toLowerCase().includes(search.toLowerCase()) ||
              (t.description || '').toLowerCase().includes(search.toLowerCase())
            )
          : tasks;
        return (
          <>
            {filtered.length === 0 && (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>
                {search ? 'Ничего не найдено' : 'Задач нет'}
              </p>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {filtered.map(t => (
                <TaskRow
                  key={t.id}
                  task={t}
                  clientName={t.client_id ? clients.find(c => c.id === t.client_id)?.name : undefined}
                  onStatusChange={status => update(t.id, { title: t.title, description: t.description, status, client_id: t.client_id })}
                  onEdit={() => openEdit(t)}
                  onDelete={() => setDeleteId(t.id)}
                />
              ))}
            </div>
          </>
        );
      })()}

      {showModal && (
        <Modal title={editTarget ? 'Редактировать задачу' : 'Новая задача'} onClose={closeModal}>
          <form onSubmit={handleSubmit}>
            <div className="input-group">
              <label>Название *</label>
              <input required value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} />
            </div>
            <div className="input-group">
              <label>Описание</label>
              <textarea rows={3} style={{ resize: 'vertical' }} value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
            </div>
            <div className="input-group">
              <label>Дедлайн</label>
              <input type="date" value={form.dueDate} onChange={e => setForm(p => ({ ...p, dueDate: e.target.value }))} />
            </div>
            <div className="input-group">
              <label>Клиент</label>
              <select value={form.clientId} onChange={e => setForm(p => ({ ...p, clientId: e.target.value }))}>
                <option value="">— не указан —</option>
                {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>{editTarget ? 'Сохранить' : 'Создать задачу'}</button>
          </form>
        </Modal>
      )}

      {deleteId && (
        <ConfirmDialog
          message="Удалить задачу?"
          onConfirm={() => { remove(deleteId); setDeleteId(null); }}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
};

const TaskRow: React.FC<{
  task: Task;
  clientName?: string;
  onStatusChange: (s: Task['status']) => void;
  onEdit: () => void;
  onDelete: () => void;
}> = ({ task, clientName, onStatusChange, onEdit, onDelete }) => {
  const overdue = isOverdue(task);
  return (
    <div className="glass-panel" style={{
      padding: '1.25rem 1.5rem', display: 'flex', alignItems: 'flex-start', gap: '1rem',
      borderLeft: `3px solid ${overdue ? 'var(--danger)' : 'transparent'}`,
    }}>
      <div style={{ paddingTop: 2 }}><StatusIcon status={task.status} /></div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 500, textDecoration: task.status === 'done' ? 'line-through' : 'none', opacity: task.status === 'done' ? 0.5 : 1 }}>
            {task.title}
          </span>
          {overdue && <span style={{ fontSize: '0.75rem', color: 'var(--danger)', fontWeight: 600 }}>просрочена</span>}
          {clientName && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <User size={12} /> {clientName}
            </span>
          )}
        </div>
        {task.description && <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.25rem 0 0' }}>{task.description}</p>}
        {task.due_date && (
          <p style={{ color: overdue ? 'var(--danger)' : 'var(--text-muted)', fontSize: '0.8rem', margin: '0.25rem 0 0' }}>
            До: {new Date(task.due_date).toLocaleDateString('ru-RU')}
          </p>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
        <select
          value={task.status}
          onChange={e => onStatusChange(e.target.value as Task['status'])}
          style={{ fontSize: '0.8rem', padding: '0.3rem 0.5rem', background: 'rgba(255,255,255,0.08)', border: '1px solid var(--glass-border)', borderRadius: '6px', color: STATUS_COLOR[task.status] }}
        >
          {STATUS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <button onClick={onEdit} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', opacity: 0.6 }}><Edit3 size={16} /></button>
        <button onClick={onDelete} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', opacity: 0.6 }}><Trash2 size={16} /></button>
      </div>
    </div>
  );
};

const FilterBtn: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button onClick={onClick} className="btn" style={{ background: active ? 'var(--primary)' : 'rgba(255,255,255,0.08)', color: active ? 'white' : 'var(--text-muted)', fontSize: '0.85rem', padding: '0.4rem 1rem' }}>
    {children}
  </button>
);
