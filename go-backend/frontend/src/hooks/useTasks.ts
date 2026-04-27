import { useState, useEffect, useCallback } from 'react';
import { request } from '../api/client';
import type { Task } from '../types';

export function useTasks(filterStatus = '') {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const qs = filterStatus ? `?status=${filterStatus}` : '';
      const data = await request(`/tasks${qs}`);
      if (data) setTasks(data);
    } catch {
      setError('Ошибка загрузки задач');
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => { fetch(); }, [fetch]);

  const create = async (payload: Pick<Task, 'title' | 'description'> & { due_date?: string | null; client_id?: number }) => {
    try {
      setMutationError(null);
      await request('/tasks', { method: 'POST', body: JSON.stringify(payload) });
      fetch();
    } catch {
      setMutationError('Не удалось создать задачу');
    }
  };

  const update = async (id: number, payload: Partial<Task> & { due_date?: string | null }) => {
    try {
      setMutationError(null);
      await request(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
      fetch();
    } catch {
      setMutationError('Не удалось обновить задачу');
    }
  };

  const remove = async (id: number) => {
    try {
      setMutationError(null);
      await request(`/tasks/${id}`, { method: 'DELETE' });
      fetch();
    } catch {
      setMutationError('Не удалось удалить задачу');
    }
  };

  return {
    tasks,
    loading, error, mutationError,
    clearMutationError: () => setMutationError(null),
    create, update, remove,
  };
}
