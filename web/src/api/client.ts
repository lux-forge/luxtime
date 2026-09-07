import type {
  ApiInsights,
  ApiProject,
  ApiSession,
  ApiSettings,
  ApiStatus,
  InsightPeriod,
  WorkTypeName,
} from './types'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let detail = `LuxTime request failed (${response.status})`
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) detail = body.detail
    } catch {
      // Keep the HTTP fallback if the response was not JSON.
    }
    throw new ApiError(detail, response.status)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

const json = (value: unknown): string => JSON.stringify(value)

export const api = {
  status: () => request<ApiStatus>('/status'),
  projects: () => request<ApiProject[]>('/projects'),
  createProject: (payload: { name: string; code?: string; color: string }) =>
    request<ApiProject>('/projects', { method: 'POST', body: json(payload) }),
  updateProject: (id: string, payload: Partial<Pick<ApiProject, 'name' | 'code' | 'color' | 'active'>>) =>
    request<ApiProject>(`/projects/${id}`, { method: 'PATCH', body: json(payload) }),
  sessions: (status?: 'stopped') =>
    request<ApiSession[]>(`/sessions${status ? `?status=${status}` : ''}`),
  active: () => request<ApiSession[]>('/active'),
  start: (payload: { project_id: string; work_type: WorkTypeName; description: string }) =>
    request<ApiSession>('/sessions/start', { method: 'POST', body: json(payload) }),
  pause: (id: string) => request<ApiSession>(`/sessions/${id}/pause`, { method: 'POST', body: '{}' }),
  resume: (id: string) => request<ApiSession>(`/sessions/${id}/resume`, { method: 'POST', body: '{}' }),
  stop: (id: string) => request<ApiSession>(`/sessions/${id}/stop`, { method: 'POST', body: '{}' }),
  pauseAll: () => request<{ sessions: ApiSession[] }>('/active/pause-all', { method: 'POST', body: '{}' }),
  resumeAll: () => request<{ sessions: ApiSession[] }>('/active/resume-all', { method: 'POST', body: '{}' }),
  stopAll: () => request<{ sessions: ApiSession[] }>('/active/stop-all', { method: 'POST', body: '{}' }),
  deleteSession: (id: string) => request<void>(`/sessions/${id}`, { method: 'DELETE' }),
  settings: () => request<ApiSettings>('/settings'),
  updateSettings: (payload: Record<string, string | number | boolean>) =>
    request<ApiSettings>('/settings', { method: 'PATCH', body: json(payload) }),
  insights: (period: InsightPeriod) => request<ApiInsights>(`/insights?period=${period}`),
}
