import type { ApiEnvelope, AuthTokens, AuthUser } from '@/types/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export function getApiBaseUrl() {
  return API_BASE_URL
}

export class ApiError extends Error {
  status: number
  details?: unknown

  constructor(message: string, status: number, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

interface RequestOptions extends RequestInit {
  token?: string | null
}

async function request<T>(path: string, method: HttpMethod, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...rest } = options
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    ...rest,
  })

  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null

  if (!response.ok || !payload?.success) {
    throw new ApiError(
      typeof payload?.error === 'string'
        ? payload.error
        : `Request failed with status ${response.status}`,
      response.status,
      payload?.error,
    )
  }

  return payload.data
}

export interface LoginPayload {
  username: string
  password: string
}

function normalizeTokens(payload: unknown): AuthTokens {
  const source = payload as Record<string, unknown>
  return {
    accessToken: String(source.accessToken ?? source.access_token ?? ''),
    refreshToken: String(source.refreshToken ?? source.refresh_token ?? ''),
  }
}

function normalizeUser(payload: unknown): AuthUser {
  const source = payload as Record<string, unknown>
  return {
    id: source.id as number | string,
    username: String(source.username ?? ''),
    role: (source.role as AuthUser['role']) ?? 'viewer',
    isActive: Boolean(source.isActive ?? source.is_active),
    lastLoginAt: (source.lastLoginAt as string | null | undefined) ?? (source.last_login_at as string | null | undefined) ?? null,
  }
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>(path, 'GET', options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, 'POST', {
      body: body === undefined ? undefined : JSON.stringify(body),
      ...options,
    }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, 'PUT', {
      body: body === undefined ? undefined : JSON.stringify(body),
      ...options,
    }),
  auth: {
    login: async (payload: LoginPayload) => {
      const response = await apiClient.post<{ user?: unknown; tokens?: unknown }>('/auth/login', payload)
      return normalizeTokens(response.tokens ?? response)
    },
    me: async (token: string) => normalizeUser(await apiClient.get<unknown>('/auth/me', { token })),
    logout: (refreshToken: string, token?: string | null) =>
      apiClient.post('/auth/logout', { refresh_token: refreshToken }, { token }),
    refresh: async (refreshToken: string) => {
      const response = await apiClient.post<{ tokens?: unknown }>('/auth/refresh', { refresh_token: refreshToken })
      return normalizeTokens(response.tokens ?? response)
    },
  },
}
