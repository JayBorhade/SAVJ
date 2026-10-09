import type { TaskStatus } from '../domain/taskWorkflow';

const API_BASE_URL = (import.meta.env.VITE_SAVJ_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const TOKEN_KEY = 'savj.accessToken';

export type ApiUser = {
  id: number;
  email: string;
  display_name: string;
  locality: string;
  purpose: string;
  skills: string[];
  created_at: string;
};

export type ApiTask = {
  id: number;
  requester_id: number;
  worker_id: number | null;
  title: string;
  description: string;
  category: string;
  location_text: string;
  budget_minor_units: number;
  currency: string;
  status: TaskStatus;
  scheduled_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
};

export type AuthResult = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: ApiUser;
};

type ApiError = { detail?: string | Array<{ msg?: string }> };

export function getAccessToken(): string | null {
  try { return window.localStorage.getItem(TOKEN_KEY); } catch { return null; }
}

export function clearAccessToken(): void {
  try { window.localStorage.removeItem(TOKEN_KEY); } catch { /* storage may be unavailable */ }
}

function saveAccessToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

async function request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (authenticated) {
    const token = getAccessToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new Error('Cannot reach the SAVJ API. Start the backend and check VITE_SAVJ_API_URL.');
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json() as ApiError;
      if (typeof body.detail === 'string') message = body.detail;
      else if (Array.isArray(body.detail)) message = body.detail.map((item) => item.msg || 'Invalid input').join(' ');
    } catch { /* use status fallback */ }
    if (response.status === 401) clearAccessToken();
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function authenticate(path: '/api/v1/auth/register' | '/api/v1/auth/login', payload: Record<string, unknown>): Promise<AuthResult> {
  const result = await request<AuthResult>(path, { method: 'POST', body: JSON.stringify(payload) }, false);
  saveAccessToken(result.access_token);
  return result;
}

export const savjApi = {
  register: (payload: { email: string; password: string; display_name: string; locality: string; purpose: string; skills: string[] }) =>
    authenticate('/api/v1/auth/register', payload),
  login: (email: string, password: string) =>
    authenticate('/api/v1/auth/login', { email, password }),
  me: () => request<ApiUser>('/api/v1/me'),
  listTasks: () => request<ApiTask[]>('/api/v1/tasks?limit=100'),
  createTask: (payload: { title: string; description: string; category: string; location_text: string; budget_rupees: number }) =>
    request<ApiTask>('/api/v1/tasks', { method: 'POST', body: JSON.stringify(payload) }),
  transitionTask: (id: number, action: 'accept' | 'start' | 'submit' | 'approve' | 'cancel') =>
    request<ApiTask>(`/api/v1/tasks/${id}/${action}`, { method: 'POST' }),
  listDrives: () => request<Array<{ id: number; title: string; description: string; location_text: string; starts_at: string; capacity: number | null; status: string; participant_count: number }>>('/api/v1/drives'),
  joinDrive: (id: number) => request<{ status: string }>(`/api/v1/drives/${id}/join`, { method: 'POST' }),
  createDrive: (payload: { title: string; description: string; location_text: string; starts_at: string; capacity: number | null }) =>
    request<ApiDrive>('/api/v1/drives', { method: 'POST', body: JSON.stringify(payload) }),
  listMessages: (taskId: number) => request<ApiMessage[]>(`/api/v1/tasks/${taskId}/messages`),
  sendMessage: (taskId: number, body: string) =>
    request<ApiMessage>(`/api/v1/tasks/${taskId}/messages`, { method: 'POST', body: JSON.stringify({ body }) }),
  myImpact: () => request<{ verified_completed_tasks: number; community_drives_joined: number }>('/api/v1/me/impact'),
};

export type ApiDrive = {
  id: number; organizer_id: number; title: string; description: string; location_text: string;
  starts_at: string; capacity: number | null; status: string; participant_count: number;
};
export type ApiMessage = { id: number; task_id: number; sender_id: number; body: string; created_at: string };
