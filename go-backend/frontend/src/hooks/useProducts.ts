import { useState, useEffect, useCallback } from 'react';
import { request } from '../api/client';
import type { Product } from '../types';

export function useProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setError(null);
      const data = await request('/products');
      if (data) setProducts(data);
    } catch {
      setError('Ошибка загрузки товаров');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  const create = async (payload: Pick<Product, 'name' | 'description' | 'price'>) => {
    try {
      setMutationError(null);
      await request('/products', { method: 'POST', body: JSON.stringify(payload) });
      fetch();
    } catch {
      setMutationError('Не удалось создать товар');
    }
  };

  const update = async (id: number, payload: Partial<Product>) => {
    try {
      setMutationError(null);
      await request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
      fetch();
    } catch {
      setMutationError('Не удалось обновить товар');
    }
  };

  const toggle = async (id: number) => {
    try {
      setMutationError(null);
      await request(`/products/${id}/toggle`, { method: 'PATCH' });
      fetch();
    } catch {
      setMutationError('Не удалось изменить статус товара');
    }
  };

  const remove = async (id: number) => {
    try {
      setMutationError(null);
      await request(`/products/${id}`, { method: 'DELETE' });
      fetch();
    } catch {
      setMutationError('Не удалось удалить товар');
    }
  };

  const active = products.filter(p => p.is_active);
  const archived = products.filter(p => !p.is_active);

  return {
    products, active, archived,
    loading, error, mutationError,
    clearMutationError: () => setMutationError(null),
    create, update, toggle, remove,
  };
}
