import { useState, useEffect, useCallback } from 'react';
import { request } from '../api/client';
import type { Order } from '../types';

export function useOrders(statusFilter = '', qFilter = '') {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setError(null);
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (qFilter) params.set('q', qFilter);
      const qs = params.toString();
      const data = await request(qs ? `/orders?${qs}` : '/orders');
      if (data) setOrders(data);
    } catch {
      setError('Ошибка загрузки заказов');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, qFilter]);

  useEffect(() => { fetch(); }, [fetch]);

  const create = async (payload: {
    title: string;
    comment: string;
    client_id: number;
    price: number;
    items: Array<{ title: string; quantity: number; unit_price: number }>;
  }) => {
    try {
      setMutationError(null);
      await request('/orders', { method: 'POST', body: JSON.stringify(payload) });
      fetch();
    } catch {
      setMutationError('Не удалось создать заказ');
    }
  };

  const update = async (id: number, payload: Partial<Order>) => {
    try {
      setMutationError(null);
      await request(`/orders/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
      fetch();
    } catch {
      setMutationError('Не удалось обновить заказ');
    }
  };

  const updateStatus = async (id: number, status: Order['status']) => {
    try {
      setMutationError(null);
      await request(`/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
      fetch();
    } catch {
      setMutationError('Не удалось обновить статус');
    }
  };

  const remove = async (id: number) => {
    try {
      setMutationError(null);
      await request(`/orders/${id}`, { method: 'DELETE' });
      fetch();
    } catch {
      setMutationError('Не удалось удалить заказ');
    }
  };

  const pay = async (orderId: number, amount: number) => {
    try {
      setMutationError(null);
      await request('/payments', { method: 'POST', body: JSON.stringify({ order_id: orderId, amount }) });
      fetch();
    } catch {
      setMutationError('Не удалось внести оплату');
    }
  };

  return {
    orders, fetch,
    loading, error, mutationError,
    clearMutationError: () => setMutationError(null),
    create, update, updateStatus, remove, pay,
  };
}
