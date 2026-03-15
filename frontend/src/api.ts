const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const API_BASE = `${BACKEND_URL}/api`;

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function getAuthToken() {
  return authToken;
}

async function request(endpoint: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  // Auth
  register: (data: any) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data: any) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),

  // Clinic
  getClinic: () => request('/clinic'),
  updateClinic: (data: any) => request('/clinic', { method: 'PUT', body: JSON.stringify(data) }),

  // Clinic Hours
  getClinicHours: () => request('/clinic/hours'),
  updateClinicHours: (data: any) => request('/clinic/hours', { method: 'PUT', body: JSON.stringify(data) }),

  // AI Agent
  getAIConfig: () => request('/ai-agent/config'),
  updateAIConfig: (data: any) => request('/ai-agent/config', { method: 'PUT', body: JSON.stringify(data) }),
  toggleAIAgent: () => request('/ai-agent/toggle', { method: 'PUT' }),

  // Appointments
  getAppointments: (params?: string) => request(`/appointments${params ? `?${params}` : ''}`),
  createAppointment: (data: any) => request('/appointments', { method: 'POST', body: JSON.stringify(data) }),
  getAppointment: (id: string) => request(`/appointments/${id}`),
  updateAppointment: (id: string, data: any) => request(`/appointments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAppointment: (id: string) => request(`/appointments/${id}`, { method: 'DELETE' }),

  // Patients
  getPatients: () => request('/patients'),
  createPatient: (data: any) => request('/patients', { method: 'POST', body: JSON.stringify(data) }),
  getPatient: (id: string) => request(`/patients/${id}`),

  // Dashboard
  getDashboardStats: () => request('/dashboard/stats'),

  // AI Chat & Simulation
  aiChat: (data: any) => request('/ai-agent/chat', { method: 'POST', body: JSON.stringify(data) }),
  simulateCall: (data: any) => request('/ai-agent/simulate-call', { method: 'POST', body: JSON.stringify(data) }),
  triggerMorningCalls: () => request('/twilio/voice/morning-calls', { method: 'POST' }),

  // Calendar (in-app)
  getCalendarAppointments: (month?: number, year?: number) => {
    const params = [];
    if (month) params.push(`month=${month}`);
    if (year) params.push(`year=${year}`);
    return request(`/calendar/appointments${params.length ? `?${params.join('&')}` : ''}`);
  },

  // Seed
  seed: () => request('/seed', { method: 'POST' }),
};
