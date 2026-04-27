import { useState, useEffect, useCallback } from 'react';
import { request } from '../api/client';
import type { Client } from '../types';

export function useClients() {
  const [clients, setClients] = useState<Client[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const fetch = useCallback(async (q = '') => {
    try {
      setError(null);
      const endpoint = q ? `/clients?q=${encodeURIComponent(q)}` : '/clients';
      const data = await request(endpoint);
      if (data) setClients(data);
    } catch {
      setError('Ошибка загрузки клиентов');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  useEffect(() => {
    const timer = setTimeout(() => fetch(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery, fetch]);

  const create = async (payload: Omit<Client, 'id' | 'created_at'>) => {
    try {
      setMutationError(null);
      await request('/clients', { method: 'POST', body: JSON.stringify(payload) });
      fetch(searchQuery);
    } catch {
      setMutationError('Не удалось создать клиента');
    }
  };

  const update = async (id: number, payload: Partial<Client>) => {
    try {
      setMutationError(null);
      await request(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
      fetch(searchQuery);
    } catch {
      setMutationError('Не удалось обновить клиента');
    }
  };

  const remove = async (id: number) => {
    try {
      setMutationError(null);
      await request(`/clients/${id}`, { method: 'DELETE' });
      fetch(searchQuery);
    } catch {
      setMutationError('Не удалось удалить клиента');
    }
  };

  return {
    clients, searchQuery, setSearchQuery,
    loading, error, mutationError,
    clearMutationError: () => setMutationError(null),
    create, update, remove,
  };
}
