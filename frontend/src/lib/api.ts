import type { DashboardSummary, PaginatedScans, ScanDetail, User } from './types';

const API = '/api/v1';
export const getToken = () => sessionStorage.getItem('rice_age_token');
export const setToken = (token: string | null) => token ? sessionStorage.setItem('rice_age_token', token) : sessionStorage.removeItem('rice_age_token');

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API}${path}`, { ...init, headers });
  if (response.status === 401) {
    setToken(null);
    window.dispatchEvent(new Event('rice-age:unauthorized'));
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const data = await response.json(); message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail ?? data); } catch { /* keep fallback */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) => request<{access_token: string; token_type: string; expires_in: number}>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<User>('/auth/me'),
  summary: (departmentId?: number) => request<DashboardSummary>(`/dashboard/summary${departmentId ? `?department_id=${departmentId}` : ''}`),
  latest: (departmentId?: number) => request<{item: ScanDetail | null; message?: string}>(`/scans/latest${departmentId ? `?department_id=${departmentId}` : ''}`),
  scans: (params: URLSearchParams) => request<PaginatedScans>(`/scans?${params.toString()}`),
  scan: (id: number) => request<ScanDetail>(`/scans/${id}`),
  departments: () => request<Array<{id:number;code:string;name:string;location:string|null;is_active:boolean}>>('/admin/departments'),
  asset: async (path: string) => {
    const token = getToken();
    const response = await fetch(path, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (response.status === 401) { setToken(null); window.dispatchEvent(new Event('rice-age:unauthorized')); }
    if (!response.ok) throw new Error(`Unable to load attachment (${response.status})`);
    return URL.createObjectURL(await response.blob());
  },
};
