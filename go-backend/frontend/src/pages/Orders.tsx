import React, { useState } from 'react';
import { Plus, Banknote, Edit3, Trash2, ChevronDown, ChevronRight, CheckCircle, Search, User, Download, MessageSquare, Send } from 'lucide-react';
import { useOrders } from '../hooks/useOrders';
import { useClients } from '../hooks/useClients';
import { useProducts } from '../hooks/useProducts';
import { useOrderComments } from '../hooks/useOrderComments';
import { Modal } from '../components/Modal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import type { Order, Client, Product } from '../types';

export const STATUS_MAP: Record<Order['status'], { label: string; bg: string; color: string }> = {
  new:       { label: 'Новый',    bg: 'rgba(59,130,246,0.2)',  color: '#3b82f6' },
  in_work:   { label: 'В работе', bg: 'rgba(168,85,247,0.2)',  color: '#a855f7' },
  done:      { label: 'Выполнен', bg: 'rgba(16,185,129,0.2)',  color: '#10b981' },
  cancelled: { label: 'Отменён',  bg: 'rgba(239,68,68,0.2)',   color: '#ef4444' },
};

export const Orders: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState('');
  const [qFilter, setQFilter] = useState('');

  const { orders, create, update, updateStatus, remove, pay, loading, error, mutationError, clearMutationError } = useOrders(statusFilter, qFilter);
  const { clients } = useClients();
  const { active: activeProducts } = useProducts();

  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [payOrder, setPayOrder] = useState<Order | null>(null);
  const [doneOrder, setDoneOrder] = useState<Order | null>(null);
  const [editTarget, setEditTarget] = useState<Order | null>(null);
  const [showForm, setShowForm] = useState(false);

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Загрузка...</div>;
  if (error) return <div style={{ padding: '2rem', color: 'var(--danger)' }}>{error}</div>;

  const openCreate = () => { setEditTarget(null); setShowForm(true); };
  const openEdit = (o: Order) => { setEditTarget(o); setShowForm(true); };

  const exportCSV = () => {
    const rows = [['ID', 'Название', 'Клиент', 'Сумма', 'Оплачено', 'Долг', 'Статус']];
    orders.forEach(o => {
      const debt = Math.max(0, Number(o.price) - Number(o.paid_amount));
      rows.push([String(o.id), o.title, o.client_name || '', String(o.price), String(o.paid_amount), String(debt), STATUS_MAP[o.status].label]);
    });
    const csv = rows.map(r => r.map(f => `"${f.replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'orders.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const handlePay = async (amount: number) => {
    if (!payOrder) return;
    await pay(payOrder.id, amount);
    const newPaid = payOrder.paid_amount + amount;
    if (newPaid >= payOrder.price && payOrder.status !== 'done') {
      setDoneOrder(payOrder);
    }
    setPayOrder(null);
  };

  return (
    <div>
      {mutationError && (
        <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', color: '#ef4444', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{mutationError}</span>
          <button onClick={clearMutationError} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
        </div>
      )}
      <header style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div><h1>Заказы</h1><p className="text-muted">Управление и статусы</p></div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn" onClick={exportCSV}><Download size={16} /> CSV</button>
          <button className="btn btn-primary" onClick={openCreate}><Plus size={18} /> Новый заказ</button>
        </div>
      </header>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 200px' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
          <input
            type="text"
            placeholder="Поиск по клиенту..."
            value={qFilter}
            onChange={e => setQFilter(e.target.value)}
            style={{ paddingLeft: '2.5rem' }}
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{ flex: '0 0 auto', padding: '0.55rem 0.875rem' }}
        >
          <option value="">Все статусы</option>
          {Object.entries(STATUS_MAP).map(([v, { label }]) => (
            <option key={v} value={v}>{label}</option>
          ))}
        </select>
      </div>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 32 }} />
              <th>ID</th><th>Название</th><th>Клиент</th>
              <th>Сумма</th><th>Оплачено</th><th>Статус</th><th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {orders.map(o => (
              <OrderRows
                key={o.id}
                order={o}
                expanded={expandedId === o.id}
                onToggle={() => setExpandedId(p => p === o.id ? null : o.id)}
                onEdit={() => openEdit(o)}
                onDelete={() => setDeleteId(o.id)}
                onPay={() => setPayOrder(o)}
                onStatusChange={status => updateStatus(o.id, status)}
              />
            ))}
          </tbody>
        </table>
        {orders.length === 0 && (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>Заказов пока нет</p>
        )}
      </div>

      {showForm && (
        <OrderFormModal
          order={editTarget}
          clients={clients}
          products={activeProducts}
          onSubmit={async payload => {
            if (editTarget) await update(editTarget.id, payload);
            else await create(payload);
            setShowForm(false);
          }}
          onClose={() => setShowForm(false)}
        />
      )}

      {payOrder && (
        <PayModal
          order={payOrder}
          onSubmit={handlePay}
          onClose={() => setPayOrder(null)}
        />
      )}

      {doneOrder && (
        <DoneConfirm
          onConfirm={() => { updateStatus(doneOrder.id, 'done'); setDoneOrder(null); }}
          onCancel={() => setDoneOrder(null)}
        />
      )}

      {deleteId && (
        <ConfirmDialog
          message="Удалить заказ?"
          onConfirm={() => { remove(deleteId); setDeleteId(null); }}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
};

// ── Строки таблицы ──────────────────────────────────────────────────────────

const OrderRows: React.FC<{
  order: Order;
  expanded: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onPay: () => void;
  onStatusChange: (s: Order['status']) => void;
}> = ({ order, expanded, onToggle, onEdit, onDelete, onPay, onStatusChange }) => {
  const st = STATUS_MAP[order.status];
  const debt = order.price - order.paid_amount;

  return (
    <React.Fragment>
      <tr>
        <td>
          <button onClick={onToggle} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 2 }}>
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        </td>
        <td>#{order.id}</td>
        <td style={{ fontWeight: 500 }}>{order.title}</td>
        <td style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{order.client_name || '—'}</td>
        <td>{order.price.toLocaleString()} ₽</td>
        <td>
          <span style={{ color: debt > 0 ? '#f59e0b' : 'var(--success)' }}>
            {order.paid_amount.toLocaleString()} ₽
          </span>
        </td>
        <td>
          <select
            value={order.status}
            onChange={e => onStatusChange(e.target.value as Order['status'])}
            style={{ background: st.bg, color: st.color, border: 'none', padding: '4px 8px', borderRadius: 4, fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}
          >
            {Object.entries(STATUS_MAP).map(([v, { label }]) => (
              <option key={v} value={v} style={{ color: 'black' }}>{label}</option>
            ))}
          </select>
        </td>
        <td style={{ display: 'flex', gap: 6 }}>
          <button className="btn" style={{ padding: '4px 8px', background: 'rgba(16,185,129,0.2)', color: 'var(--success)' }} onClick={onPay} title="Оплата"><Banknote size={14} /></button>
          <button className="btn" style={{ padding: '4px 8px', background: 'rgba(59,130,246,0.2)', color: 'var(--primary)' }} onClick={onEdit} title="Редактировать"><Edit3 size={14} /></button>
          <button className="btn" style={{ padding: '4px 8px', background: 'rgba(239,68,68,0.2)', color: 'var(--danger)' }} onClick={onDelete} title="Удалить"><Trash2 size={14} /></button>
        </td>
      </tr>
      {expanded && <OrderDetail order={order} debt={debt} />}
    </React.Fragment>
  );
};

const OrderDetail: React.FC<{ order: Order; debt: number }> = ({ order, debt }) => {
  const { comments, add } = useOrderComments(order.id);
  const [msg, setMsg] = useState('');

  const submit = async () => {
    if (!msg.trim()) return;
    await add(msg.trim());
    setMsg('');
  };

  return (
    <tr>
      <td colSpan={8} style={{ padding: 0 }}>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem 1.5rem', borderTop: '1px solid var(--border)' }}>
          {order.items?.length > 0 ? (
            <>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Позиции:</p>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ color: 'var(--text-muted)' }}>
                    <th style={{ textAlign: 'left', fontWeight: 500, paddingBottom: 4 }}>Наименование</th>
                    <th style={{ textAlign: 'right', fontWeight: 500, paddingBottom: 4 }}>Кол-во</th>
                    <th style={{ textAlign: 'right', fontWeight: 500, paddingBottom: 4 }}>Цена</th>
                    <th style={{ textAlign: 'right', fontWeight: 500, paddingBottom: 4 }}>Итого</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map(item => (
                    <tr key={item.id}>
                      <td style={{ paddingTop: 4 }}>{item.title}</td>
                      <td style={{ textAlign: 'right', paddingTop: 4 }}>{item.quantity}</td>
                      <td style={{ textAlign: 'right', paddingTop: 4 }}>{item.unit_price.toLocaleString()} ₽</td>
                      <td style={{ textAlign: 'right', paddingTop: 4 }}>{item.total_price.toLocaleString()} ₽</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: 0 }}>Позиций нет</p>
          )}
          {order.comment && <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '0.75rem', marginBottom: 0 }}><b>Примечание:</b> {order.comment}</p>}
          {debt > 0 && <p style={{ color: '#f59e0b', fontSize: '0.88rem', marginTop: '0.5rem', marginBottom: 0 }}>Долг: {debt.toLocaleString()} ₽</p>}

          {/* Комментарии */}
          <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '0.875rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              <MessageSquare size={14} /> Комментарии {comments.length > 0 && `(${comments.length})`}
            </div>
            {comments.map(c => (
              <div key={c.id} style={{ display: 'flex', gap: 8, marginBottom: '0.4rem', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)', flexShrink: 0, fontSize: '0.75rem', paddingTop: 2 }}>
                  {new Date(c.created_at).toLocaleDateString('ru-RU')}
                </span>
                <span style={{ color: 'var(--text-main)' }}>{c.message}</span>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 8, marginTop: '0.5rem' }}>
              <input
                value={msg}
                onChange={e => setMsg(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') submit(); }}
                placeholder="Добавить комментарий..."
                style={{ flex: 1, padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
              />
              <button onClick={submit} className="btn" style={{ padding: '0.4rem 0.75rem', flexShrink: 0 }}>
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      </td>
    </tr>
  );
};

// ── Модалы ──────────────────────────────────────────────────────────────────

const PayModal: React.FC<{ order: Order; onSubmit: (amount: number) => void; onClose: () => void }> = ({ order, onSubmit, onClose }) => {
  const [amount, setAmount] = useState(String(Math.max(0, order.price - order.paid_amount)));
  return (
    <Modal title="Внести оплату" onClose={onClose} width={400}>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1rem', fontSize: '0.9rem' }}>
        {order.title} — остаток: {Math.max(0, order.price - order.paid_amount).toLocaleString()} ₽
      </p>
      <div className="input-group"><label>Сумма (₽)</label><input type="number" min="0" value={amount} onChange={e => setAmount(e.target.value)} /></div>
      <button className="btn btn-primary" style={{ width: '100%', background: 'var(--success)' }} onClick={() => onSubmit(parseFloat(amount) || 0)}>
        Подтвердить
      </button>
    </Modal>
  );
};

const DoneConfirm: React.FC<{ onConfirm: () => void; onCancel: () => void }> = ({ onConfirm, onCancel }) => (
  <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100, backdropFilter: 'blur(8px)' }}>
    <div className="glass-panel" style={{ width: 400, padding: '2.5rem', textAlign: 'center' }}>
      <CheckCircle size={48} color="var(--success)" style={{ margin: '0 auto 1.5rem' }} />
      <h2>Заказ полностью оплачен!</h2>
      <p className="text-muted">Отметить как «Выполнен»?</p>
      <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        <button className="btn btn-primary" style={{ flex: 1, background: 'var(--success)' }} onClick={onConfirm}>Да</button>
        <button className="btn" style={{ flex: 1, background: 'rgba(255,255,255,0.1)' }} onClick={onCancel}>Позже</button>
      </div>
    </div>
  </div>
);

const OrderFormModal: React.FC<{
  order: Order | null;
  clients: Client[];
  products: Product[];
  onSubmit: (payload: any) => void;
  onClose: () => void;
}> = ({ order, clients, products, onSubmit, onClose }) => {
  const [title, setTitle] = useState(order?.title ?? '');
  const [comment, setComment] = useState(order?.comment ?? '');
  const [price, setPrice] = useState(String(order?.price ?? 0));
  const [selectedClient, setSelectedClient] = useState<Client | null>(
    order ? clients.find(c => c.id === order.client_id) ?? null : null
  );
  const [clientSearch, setClientSearch] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([]);

  const filteredClients = clients.filter(c => c.name.toLowerCase().includes(clientSearch.toLowerCase()));

  const toggleProduct = (id: number) => {
    setSelectedProductIds(prev => {
      const next = prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id];
      const total = products.filter(p => next.includes(p.id)).reduce((s, p) => s + p.price, 0);
      setPrice(String(total));
      return next;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClient) { alert('Выберите клиента'); return; }
    const items = products
      .filter(p => selectedProductIds.includes(p.id))
      .map(p => ({ title: p.name, quantity: 1, unit_price: p.price }));
    onSubmit({ title, comment, client_id: selectedClient.id, price: parseFloat(price) || 0, items });
  };

  return (
    <Modal title={order ? 'Редактировать заказ' : 'Новый заказ'} onClose={onClose} width={550}>
      <form onSubmit={handleSubmit}>
        <div className="input-group"><label>Название *</label><input required value={title} onChange={e => setTitle(e.target.value)} /></div>

        {/* Клиент */}
        <div className="input-group" style={{ position: 'relative' }}>
          <label>Клиент *</label>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
            <input
              value={selectedClient ? selectedClient.name : clientSearch}
              onChange={e => { setClientSearch(e.target.value); setSelectedClient(null); setShowDropdown(true); }}
              onFocus={() => setShowDropdown(true)}
              placeholder="Выберите клиента..."
              style={{ paddingLeft: 36 }}
            />
          </div>
          {showDropdown && (
            <div className="glass-panel" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 10, marginTop: 4, maxHeight: 200, overflowY: 'auto', background: 'rgba(15,23,42,0.97)' }}>
              {filteredClients.length > 0
                ? filteredClients.map(c => (
                    <div key={c.id} className="nav-item" style={{ padding: '10px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}
                      onClick={() => { setSelectedClient(c); setShowDropdown(false); }}>
                      <User size={14} /> {c.name}
                    </div>
                  ))
                : <div style={{ padding: 10, color: 'var(--text-muted)' }}>Ничего не найдено</div>
              }
            </div>
          )}
        </div>

        {/* Товары (только при создании) */}
        {!order && products.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem' }}>Товары / услуги:</label>
            <div style={{ border: '1px solid var(--glass-border)', borderRadius: 10, padding: '0.5rem', maxHeight: 150, overflowY: 'auto' }}>
              {products.map(p => (
                <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 10px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={selectedProductIds.includes(p.id)} onChange={() => toggleProduct(p.id)} />
                  <span>{p.name} <span style={{ color: 'var(--text-muted)' }}>({p.price.toLocaleString()} ₽)</span></span>
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="input-group"><label>Стоимость (₽)</label><input type="number" min="0" value={price} onChange={e => setPrice(e.target.value)} /></div>
        <div className="input-group"><label>Комментарий</label><textarea rows={2} style={{ resize: 'vertical' }} value={comment} onChange={e => setComment(e.target.value)} /></div>
        <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
          {order ? 'Сохранить изменения' : 'Создать заказ'}
        </button>
      </form>
    </Modal>
  );
};
