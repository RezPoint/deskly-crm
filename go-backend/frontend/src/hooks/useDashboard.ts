import { useState, useEffect, useCallback } from 'react';
import { request } from '../api/client';
import type { DashboardStats, ActivityLog, RevenuePoint } from '../types';

const REFRESH_INTERVAL_MS = 30_000;

const defaultStats: DashboardStats = {
  clients: 0, orders: 0, total: 0, revenue: 0,
  debt: 0, active_tasks: 0, recent_orders: [],
};

export function useDashboard() {
  const [stats, setStats] = useState<DashboardStats>(defaultStats);
  const [activity, setActivity] = useState<ActivityLog[]>([]);
  const [revenueChart, setRevenueChart] = useState<RevenuePoint[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const [statsData, logData, revenueData] = await Promise.all([
        request('/dashboard/stats'),
        request('/activity'),
        request('/dashboard/revenue'),
      ]);
      if (statsData) setStats({ ...statsData, recent_orders: statsData.recent_orders ?? [] });
      if (logData) setActivity(logData ?? []);
      if (revenueData) setRevenueChart(revenueData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetch]);

  return { stats, activity, revenueChart, loading };
}
