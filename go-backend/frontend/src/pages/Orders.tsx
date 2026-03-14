import React, { useEffect, useState } from 'react';
import { request } from '../api/client';
import { Plus, X, Banknote, CheckCircle, Search, User, Trash2, AlertTriangle, Edit3 } from 'lucide-react';

export const Orders: React.FC = () => {
  const [orders, setOrders] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  
  const [showModal, setShowModal] = useState(false);
  const [showPayModal, setShowPayModal] = useState(false);
  const [showStatusConfirm, setShowStatusConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [payAmount, setPayAmount] = useState('0');
  const [targetDeleteId, setTargetDeleteId] = useState<number | null>(null);
  const [editMode, setEditMode] = useState(false);

  const [title, setTitle] = useState('');
  const [selectedClient, setSelectedClient] = useState<any>(null);
  const [clientSearch, setClientSearch] = useState('');
  const [showClientResults, setShowClientResults] = useState(false);
  const [price, setPrice] = useState('0');
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([]);

  useEffect(() => { fetchOrders(); fetchClients(); fetchProducts(); }, []);

  const fetchOrders = async () => { const data = await request('/orders'); if (data) setOrders(data); };
  const fetchClients = async () => { const data = await request('/clients'); if (data) setClients(data); };
  const fetchProducts = async () => { const data = await request('/products'); if (data) setProducts(data); };

  const handleEdit = (o: any) => {
    setSelectedOrder(o);
    setTitle(o.title);
    setPrice(o.price.toString());
    const client = clients.find(c => c.id === o.client_id);
    setSelectedClient(client || null);
    setEditMode(true);
    setShowModal(true);
  };

  const handleStatusChange = async (orderId: number, newStatus: string) => {
    await request(`/orders/${orderId}/status`, { method: 'PATCH', body: JSON.stringify({ status: newStatus }) });
    fetchOrders();
  };

  const confirmDelete = async () => {
    if (targetDeleteId) { await request(`/orders/${targetDeleteId}`, { method: 'DELETE' }); setShowDeleteConfirm(false); setTargetDeleteId(null); fetchOrders(); }
  };

  const handleProductToggle = (id: number) => {
    setSelectedProductIds(prev => prev.includes(id) ? prev.filter(pId => pId !== id) : [...prev, id]);
  };

  useEffect(() => {
    if (selectedProductIds.length > 0) {
      const total = products.filter(p => selectedProductIds.includes(p.id)).reduce((sum, p) => sum + parseFloat(p.price || '0'), 0);
      setPrice(total.toString());
    }
  }, [selectedProductIds, products]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClient) return alert('Выберите клиента');
    const items = products.filter(p => selectedProductIds.includes(p.id)).map(p => ({ title: p.name, quantity: 1, unit_price: parseFloat(p.price || '0') }));
    const payload = { title, client_id: selectedClient.id, price: parseFloat(price), items };
    
    if (editMode && selectedOrder) {
      await request(`/orders/${selectedOrder.id}`, { method: 'PUT', body: JSON.stringify(payload) });
    } else {
      await request('/orders', { method: 'POST', body: JSON.stringify(payload) });
    }
    closeModal(); fetchOrders();
  };

  const closeModal = () => {
    setShowModal(false); setEditMode(false); setSelectedOrder(null);
    setTitle(''); setSelectedClient(null); setClientSearch(''); setPrice('0'); setSelectedProductIds([]);
  };

  const handlePaySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const amountNum = parseFloat(payAmount || '0');
    await request('/payments', { method: 'POST', body: JSON.stringify({ order_id: selectedOrder.id, amount: amountNum }) });
    setShowPayModal(false);
    if (parseFloat(selectedOrder.paid_amount || '0') + amountNum >= parseFloat(selectedOrder.price || '0') && selectedOrder.status !== 'done') {
      setShowStatusConfirm(true);
    } else { setSelectedOrder(null); fetchOrders(); }
  };

  const filteredClients = clients.filter(c => c.name.toLowerCase().includes(clientSearch.toLowerCase()));

  const getStatusStyle = (status: string) => {
    switch(status) {
      case 'new': return { bg: 'rgba(59,130,246,0.2)', color: '#3b82f6' };
      case 'in_work': return { bg: 'rgba(168,85,247,0.2)', color: '#a855f7' };
      case 'done': return { bg: 'rgba(16,185,129,0.2)', color: '#10b981' };
      case 'cancelled': return { bg: 'rgba(239,68,68,0.2)', color: '#ef4444' };
      default: return { bg: 'rgba(255,255,255,0.1)', color: 'white' };
    }
  };

  return (
    <div>
      <header className="header" style={{ padding: '0 0 2rem 0', border: 'none', display: 'flex', justifyContent: 'space-between' }}>
        <div><h1>Заказы</h1><p className="text-muted">Статусы и правки</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={18} /> Новый заказ</button>
      </header>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table className="data-table">
          <thead><tr><th>ID</th><th>Название</th><th>Сумма</th><th>Оплачено</th><th>Статус</th><th>Действия</th></tr></thead>
          <tbody>
            {orders.map((o: any) => {
              const style = getStatusStyle(o.status);
              return (
                <tr key={o.id}>
                  <td>#{o.id}</td>
                  <td style={{ fontWeight: 500 }}>{o.title}</td>
                  <td>{parseFloat(o.price).toLocaleString()} ₽</td>
                  <td>{parseFloat(o.paid_amount).toLocaleString()} ₽</td>
                  <td>
                    <select value={o.status} onChange={(e) => handleStatusChange(o.id, e.target.value)} style={{ background: style.bg, color: style.color, border: 'none', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}>
                      <option value="new" style={{color: 'black'}}>Новый</option><option value="in_work" style={{color: 'black'}}>В работе</option><option value="done" style={{color: 'black'}}>Выполнен</option><option value="cancelled" style={{color: 'black'}}>Отменен</option>
                    </select>
                  </td>
                  <td style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn btn-primary" style={{ padding: '4px 8px', fontSize: '0.8rem', background: 'var(--success)' }} onClick={() => { setSelectedOrder(o); setPayAmount((o.price - o.paid_amount).toString()); setShowPayModal(true); }}><Banknote size={14} /></button>
                    <button className="btn" style={{ padding: '4px 8px', background: 'rgba(59, 130, 246, 0.2)', color: 'var(--primary)' }} onClick={() => handleEdit(o)}><Edit3 size={14} /></button>
                    <button className="btn" style={{ padding: '4px 8px', background: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)' }} onClick={() => { setTargetDeleteId(o.id); setShowDeleteConfirm(true); }}><Trash2 size={14} /></button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {showPayModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, backdropFilter: 'blur(4px)' }}>
          <div className="glass-panel" style={{ width: '400px', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}><h2>Внести оплату</h2><button onClick={() => setShowPayModal(false)} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}><X size={20}/></button></div>
            <form onSubmit={handlePaySubmit}>
              <div className="input-group"><label>Сумма (₽)</label><input type="number" value={payAmount} onChange={e => setPayAmount(e.target.value)} required /></div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', background: 'var(--success)' }}>Подтвердить</button>
            </form>
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100, backdropFilter: 'blur(8px)' }}>
          <div className="glass-panel" style={{ width: '350px', padding: '2rem', textAlign: 'center' }}><AlertTriangle size={48} color="var(--danger)" style={{ margin: '0 auto 1rem' }} /><h2>Удалить заказ?</h2><div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}><button className="btn" style={{ flex: 1, background: 'var(--danger)', color: 'white' }} onClick={confirmDelete}>Удалить</button><button className="btn" style={{ flex: 1, background: 'rgba(255,255,255,0.1)' }} onClick={() => setShowDeleteConfirm(false)}>Отмена</button></div></div>
        </div>
      )}

      {showStatusConfirm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100, backdropFilter: 'blur(8px)' }}>
          <div className="glass-panel" style={{ width: '400px', padding: '2.5rem', textAlign: 'center' }}><CheckCircle size={48} color="var(--success)" style={{ margin: '0 auto 1.5rem' }} /><h2>Завершить заказ?</h2><div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}><button className="btn btn-primary" style={{ flex: 1, background: 'var(--success)' }} onClick={async () => { await handleStatusChange(selectedOrder.id, 'done'); setShowStatusConfirm(false); setSelectedOrder(null); }}>Да</button><button className="btn" style={{ flex: 1, background: 'rgba(255,255,255,0.1)' }} onClick={() => { setShowStatusConfirm(false); setSelectedOrder(null); fetchOrders(); }}>Позже</button></div></div>
        </div>
      )}

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, backdropFilter: 'blur(4px)' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '550px', padding: '2.5rem', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}><h2>{editMode ? 'Редактировать заказ' : 'Новый заказ'}</h2><button onClick={closeModal} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}><X size={24}/></button></div>
            <form onSubmit={handleSubmit}>
              <div className="input-group"><label>Название</label><input value={title} onChange={e => setTitle(e.target.value)} required /></div>
              <div className="input-group" style={{ position: 'relative' }}>
                <label>Клиент</label>
                <div style={{ position: 'relative' }}>
                  <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                  <input value={selectedClient ? selectedClient.name : clientSearch} onChange={e => { setClientSearch(e.target.value); setSelectedClient(null); setShowClientResults(true); }} onFocus={() => setShowClientResults(true)} placeholder="Выберите клиента..." style={{ paddingLeft: '40px', width: '100%' }} required={!selectedClient} />
                </div>
                {showClientResults && (
                  <div className="glass-panel" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 10, marginTop: '5px', maxHeight: '200px', overflowY: 'auto', background: 'rgba(15, 23, 42, 0.95)' }}>
                    {filteredClients.length > 0 ? filteredClients.map(c => (<div key={c.id} style={{ padding: '10px 15px', cursor: 'pointer', borderRadius: '8px' }} className="nav-item" onClick={() => { setSelectedClient(c); setShowClientResults(false); }}><User size={16} style={{marginRight: 8}}/> {c.name}</div>)) : <div style={{padding: '10px', color: 'var(--text-muted)'}}>Ничего не найдено</div>}
                  </div>
                )}
              </div>
              {!editMode && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Товары:</label>
                  <div style={{ border: '1px solid var(--glass-border)', borderRadius: '10px', padding: '0.5rem', maxHeight: '120px', overflowY: 'auto' }}>
                    {products.map(p => (<label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '6px 10px', cursor: 'pointer' }}><input type="checkbox" checked={selectedProductIds.includes(p.id)} onChange={() => handleProductToggle(p.id)} /><span>{p.name} ({p.price} ₽)</span></label>))}
                  </div>
                </div>
              )}
              <div className="input-group"><label>Итоговая стоимость (₽)</label><input type="number" value={price} onChange={e => setPrice(e.target.value)} /></div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>{editMode ? 'Сохранить' : 'Создать'}</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
