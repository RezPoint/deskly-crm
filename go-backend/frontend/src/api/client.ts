export const API_URL = '/api/v1';

export const request = async (endpoint: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/login';
    throw new Error('Сессия истекла, войдите снова');
  }

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Network response was not ok');
  }

  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return null;
  }

  return response.json();
};
