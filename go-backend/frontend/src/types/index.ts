export interface Client {
  id: number;
  name: string;
  phone: string;
  telegram: string;
  notes: string;
  created_at: string;
}

export interface OrderItem {
  id: number;
  order_id: number;
  title: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Order {
  id: number;
  title: string;
  client_id: number;
  client_name: string;
  price: number;
  paid_amount: number;
  status: 'new' | 'in_work' | 'done' | 'cancelled';
  comment: string;
  items: OrderItem[];
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  is_active: boolean;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  status: 'new' | 'in_progress' | 'done';
  order_id?: number;
  client_id?: number;
  due_date?: string | null;
}

export interface OrderComment {
  id: number;
  order_id: number;
  message: string;
  created_at: string;
}

export interface RevenuePoint {
  date: string;
  amount: number;
}

export interface ActivityLog {
  id: number;
  action: string;
  entity_type: string;
  entity_id: number;
  message: string;
  created_at: string;
}

export interface DashboardStats {
  clients: number;
  orders: number;
  total: number;
  revenue: number;
  debt: number;
  active_tasks: number;
  recent_orders: Array<{
    id: number;
    title: string;
    status: Order['status'];
    client_name: string;
  }>;
}
