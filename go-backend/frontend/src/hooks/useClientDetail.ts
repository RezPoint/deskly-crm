import { useState, useEffect } from 'react';
import { request } from '../api/client';
import type { Client } from '../types';

interface ClientOrder {
  id: number;
  title: string;
  price: number;
  paid_amount: number;
  status: 'new' | 'in_work' | 'done' | 'cancelled';
  comment: string;
  created_at: string;
}

export function useClientDetail(id: number) {
  const [client, setClient] = useState<Client | null>(null);
  const [orders, setOrders] = useState<ClientOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [c, o] = await Promise.all([
          request(`/clients/${id}`),
          request(`/clients/${id}/orders`),
        ]);
        setClient(c);
        setOrders(o || []);
      } catch {
        setError('Ошибка загрузки данных клиента');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [id]);

  return { client, orders, loading, error };
}
