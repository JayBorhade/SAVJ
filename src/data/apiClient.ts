import type { TaskStatus } from '../domain/taskWorkflow';

const API_BASE_URL = (import.meta.env.VITE_SAVJ_API_URL || (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000')).replace(/\/$/, '');
const TOKEN_KEY = 'savj.accessToken';
let volatileAccessToken: string | null = null;

export type ApiUser = {
  id: number;
  email: string;
  display_name: string;
  locality: string;
  purpose: string;
  skills: string[];
  tools: string[];
  created_at: string;
};

export type ApiTask = {
  id: number;
  requester_id: number;
  worker_id: number | null;
  title: string;
  description: string;
  category: string;
  required_skills: string[];
  required_tools: string[];
  location_text: string;
  latitude: number | null;
  longitude: number | null;
  budget_minor_units: number;
  currency: string;
  status: TaskStatus;
  scheduled_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
};

export type AuthResult = {
  access_token: string | null;
  token_type: string;
  expires_in: number;
  user: ApiUser;
  requires_email_verification?: boolean;
};

type ApiError = { detail?: string | Array<{ msg?: string }> };

export function getAccessToken(): string | null {
  if (volatileAccessToken) return volatileAccessToken;
  // Production uses HttpOnly cookies; remove any legacy persistent bearer token.
  if (import.meta.env.PROD) {
    try { window.localStorage.removeItem(TOKEN_KEY); } catch { /* storage may be unavailable */ }
    return null;
  }
  try { return window.localStorage.getItem(TOKEN_KEY); }
  catch { return null; }
}

export function clearAccessToken(): void {
  volatileAccessToken = null;
  try { window.localStorage.removeItem(TOKEN_KEY); } catch { /* storage may be unavailable */ }
}

function saveAccessToken(token: string | null): void {
  volatileAccessToken = token;
  if (import.meta.env.PROD) {
    try { window.localStorage.removeItem(TOKEN_KEY); } catch { /* storage may be unavailable */ }
    return;
  }
  if (token) {
    try { window.localStorage.setItem(TOKEN_KEY, token); } catch { /* fall back to in-memory session */ }
  } else {
    try { window.localStorage.removeItem(TOKEN_KEY); } catch { /* storage may be unavailable */ }
  }
}

async function request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (authenticated) {
    const token = getAccessToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, credentials: "include" });
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
  register: (payload: { email: string; password: string; display_name: string; locality: string; purpose: string; skills: string[]; tools: string[] }) =>
    authenticate('/api/v1/auth/register', payload),
  login: (email: string, password: string) =>
    authenticate('/api/v1/auth/login', { email, password }),
  requestEmailVerification: (email: string) =>
    request<{ message: string }>('/api/v1/auth/verification-request', { method: 'POST', body: JSON.stringify({ email }) }, false),
  verifyEmail: (token: string) =>
    request<{ message: string }>('/api/v1/auth/verify-email', { method: 'POST', body: JSON.stringify({ token }) }, false),
  requestPasswordReset: (email: string) =>
    request<{ message: string }>('/api/v1/auth/password-reset/request', { method: 'POST', body: JSON.stringify({ email }) }, false),
  confirmPasswordReset: (token: string, new_password: string) =>
    request<{ message: string }>('/api/v1/auth/password-reset/confirm', { method: 'POST', body: JSON.stringify({ token, new_password }) }, false),
  logout: async () => {
    await request<void>('/api/v1/auth/logout', { method: 'POST' });
    clearAccessToken();
  },
  me: () => request<ApiUser>('/api/v1/me'),
  listWorkers: (search = '', skill = '') => { const params = new URLSearchParams({ limit: '100' }); if (search.trim()) params.set('search', search.trim()); if (skill.trim()) params.set('skill', skill.trim()); return request<ApiWorker[]>(`/api/v1/workers?${params.toString()}`); },
  updateMe: (payload: { display_name?: string; locality?: string; purpose?: string; skills?: string[]; tools?: string[] }) => request<ApiUser>('/api/v1/me', { method: 'PATCH', body: JSON.stringify(payload) }),
  listTasks: (filters?: { latitude?: number; longitude?: number; radius_km?: number }) => {
    const params = new URLSearchParams({ limit: '100' });
    if (filters?.latitude !== undefined && filters.longitude !== undefined) {
      params.set('latitude', String(filters.latitude));
      params.set('longitude', String(filters.longitude));
      if (filters.radius_km !== undefined) params.set('radius_km', String(filters.radius_km));
    }
    return request<ApiTask[]>(`/api/v1/tasks?${params.toString()}`);
  },
  createTask: (payload: { title: string; description: string; category: string; required_skills: string[]; required_tools: string[]; location_text: string; budget_rupees: number; latitude?: number | null; longitude?: number | null; scheduled_at?: string | null }) =>
    request<ApiTask>('/api/v1/tasks', { method: 'POST', body: JSON.stringify(payload) }),
  transitionTask: (id: number, action: 'accept' | 'start' | 'submit' | 'approve' | 'cancel') =>
    request<ApiTask>(`/api/v1/tasks/${id}/${action}`, { method: 'POST' }),
  listDrives: () => request<Array<{ id: number; organizer_id: number; title: string; description: string; location_text: string; starts_at: string; capacity: number | null; status: string; participant_count: number }>>('/api/v1/drives'),
  joinDrive: (id: number) => request<{ status: string }>(`/api/v1/drives/${id}/join`, { method: 'POST' }),
  createDrive: (payload: { title: string; description: string; location_text: string; starts_at: string; capacity: number | null }) =>
    request<ApiDrive>('/api/v1/drives', { method: 'POST', body: JSON.stringify(payload) }),
  listMessages: (taskId: number) => request<ApiMessage[]>(`/api/v1/tasks/${taskId}/messages`),
  sendMessage: (taskId: number, body: string) =>
    request<ApiMessage>(`/api/v1/tasks/${taskId}/messages`, { method: 'POST', body: JSON.stringify({ body }) }),
  myImpact: () => request<{ verified_completed_tasks: number; community_drives_joined: number }>('/api/v1/me/impact'),
  uploadProof: (taskId: number, kind: 'before' | 'after', file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<ApiTaskProof>(`/api/v1/tasks/${taskId}/proofs/${kind}`, { method: 'POST', body: form });
  },
  listProofs: (taskId: number) => request<ApiTaskProof[]>(`/api/v1/tasks/${taskId}/proofs`),
  downloadProof: async (proofId: number): Promise<Blob> => {
    const headers = new Headers();
    const token = getAccessToken();
    if (token) headers.set('Authorization', 'Bearer ' + token);
    let response: Response;
    try { response = await fetch(API_BASE_URL + '/api/v1/proofs/' + proofId + '/content', { headers, credentials: 'include' }); }
    catch { throw new Error('Cannot reach the SAVJ API.'); }
    if (!response.ok) {
      if (response.status === 401) clearAccessToken();
      let message = 'Could not load proof image (' + response.status + ').';
      try { const body = await response.json() as ApiError; if (typeof body.detail === 'string') message = body.detail; } catch { /* status fallback */ }
      throw new Error(message);
    }
    return response.blob();
  },
};

export type ApiDrive = {
  id: number; organizer_id: number; title: string; description: string; location_text: string;
  starts_at: string; capacity: number | null; status: string; participant_count: number;
};
export type ApiMessage = { id: number; task_id: number; sender_id: number; body: string; created_at: string };
export type ApiTaskProof = { id: number; task_id: number; uploader_id: number; proof_kind: 'before' | 'after'; original_name: string; content_type: string; size_bytes: number; created_at: string };

export type ApiWorker = { id: number; display_name: string; locality: string; purpose: string; skills: string[]; tools: string[]; created_at: string };
