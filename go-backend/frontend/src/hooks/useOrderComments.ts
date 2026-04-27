import { useState, useEffect, useCallback } from 'react';
import { request } from '../api/client';
import type { OrderComment } from '../types';

export function useOrderComments(orderId: number) {
  const [comments, setComments] = useState<OrderComment[]>([]);

  const fetch = useCallback(async () => {
    const data = await request(`/orders/${orderId}/comments`);
    if (data) setComments(data);
  }, [orderId]);

  useEffect(() => { fetch(); }, [fetch]);

  const add = async (message: string) => {
    if (!message.trim()) return;
    await request(`/orders/${orderId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    fetch();
  };

  return { comments, add };
}
